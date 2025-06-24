import logging

# Conditional imports with error handling
try:
    from ten_vad import TenVad
    _ten_available = True
except ImportError:
    TenVad = None  # type: ignore
    _ten_available = False

from getstream_common.vad import VAD
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class TENVad(VAD):
    """Voice-activity detector based on the TEN VAD binary.

    TEN VAD works on 16 kHz mono PCM with hop sizes of 160 or 256 samples. We
    keep the public surface identical to the base :class:`~getstream.plugins.vad.VAD`.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int = 160,
        threshold: float = 0.5,
        **kwargs,
    ) -> None:
        if sample_rate != 16000:
            raise ValueError("TENVad currently supports only 16 kHz audio")
        if frame_size not in (160, 256):
            raise ValueError("frame_size must be 160 (10 ms) or 256 (16 ms)")

        super().__init__(
            sample_rate=sample_rate,
            frame_size=frame_size,
            activation_th=threshold,
            deactivation_th=threshold,
            **kwargs,
        )

        # Check if ten_vad is available
        if not _ten_available:
            raise ImportError(
                "ten-vad dependency missing. Install with\n"
                "    pip install git+https://github.com/TEN-framework/ten-vad.git"
        )

        hop_mode = 0 if frame_size == 160 else 1
        self._vad = TenVad(mode=hop_mode)
        logger.info("TEN VAD initialised – hop=%s samples, threshold=%s", frame_size, threshold)

    async def is_speech(self, frame: PcmData) -> float:
        """Return probability (0.0/1.0) that *frame* contains speech."""
        if frame.sample_rate != 16000:
            raise ValueError("TENVad expects 16 kHz PCM. Resample upstream.")
        if frame.format != "s16":
            raise ValueError("TENVad expects 16-bit signed PCM samples")

        # The binary works with raw bytes and returns 0 or 1
        result = self._vad.process(frame.samples.tobytes())
        return float(result)

    async def close(self) -> None:  # noqa: D401
        """No explicit resources to release."""
        self._vad = None  # type: ignore 