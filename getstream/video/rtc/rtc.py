import io

import numpy as np

import inspect

import asyncio
import torch
import torchaudio
from typing import Dict, Union, AsyncGenerator

import cffi

from getstream.video.call import Call
from pb import events
from enum import Enum


ffi = cffi.FFI()
ffi.cdef("""
    typedef void (*CallbackFunc)(const char*, size_t);
    void Join(CallbackFunc callback);
    void SendAudio(char* cData, size_t data);
    void free(void *ptr);
""")

lib = ffi.dlopen("./libstreamvideo.so")


class AudioFormat(Enum):
    Float32 = events.AudioFormat.Float32
    Int32 = events.AudioFormat.Int32
    Int16 = events.AudioFormat.Int16


class AudioChannels(Enum):
    Mono = 1
    Stereo = 2


def create_ogg_from_pcm(pcm, sample_rate=48000):
    # Calculate number of samples per 20ms chunk
    chunk_size = int(sample_rate * 20 / 1000)  # 20ms chunk at given sample rate

    # Convert PCM bytes to numpy array and then to a PyTorch tensor
    pcm_array = np.frombuffer(pcm, dtype=np.float32)
    pcm_array = np.expand_dims(pcm_array, axis=0)  # Ensure it's 2D [channels, samples]
    pcm_tensor = torch.from_numpy(pcm_array)

    # Create in-memory bytes buffer for the Ogg file
    ogg_bytes = io.BytesIO()

    # Create a list to hold all the chunks
    chunks = []

    # Process each 20ms chunk and add it to the list
    for i in range(0, pcm_tensor.shape[1], chunk_size):
        chunk = pcm_tensor[:, i : i + chunk_size]  # Get the 20ms chunk
        if chunk.shape[1] < chunk_size:
            chunk = torch.nn.functional.pad(
                chunk, (0, chunk_size - chunk.shape[1])
            )  # Pad the last chunk with zeros
        chunks.append(chunk)

    # Concatenate all the chunks into a single tensor
    final_tensor = torch.cat(chunks, dim=1)  # Concatenate along the time axis

    # Save the entire tensor as a single Ogg Opus file
    torchaudio.save(ogg_bytes, final_tensor, sample_rate, format="ogg", encoding="opus")

    return ogg_bytes.getvalue()


def create_ogg_from_pcm(pcm, sample_rate=48000):
    # Calculate number of samples per 20ms chunk
    chunk_size = int(sample_rate * 20 / 1000)  # 20ms chunk at given sample rate

    # Convert PCM bytes to numpy array and then to a PyTorch tensor
    pcm_array = np.frombuffer(pcm, dtype=np.float32)
    pcm_array = np.expand_dims(pcm_array, axis=0)  # Ensure it's 2D [channels, samples]
    pcm_tensor = torch.from_numpy(pcm_array)

    # Create in-memory bytes buffer for the Ogg file
    ogg_bytes = io.BytesIO()

    # Create a list to hold all the chunks
    chunks = []

    # Process each 20ms chunk and add it to the list
    for i in range(0, pcm_tensor.shape[1], chunk_size):
        chunk = pcm_tensor[:, i : i + chunk_size]  # Get the 20ms chunk
        if chunk.shape[1] < chunk_size:
            chunk = torch.nn.functional.pad(
                chunk, (0, chunk_size - chunk.shape[1])
            )  # Pad the last chunk with zeros
        chunks.append(chunk)

    # Concatenate all the chunks into a single tensor
    final_tensor = torch.cat(chunks, dim=1)  # Concatenate along the time axis

    # Save the entire tensor as a single Ogg Opus file
    torchaudio.save(ogg_bytes, final_tensor, sample_rate, format="ogg", encoding="opus")

    return ogg_bytes.getvalue()


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
        lib.Join(cb)
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
        # just send the stream to Go SDK since we got bytes
        if not inspect.isasyncgen(stream):
            print("got bytes, send them to Go SDK")
            ogg_bytes = create_ogg_from_pcm(stream)

            with open("/Users/tommaso/Downloads/ogg_bytes.ogg", "wb") as f:
                f.write(ogg_bytes)

            data = events.AudioPayload(
                ogg=events.OggOpusPayload(payload=ogg_bytes),
            ).__bytes__()
            c_data = ffi.new("char[]", data)
            lib.SendAudio(c_data, len(data))
            return

        print("got an async generator of bytes!")
        # if the stream is an async generator, we will send the audio when we have at least 20ms of audio accumulated
        flush_size = 0.05 * rate
        accumulated_bytes = []
        async for value in stream:
            accumulated_bytes += value
            if len(accumulated_bytes) >= flush_size:
                print(f"for {len(accumulated_bytes)} bytes, flush them now :)")
                # TODO: send to Go SDK now that we have enough data and reset the array of accumulated bytes
                accumulated_bytes = []

    def leave(self):
        # TODO: tell go RTC layer that we want to disconnect from this call
        pass

    def on_rtc_event_payload(self, event: events.Event):
        match event:
            case events.Event(rtc_packet=rtc_packet):
                # this is needed to keep the callback on the main thread and to ensure that put_nowait will wake up
                # the event loop where call.join was executed
                self.ev_loop.call_soon_threadsafe(
                    self.audio_queue.put_nowait, rtc_packet.audio.payload
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
