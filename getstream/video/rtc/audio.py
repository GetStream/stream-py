import base64
import numpy as np
from getstream.video.rtc.pb import events


def audio_event_to_openai_pcm(event: events.Event):
    """
    Converts an audio event to what OpenAI PCM format (int16, 24khz, 1 channel)
    """
    if not event or not event.rtc_packet or not event.rtc_packet.audio:
        return

    # Get PCM data and info from Stream
    pcm = event.rtc_packet.audio.pcm
    payload = bytes(pcm.payload)
    sample_rate = pcm.sample_rate  # Usually 48000 Hz
    channels = pcm.channels  # Usually 2 (stereo)

    # Convert bytes to numpy array (assuming int16 format - PCM16)
    # Each sample is 2 bytes (16 bits)
    samples_np = np.frombuffer(payload, dtype=np.int16)

    # Check if we need to convert from stereo to mono
    if channels == 2:
        # Reshape to (n_samples, n_channels)
        samples_np = samples_np.reshape(-1, 2)
        # Convert to mono by averaging channels
        samples_np = samples_np.mean(axis=1, dtype=np.int16)

    # Resample from 48kHz to 24kHz if needed
    if sample_rate == 48000:
        # Simple down sampling by taking every other sample
        # For more accurate resampling, consider using scipy.signal.resample
        samples_np = samples_np[::2]

    # Convert back to bytes (ensuring little-endian)
    audio_bytes = samples_np.astype(np.int16).tobytes()
    return base64.b64encode(audio_bytes).decode("ascii")
