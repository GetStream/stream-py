import os


import asyncio
from typing import Dict, Union, AsyncGenerator
import logging

import cffi

from getstream.video.call import Call
from getstream.video.rtc.pb import events
from enum import Enum


ffi = cffi.FFI()
ffi.cdef("""
    typedef void (*CallbackFunc)(const char*, size_t);
    void Join(const char* apiKey, const char* apiSecret, CallbackFunc callback);
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

    async def join(self, user_id: str, timeout: float = 30.0) -> None:
        """
        Join a call asynchronously.

        Args:
            user_id: The ID of the user joining the call
            timeout: Maximum time to wait for the join operation to complete, in seconds

        Raises:
            JoinError: If joining the call fails
            asyncio.TimeoutError: If the join operation times out
        """
        if self._joined:
            raise RuntimeError("Already joined")

        # Create a future to track join status
        self._join_future = asyncio.Future()

        # Get API key and secret from the client
        api_key = self.client.stream.api_key
        api_secret = self.client.stream.api_secret

        # Create the callback
        cb = make_rtc_event_callback(self)
        self._cb = cb  # Keep a reference to prevent garbage collection

        # Convert to C strings
        c_api_key = ffi.new("char[]", api_key.encode("utf-8"))
        c_api_secret = ffi.new("char[]", api_secret.encode("utf-8"))

        # Mark that we're using the current event loop
        self.ev_loop = asyncio.get_event_loop()

        # Call the Go function with API credentials (non-blocking)
        lib.Join(c_api_key, c_api_secret, cb)

        try:
            # Wait for join response or error with timeout
            await asyncio.wait_for(self._join_future, timeout=timeout)
            self._joined = True
        except asyncio.TimeoutError:
            # Timed out waiting for join response
            raise asyncio.TimeoutError(
                f"Timed out waiting to join call after {timeout} seconds"
            )

    async def send_audio(
        self,
        stream: Union[bytes, AsyncGenerator[bytes, None]],
        channels: AudioChannels = AudioChannels.Mono,
        format: AudioFormat = AudioFormat.Float32,
        rate: int = 48_000,
    ):
        pass

    def leave(self):
        # TODO: tell go RTC layer that we want to disconnect from this call
        pass

    def on_rtc_event_payload(self, event: events.Event):
        # Process the event on the event loop to ensure thread safety
        if self.ev_loop:
            self.ev_loop.call_soon_threadsafe(self._process_event, event)

    def _process_event(self, event: events.Event):
        # If we have a pending join operation
        if self._join_future and not self._join_future.done():
            # Check if this is a join response or error
            if event.error:
                self._join_future.set_exception(
                    JoinError(event.error.code, event.error.message)
                )
                return
            elif event.call_join_response:
                self._join_future.set_result(None)  # Successful join
                return

        # Handle other event types
        match event:
            case events.Event(rtc_packet=rtc_packet):
                # this is needed to keep the callback on the main thread and to ensure that put_nowait will wake up
                # the event loop where call.join was executed
                self.audio_queue.put_nowait(rtc_packet.audio.pcm.payload)
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
