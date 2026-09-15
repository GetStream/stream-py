import fractions
import logging
import os
from typing import Optional

import av
from aiortc import RTCRtpCodecParameters
from aiortc.codecs.h264 import MAX_FRAME_RATE as H264_MAX_FRAME_RATE
from aiortc.codecs.h264 import H264Encoder
from aiortc.codecs.opus import SAMPLE_RATE as OPUS_SAMPLE_RATE
from aiortc.codecs.opus import SAMPLES_PER_FRAME as OPUS_SAMPLES_PER_FRAME
from aiortc.codecs.opus import OpusEncoder
from aiortc.codecs.vpx import Vp8Encoder
from aiortc.rtcrtpsender import RTCEncodedFrame, RTCRtpSender
from av import AudioResampler

logger = logging.getLogger(__name__)

# Stream video bitrate overrides (applied per-connection, not globally).
# These are higher than aiortc defaults to ensure acceptable video quality.
STREAM_VIDEO_DEFAULT_BITRATE = 2_500_000  # 2.5 Mbps
STREAM_VIDEO_MIN_BITRATE = 1_500_000  # 1.5 Mbps
STREAM_VIDEO_MAX_BITRATE = 3_000_000  # 3 Mbps

# Override hardcoded Opus defaults to reduce CPU usage. Lower than aiortc's 96 kbps stereo default; tuned for
# voice. Both are configurable per StreamOpusEncoder() instance.
STREAM_OPUS_DEFAULT_BITRATE = 64_000  # 96kbps -> 64kbps
STREAM_OPUS_DEFAULT_LAYOUT = "mono"  # stereo -> mono
# Compression level <= 7 reduces the CPU work for encoder with minimal quality impact at 64kbps
STREAM_OPUS_DEFAULT_COMPRESSION_LEVEL = 7  # 10 -> 7


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
    # TODO: Implement a way to configure encoders per track.
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


class StreamOpusEncoder(OpusEncoder):
    """OpusEncoder subclass with configurable bitrate and channel layout."""

    def __init__(
        self,
        bitrate: int = STREAM_OPUS_DEFAULT_BITRATE,
        layout: str = STREAM_OPUS_DEFAULT_LAYOUT,
        compression_level: int = STREAM_OPUS_DEFAULT_COMPRESSION_LEVEL,
    ) -> None:
        super().__init__()
        self.codec.bit_rate = bitrate
        self.codec.layout = layout
        self.codec.options = {
            "application": "voip",
            "compression_level": str(compression_level),
        }
        # Resampler layout must match codec layout; parent hard-codes stereo.
        self.resampler = AudioResampler(
            format="s16",
            layout=layout,
            rate=OPUS_SAMPLE_RATE,
            frame_size=OPUS_SAMPLES_PER_FRAME,
        )


def patch_sender_encoder(sender: RTCRtpSender) -> None:
    """Patch a sender to use Stream's tuned encoders for the negotiated codec.

    Works for video (VP8/H264) and audio (Opus) senders. If anything
    goes wrong (e.g. aiortc internals changed), the sender is left untouched
    and will use the stock encoder via get_encoder().
    """
    try:
        _orig_next = sender._next_encoded_frame

        async def _next_with_stream_encoder(
            codec: RTCRtpCodecParameters, _orig_next=_orig_next
        ) -> Optional[RTCEncodedFrame]:
            if sender._RTCRtpSender__encoder is None:  # type: ignore[attr-defined]
                mime = codec.mimeType.lower()
                if mime == "video/vp8" and StreamVp8Encoder is not None:
                    sender._RTCRtpSender__encoder = StreamVp8Encoder()  # type: ignore[attr-defined]
                elif mime == "video/h264" and StreamH264Encoder is not None:
                    sender._RTCRtpSender__encoder = StreamH264Encoder()  # type: ignore[attr-defined]
                elif mime == "audio/opus":
                    sender._RTCRtpSender__encoder = StreamOpusEncoder()  # type: ignore[attr-defined]
            return await _orig_next(codec)

        sender._next_encoded_frame = _next_with_stream_encoder  # type: ignore[method-assign]
    except Exception:
        logger.warning(
            "Failed to patch aiortc encoder subclasses with Stream values (aiortc internals may have changed), "
            "falling back to default aiortc encoders. \n"
            "Set STREAM_PATCH_AIORTC_BITRATES=0 to disable patching.",
            exc_info=True,
        )
