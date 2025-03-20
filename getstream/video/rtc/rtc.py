import os


import asyncio
from typing import Dict, Union, AsyncGenerator, AsyncIterator
import logging

import cffi

from getstream.video.call import Call
from getstream.video.rtc.pb import events
from enum import Enum


ffi = cffi.FFI()
ffi.cdef("""
    typedef void (*CallbackFunc)(const char*, size_t);
    void Join(const char* apiKey, const char* token, const char* callType, const char* callId, CallbackFunc callback);
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

        # Mark that we're using the current event loop
        self.call.ev_loop = asyncio.get_event_loop()

        # Call the Go function with API credentials and call info (non-blocking)
        lib.Join(c_api_key, c_token, c_call_type, c_call_id, cb)

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

        # TODO: implement leave functionality by telling Go to disconnect
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
            match event:
                case events.Event(error=value):
                    self._join_future.set_exception(
                        JoinError(value.code, value.message)
                    )
                case events.Event(call_join_response=value):
                    self._join_future.set_result(value)
                case _:
                    self._join_future.set_exception(
                        TypeError(f"unexpected event {event}")
                    )
            return

        # Handle other event types
        match event:
            case events.Event(rtc_packet=rtc_packet):
                # Handle audio data
                if hasattr(rtc_packet.audio, "pcm") and rtc_packet.audio.pcm:
                    self.audio_queue.put_nowait(rtc_packet.audio.pcm.payload)

                # Also put the RTC packet event in the general event queue
                self._event_queue.put_nowait(event)
            case _:
                logging.debug(f"Got event: {event}")
                self._event_queue.put_nowait(event)

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
        serialized_data = ffi.buffer(payload, length)[:]
        # make sure that we free the payload and re-raise if necessary (otherwise we could silently leak)
        try:
            event = events.Event()
            event.parse(serialized_data)
        finally:
            lib.free(payload)
        call.on_rtc_event_payload(event)

    return event_callback
