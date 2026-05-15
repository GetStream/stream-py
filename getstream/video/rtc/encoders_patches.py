import fractions
import logging
import os
from typing import Optional

import av
from aiortc import RTCRtpCodecParameters
from aiortc.codecs.h264 import MAX_FRAME_RATE as H264_MAX_FRAME_RATE
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

# libx264 preset for the StreamH264Encoder. Defaults to "ultrafast" for
# real-time CPU; can be raised (e.g. "veryfast", "medium") for better
# quality-per-bit at the cost of more CPU per frame.
STREAM_H264_PRESET = os.getenv("STREAM_PATCH_AIORTC_H264_PRESET", "ultrafast").strip()


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
        """H264Encoder subclass with higher bitrate bounds and a real-time
        libx264 preset for Stream calls."""

        def __init__(self) -> None:
            super().__init__()
            self._H264Encoder__target_bitrate = STREAM_VIDEO_DEFAULT_BITRATE
            self.preset = STREAM_H264_PRESET

        @property
        def target_bitrate(self) -> int:
            return self._H264Encoder__target_bitrate

        @target_bitrate.setter
        def target_bitrate(self, bitrate: int) -> None:
            bitrate = max(
                STREAM_VIDEO_MIN_BITRATE, min(bitrate, STREAM_VIDEO_MAX_BITRATE)
            )
            self._H264Encoder__target_bitrate = bitrate

        def _encode_frame(self, frame, force_keyframe):
            # Mirror parent's invalidation policy so we own codec creation in
            # both first-init AND recreation (resolution/bitrate change) paths;
            # otherwise parent's `if self.codec is None` branch silently
            # reverts our preset to libx264's default `medium`.
            codec = self.codec
            if (
                codec is not None
                and codec.bit_rate
                and (
                    frame.width != codec.width
                    or frame.height != codec.height
                    or abs(self.target_bitrate - codec.bit_rate) / codec.bit_rate > 0.1
                )
            ):
                self.buffer_data = b""
                self.buffer_pts = None
                self.codec = None

            if self.codec is None:
                self.codec = av.CodecContext.create("libx264", "w")
                self.codec.width = frame.width
                self.codec.height = frame.height
                self.codec.bit_rate = self.target_bitrate
                self.codec.pix_fmt = "yuv420p"
                self.codec.framerate = fractions.Fraction(H264_MAX_FRAME_RATE, 1)
                self.codec.time_base = fractions.Fraction(1, H264_MAX_FRAME_RATE)
                self.codec.options = {
                    "level": "31",
                    "tune": "zerolatency",
                    "preset": self.preset,
                }
                self.codec.profile = "Baseline"
            yield from super()._encode_frame(frame, force_keyframe)

except Exception:
    logger.warning(
        "Failed to patch aiortc encoder subclasses with Stream values (aiortc internals may have changed), "
        "falling back to default aiortc encoders. \n"
        "Set STREAM_PATCH_AIORTC_BITRATES=0 to disable patching.",
        exc_info=True,
    )
    StreamVp8Encoder = None  # type: ignore[assignment, misc]
    StreamH264Encoder = None  # type: ignore[assignment, misc]


def patch_sender_encoder(sender: RTCRtpSender) -> None:
    """Patch a sender to use Stream's tuned encoders for the negotiated codec.

    Works for video (VP8/H264) senders. If anything
    goes wrong (e.g. aiortc internals changed), the sender is left untouched
    and will use the stock encoder via get_encoder().
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
            "Failed to patch aiortc encoder subclasses with Stream values (aiortc internals may have changed), "
            "falling back to default aiortc encoders. \n"
            "Set STREAM_PATCH_AIORTC_BITRATES=0 to disable patching.",
            exc_info=True,
        )
