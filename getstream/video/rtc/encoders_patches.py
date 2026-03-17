import logging
import os
from typing import Optional

from aiortc import RTCRtpCodecParameters
from aiortc.codecs.h264 import H264Encoder
from aiortc.codecs.vpx import Vp8Encoder
from aiortc.rtcrtpsender import RTCEncodedFrame, RTCRtpSender

logger = logging.getLogger(__name__)

# Stream video bitrate overrides (applied per-connection, not globally).
# These are higher than aiortc defaults to ensure acceptable video quality.
STREAM_VIDEO_DEFAULT_BITRATE = 2_500_000  # 2.5 Mbps
STREAM_VIDEO_MIN_BITRATE = 1_500_000  # 1.5 Mbps
STREAM_VIDEO_MAX_BITRATE = 3_000_000  # 3 Mbps


# Check if the Stream bitrate patching is disabled via environment variable
BITRATE_PATCH_DISABLED = os.getenv(
    "STREAM_PATCH_AIORTC_BITRATES", ""
).lower().strip() in (
    "0",
    "false",
    "no",
    "off",
)


try:
    # Verify the name-mangled attributes we depend on still exist.
    assert hasattr(Vp8Encoder(), "_Vp8Encoder__target_bitrate")
    assert hasattr(H264Encoder(), "_H264Encoder__target_bitrate")

    class StreamVp8Encoder(Vp8Encoder):
        """Vp8Encoder subclass with higher bitrate bounds for Stream calls."""

        def __init__(self) -> None:
            super().__init__()
            self._Vp8Encoder__target_bitrate = STREAM_VIDEO_DEFAULT_BITRATE

        @property
        def target_bitrate(self) -> int:
            return self._Vp8Encoder__target_bitrate

        @target_bitrate.setter
        def target_bitrate(self, bitrate: int) -> None:
            bitrate = max(
                STREAM_VIDEO_MIN_BITRATE, min(bitrate, STREAM_VIDEO_MAX_BITRATE)
            )
            self._Vp8Encoder__target_bitrate = bitrate

    class StreamH264Encoder(H264Encoder):
        """H264Encoder subclass with higher bitrate bounds for Stream calls."""

        def __init__(self) -> None:
            super().__init__()
            self._H264Encoder__target_bitrate = STREAM_VIDEO_DEFAULT_BITRATE

        @property
        def target_bitrate(self) -> int:
            return self._H264Encoder__target_bitrate

        @target_bitrate.setter
        def target_bitrate(self, bitrate: int) -> None:
            bitrate = max(
                STREAM_VIDEO_MIN_BITRATE, min(bitrate, STREAM_VIDEO_MAX_BITRATE)
            )
            self._H264Encoder__target_bitrate = bitrate

except Exception:
    logger.warning(
        "Failed to patch aiortc video encoder subclasses with Stream bitrate values (aiortc internals may have changed), "
        "falling back to default aiortc bitrates. \n"
        "Set STREAM_PATCH_AIORTC_BITRATES=0 to disable patching.",
        exc_info=True,
    )
    StreamVp8Encoder = None  # type: ignore[assignment, misc]
    StreamH264Encoder = None  # type: ignore[assignment, misc]


def patch_sender_encoder(sender: RTCRtpSender) -> None:
    """Patch a video sender to use Stream's higher-bitrate encoders.

    If anything goes wrong (e.g. aiortc internals changed), the sender
    is left untouched and will use the stock encoder via get_encoder().
    """
    if StreamVp8Encoder is None or StreamH264Encoder is None:
        return

    try:
        _orig_next = sender._next_encoded_frame

        async def _next_with_stream_encoder(
            codec: RTCRtpCodecParameters, _orig_next=_orig_next
        ) -> Optional[RTCEncodedFrame]:
            if sender._RTCRtpSender__encoder is None:  # type: ignore[attr-defined]
                mime = codec.mimeType.lower()
                if mime == "video/vp8":
                    sender._RTCRtpSender__encoder = StreamVp8Encoder()  # type: ignore[attr-defined]
                elif mime == "video/h264":
                    sender._RTCRtpSender__encoder = StreamH264Encoder()  # type: ignore[attr-defined]
            return await _orig_next(codec)

        sender._next_encoded_frame = _next_with_stream_encoder  # type: ignore[method-assign]
    except Exception:
        logger.warning(
            "Failed to patch aiortc video encoder subclasses with Stream bitrate values (aiortc internals may have changed), "
            "falling back to default aiortc bitrates. \n"
            "Set STREAM_PATCH_AIORTC_BITRATES=0 to disable patching.",
            exc_info=True,
        )
