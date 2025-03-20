import os


import asyncio
from typing import Dict, Union, AsyncGenerator, AsyncIterator, List, Optional
import logging

import cffi

from getstream.video.call import Call
from getstream.video.rtc.pb import events
from enum import Enum


ffi = cffi.FFI()
ffi.cdef("""
    typedef void (*CallbackFunc)(const char*, size_t);
    void Join(const char* apiKey, const char* token, const char* callType, const char* callId, const char* mockConfig, size_t mockConfigLen, CallbackFunc callback);
    void StopMock(const char* callType, const char* callId);
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

    def __init__(self, audio_file_path: str, realistic_timing: bool = True):
        """
        Initialize audio configuration for a mocked participant.

        Args:
            audio_file_path: Path to the WAV file to use for audio.
            realistic_timing: If True, send audio events at realistic 20ms intervals.
                              If False, send events as fast as possible.
        """
        self.audio_file_path = audio_file_path
        self.realistic_timing = realistic_timing

    def to_proto(self) -> events.MockAudioConfig:
        """Convert to protobuf message."""
        return events.MockAudioConfig(
            audio_file_path=self.audio_file_path, realistic_timing=self.realistic_timing
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
        except asyncio.TimeoutError:
            # Timed out waiting for join response
            raise asyncio.TimeoutError(
                f"Timed out waiting to join call after {self.timeout} seconds"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager, leaving the call."""
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
            event = await self.call._event_queue.get()
            self.call._event_queue.task_done()
            return event
        except asyncio.CancelledError:
            raise StopAsyncIteration


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

            # Tell Go to stop the mock
            lib.StopMock(c_call_type, c_call_id)

            logging.debug("Stopped mock")

        # TODO: implement leave functionality for real calls by telling Go to disconnect
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
