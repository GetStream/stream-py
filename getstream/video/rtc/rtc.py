import os


import asyncio
from typing import Dict, Union, AsyncGenerator

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

    async def join(self, user_id: str):
        if self._joined:
            raise RuntimeError("Already joined")
        # TODO: we should keep a reference to the go rtc call object here
        cb = make_rtc_event_callback(self)
        self._cb = cb  # maybe not needed, just here to be safe (GC)

        # Get API key and secret from the client
        api_key = self.client.stream.api_key
        api_secret = self.client.stream.api_secret

        # Convert to C strings
        c_api_key = ffi.new("char[]", api_key.encode("utf-8"))
        c_api_secret = ffi.new("char[]", api_secret.encode("utf-8"))

        # Call the Go function with API credentials
        lib.Join(c_api_key, c_api_secret, cb)

        # Mark as joined
        self._joined = True

        # this call.join method should run on the event loop where all processing is done
        self.ev_loop = asyncio.get_event_loop()
        await asyncio.sleep(60)  # this needs to be removed eventually

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
        match event:
            case events.Event(rtc_packet=rtc_packet):
                # this is needed to keep the callback on the main thread and to ensure that put_nowait will wake up
                # the event loop where call.join was executed
                self.ev_loop.call_soon_threadsafe(
                    self.audio_queue.put_nowait, rtc_packet.audio.pcm.payload
                )
            case _:
                print(f"got an event {event}!")

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
