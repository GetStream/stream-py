import os


import asyncio
from typing import (
    Dict,
    Union,
    AsyncGenerator,
    AsyncIterator,
    List,
    Optional,
    Callable,
    Awaitable,
)
import logging

import cffi

from getstream.video.call import Call
from getstream.video.rtc.pb import events
from enum import Enum


ffi = cffi.FFI()
ffi.cdef("""
    typedef void (*CallbackFunc)(const char*, size_t);
    void Join(const char* apiKey, const char* token, const char* callType, const char* callId, const char* mockConfig, size_t mockConfigLen, CallbackFunc callback);
    void Leave(const char* callType, const char* callId);
    void SendAudio(char* cData, size_t data);
    void free(void *ptr);
""")

# Use absolute path to the shared library
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libstreamvideo.so")
lib = ffi.dlopen(lib_path)


class AudioFormat(Enum):
    Float32 = events.AudioFormat.Float32
    Int32 = events.AudioFormat.Int32
    Int16 = events.AudioFormat.Int16


class AudioChannels(Enum):
    Mono = 1
    Stereo = 2


class JoinError(Exception):
    """Exception raised when joining a call fails."""

    def __init__(self, code: events.ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Call join failed: {message} (code: {code})")


class MockAudioConfig:
    """Configuration for mocked audio in a call."""

    def __init__(self, audio_file_path: str, realtime_clock: bool = True):
        """
        Initialize audio configuration for a mocked participant.

        Args:
            audio_file_path: Path to the audio file to use for audio.
                            The file type is determined from the file extension.
            realtime_clock: If True, send audio events at realistic 20ms intervals.
                           If False, send events as fast as possible.
        """
        self.audio_file_path = audio_file_path
        self.realtime_clock = realtime_clock

    def to_proto(self) -> events.MockAudioConfig:
        """Convert to protobuf message."""
        return events.MockAudioConfig(
            audio_file_path=self.audio_file_path, realtime_clock=self.realtime_clock
        )


class MockParticipant:
    """Configuration for a mocked participant in a call."""

    def __init__(
        self, user_id: str, name: str = "", audio: Optional[MockAudioConfig] = None
    ):
        """
        Initialize a mocked participant configuration.

        Args:
            user_id: User ID of the mocked participant.
            name: Name of the mocked participant.
            audio: Audio configuration for this participant.
        """
        self.user_id = user_id
        self.name = name
        self.audio = audio

    def to_proto(self) -> events.MockParticipant:
        """Convert to protobuf message."""
        return events.MockParticipant(
            user_id=self.user_id,
            name=self.name,
            audio=self.audio.to_proto() if self.audio else None,
        )


class MockConfig:
    """Configuration for a mocked call."""

    def __init__(self, participants: List[MockParticipant] = None):
        """
        Initialize a mock configuration.

        Args:
            participants: List of mocked participants.
        """
        self.participants = participants or []

    def to_proto(self) -> events.MockConfig:
        """Convert to protobuf message."""
        return events.MockConfig(participants=[p.to_proto() for p in self.participants])

    def add_participant(self, participant: MockParticipant):
        """Add a participant to the mock configuration."""
        self.participants.append(participant)


class ConnectionManager:
    """
    Manages the connection to a call. Serves as both an async context manager and
    an async iterator over events received from the call.
    """

    def __init__(self, call: "RTCCall", user_id: str, timeout: float = 30.0):
        """
        Initialize a connection manager for a call.

        Args:
            call: The RTCCall instance to manage
            user_id: ID of the user joining the call
            timeout: Maximum time to wait for join to complete
        """
        self.call = call
        self.user_id = user_id
        self.timeout = timeout
        self.joined = False
        self._incoming_audio_iterator = None
        self._event_handlers = {}  # Dictionary to store event handlers
        self._exit_event = asyncio.Event()  # Event to signal when to exit
        self._iteration_task = None  # Task for background event processing

    async def __aenter__(self) -> "ConnectionManager":
        """Enter the async context manager, joining the call."""
        # Create a future to track join status
        self.call._join_future = asyncio.Future()

        # Get API key and secret from the client
        api_key = self.call.client.stream.api_key

        # Create the callback
        cb = make_rtc_event_callback(self.call)
        self.call._cb = cb  # Keep a reference to prevent garbage collection

        token = self.call.client.stream.create_token(self.user_id)

        # Convert to C strings
        c_api_key = ffi.new("char[]", api_key.encode("utf-8"))
        c_token = ffi.new("char[]", token.encode("utf-8"))
        c_call_type = ffi.new("char[]", self.call.call_type.encode("utf-8"))
        c_call_id = ffi.new("char[]", self.call.id.encode("utf-8"))

        # Prepare mock config if available
        c_mock_config = ffi.NULL
        mock_config_len = 0
        mock_bytes = None
        if self.call._mock_config:
            proto_mock = self.call._mock_config.to_proto()
            mock_bytes = proto_mock.SerializeToString()
            c_mock_config = ffi.new("char[]", mock_bytes)
            mock_config_len = len(mock_bytes)

        # Mark that we're using the current event loop
        self.call.ev_loop = asyncio.get_event_loop()

        # Call the Go function with API credentials and call info (non-blocking)
        lib.Join(
            c_api_key,
            c_token,
            c_call_type,
            c_call_id,
            c_mock_config,
            mock_config_len,
            cb,
        )

        try:
            # Wait for join response or error with timeout
            await asyncio.wait_for(self.call._join_future, timeout=self.timeout)
            self.call._joined = True
            self.joined = True

            # Start background task for event processing
            self._iteration_task = asyncio.create_task(self._process_events_task())
        except asyncio.TimeoutError:
            # Timed out waiting for join response
            raise asyncio.TimeoutError(
                f"Timed out waiting to join call after {self.timeout} seconds"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager, leaving the call."""
        if self._iteration_task:
            self._exit_event.set()
            try:
                await asyncio.wait_for(self._iteration_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._iteration_task.cancel()
            finally:
                self._iteration_task = None

        if self.joined:
            await self.call.leave()
            self.call._joined = False
            self.joined = False

    def __aiter__(self) -> AsyncIterator[events.Event]:
        """Return the async iterator over events."""
        return self

    async def __anext__(self) -> events.Event:
        """Get the next event from the event queue."""
        if not self.joined:
            raise StopAsyncIteration

        try:
            # Wait for an event or exit signal
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(self.call._event_queue.get()),
                    asyncio.create_task(self._exit_event.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # If exit event is set, stop iteration
            if self._exit_event.is_set():
                raise StopAsyncIteration

            # Get the completed task result
            for task in done:
                result = task.result()
                if isinstance(result, events.Event):
                    event = result
                    self.call._event_queue.task_done()

                    # Process event through registered handlers
                    await self._dispatch_event(event)

                    return event
                else:
                    # Exit event was set
                    raise StopAsyncIteration
        except asyncio.CancelledError:
            raise StopAsyncIteration

    async def _process_events_task(self):
        """
        Background task that processes events and monitors participant status.
        Automatically exits the call when a call_ended event is received from Go.
        """
        try:
            while not self._exit_event.is_set() and self.joined:
                try:
                    # Wait for an event with a timeout to periodically check conditions
                    event = await asyncio.wait_for(
                        self.call._event_queue.get(), timeout=1.0
                    )

                    # Process the event through registered handlers
                    await self._dispatch_event(event)

                    # Put the event back in the queue for the iterator
                    self.call._event_queue.put_nowait(event)
                    self.call._event_queue.task_done()

                    if event.call_ended is not None:
                        # Call ended event received, signal to exit
                        logging.debug("Call ended event received, signaling exit")
                        self._exit_event.set()
                        break

                except asyncio.TimeoutError:
                    # Regular timeout, just continue
                    continue

                except Exception as e:
                    logging.error(f"Error in event processing task: {e}")
        except asyncio.CancelledError:
            logging.debug("Event processing task cancelled")
            pass

    async def _dispatch_event(self, event: events.Event) -> None:
        """
        Dispatch event to registered handlers based on event type.

        Args:
            event: The event to dispatch to handlers
        """
        # Process the event through the appropriate handlers
        for event_type, handlers in self._event_handlers.items():
            matched = False

            # Check if this event matches the registered event type
            match event_type:
                case "rtc_packet":
                    matched = event.rtc_packet is not None
                case "audio_packet":
                    matched = (
                        event.rtc_packet is not None
                        and event.rtc_packet.audio is not None
                    )
                case "participant_joined":
                    matched = event.participant_joined is not None
                case "participant_left":
                    matched = event.participant_left is not None
                case "call_ended":
                    matched = event.call_ended is not None
                case "error":
                    matched = event.error is not None
                case _:
                    matched = False

            # Call all handlers registered for this event type
            if matched:
                for handler in handlers:
                    await handler(event)

    def add_event_handler(self, event_type: str, handler: callable) -> None:
        """
        Register an event handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Async callback function that will be called with the event
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: callable) -> None:
        """
        Remove a registered event handler.

        Args:
            event_type: Type of event the handler was registered for
            handler: The handler function to remove
        """
        if event_type in self._event_handlers:
            if handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)


class RTCCall(Call):
    def __init__(
        self, client, call_type: str, call_id: str = None, custom_data: Dict = None
    ):
        super().__init__(client, call_type, call_id, custom_data)
        self._joined = False
        self._rtc_id = None
        self._cb = None  # not sure if this is needed, maybe its needed to keep one ref
        self.audio_queue = asyncio.Queue()  # this is here just for testing things out, we need something a bit more flexible and generic in reality
        self.ev_loop = None  # not super sure
        self._join_future = None  # Future to track join status
        self._event_queue = asyncio.Queue()  # Queue to track events
        self._mock_config = None  # Mock configuration for testing

    def set_mock(self, mock_config: MockConfig):
        """
        Set mock configuration for testing.

        Args:
            mock_config: The mock configuration to use.

        Returns:
            Self for method chaining.
        """
        self._mock_config = mock_config
        return self

    def join(self, user_id: str, timeout: float = 30.0) -> ConnectionManager:
        """
        Join a call and return a connection manager that can be used as an async context manager.

        Usage:
            async with call.join("user-id") as connection:
                async for event in connection:
                    # Process event

            # Or to iterate only over audio events:
            async with call.join("user-id") as connection:
                async for participant, audio in connection.incoming_audio:
                    sample_rate, pcm_data = audio
                    # Process audio data

        Args:
            user_id: The ID of the user joining the call
            timeout: Maximum time to wait for the join operation to complete, in seconds

        Returns:
            A ConnectionManager instance that serves as both an async context manager and iterator

        Raises:
            RuntimeError: If the call is already joined
        """
        if self._joined:
            raise RuntimeError("Already joined")

        return ConnectionManager(self, user_id, timeout)

    async def leave(self):
        """Leave the call."""
        if not self._joined:
            return

        # Stop any mock if we were using one
        if self._mock_config:
            # Convert to C strings
            c_call_type = ffi.new("char[]", self.call_type.encode("utf-8"))
            c_call_id = ffi.new("char[]", self.id.encode("utf-8"))

            # Tell Go to stop the call (works for both mock and real calls)
            lib.Leave(c_call_type, c_call_id)

            logging.debug("Stopped call")

        # Mark call as left
        self._joined = False
        logging.debug("Left call")

    async def send_audio(
        self,
        stream: Union[bytes, AsyncGenerator[bytes, None]],
        channels: AudioChannels = AudioChannels.Mono,
        format: AudioFormat = AudioFormat.Float32,
        rate: int = 48_000,
    ):
        pass

    def on_rtc_event_payload(self, event: events.Event):
        # Process the event on the event loop to ensure thread safety
        if self.ev_loop:
            self.ev_loop.call_soon_threadsafe(self._process_event, event)

    def _process_event(self, event: events.Event):
        # If we have a pending join operation
        if self._join_future and not self._join_future.done():
            logging.debug(f"Processing join event: {event}")
            logging.debug(f"Event type: {type(event)}")
            logging.debug(f"Event fields: {event.to_dict()}")

            # Check if this is a join response event
            if event.call_join_response is not None:
                logging.debug("Matched join response event")
                self._join_future.set_result(event.call_join_response)
            # Check if this is an error event
            elif event.error is not None and event.error != events.Error():
                logging.debug("Matched error event")
                self._join_future.set_exception(
                    JoinError(event.error.code, event.error.message)
                )
            else:
                logging.debug("No match found for event")
                self._join_future.set_exception(TypeError(f"unexpected event {event}"))
            return

        # Handle other event types
        match event:
            case events.Event(rtc_packet=rtc_packet):
                # Handle audio data
                if hasattr(rtc_packet.audio, "pcm") and rtc_packet.audio.pcm:
                    self.audio_queue.put_nowait(rtc_packet.audio.pcm.payload)
                    logging.debug("Queued audio data")

                # Put the RTC packet event in the general event queue
                self._event_queue.put_nowait(event)
                logging.debug(f"Queued RTC packet event: {event}")
            case events.Event(participant_joined=participant_joined):
                # Handle participant joined event
                logging.debug(f"Participant joined: {participant_joined.user_id}")
                self._event_queue.put_nowait(event)
            case events.Event(participant_left=participant_left):
                # Handle participant left event
                logging.debug(f"Participant left: {participant_left.user_id}")
                self._event_queue.put_nowait(event)
            case _:
                # Put any other event in the general event queue
                self._event_queue.put_nowait(event)
                logging.debug(f"Queued other event: {event}")

    def __del__(self):
        # TODO: tell go RTC layer that we can garbage collect this call
        pass


def make_rtc_event_callback(call: RTCCall):
    """
    Returns a C function ready to be passed to the Go Join function, the callback
    takes care of parsing the bytes into a events.Event object, release the memory and
    then it will pass it to the RTCCall instance's _on_rtc_event_payload method

    :param call: the RTCCall object that we want to bind
    :return:
    """

    @ffi.callback("void(const char*, size_t)")
    def event_callback(payload: bytes, length: int):
        if payload == ffi.NULL:
            return
        try:
            serialized_data = ffi.buffer(payload, length)[:]
            logging.debug(f"Raw event data from Go: {serialized_data.hex()}")

            # Create the event object from the serialized data
            event = events.Event().parse(serialized_data)

            # Forward the event to the RTCCall
            call.on_rtc_event_payload(event)

        except Exception as e:
            logging.error(f"Error processing event from Go: {e}")
        finally:
            # Always free the payload memory to avoid leaks
            lib.free(payload)

    return event_callback


async def on_event(
    connection: ConnectionManager,
    event_type: str,
    handler: Callable[[events.Event], Awaitable[None]],
) -> None:
    """
    Binds an event handler to the connection based on event_type.

    The handler will be called whenever an event of the specified type is received.

    Args:
        connection: The ConnectionManager to register the handler with
        event_type: Type of event to handle, one of:
                   - "rtc_packet": any RTC packet
                   - "audio_packet": an audio packet (RTCPacket.AudioPayload)
                   - "participant_joined": when a participant joins the call
                   - "participant_left": when a participant leaves the call
                   - "error": error events
        handler: Async callback function that will be called with the event
                The handler signature should be: async def handler(event: events.Event)

    Example:
        async def on_participant_joined(event):
            participant = event.participant_joined
            print(f"Participant joined: {participant.user_id}")

        await on_event(connection, "participant_joined", on_participant_joined)
    """
    connection.add_event_handler(event_type, handler)
