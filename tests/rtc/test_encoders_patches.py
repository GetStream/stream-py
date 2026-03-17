import importlib
from unittest.mock import MagicMock

import pytest
from aiortc.codecs.h264 import H264Encoder
from aiortc.codecs.vpx import Vp8Encoder

from getstream.video.rtc.encoders_patches import (
    STREAM_VIDEO_DEFAULT_BITRATE,
    STREAM_VIDEO_MAX_BITRATE,
    STREAM_VIDEO_MIN_BITRATE,
    StreamH264Encoder,
    StreamVp8Encoder,
    patch_sender_encoder,
)

# Original upstream values
ORIGINAL_VPX = {
    "DEFAULT_BITRATE": 500_000,
    "MIN_BITRATE": 250_000,
    "MAX_BITRATE": 1_500_000,
}
ORIGINAL_H264 = {
    "DEFAULT_BITRATE": 1_000_000,
    "MIN_BITRATE": 500_000,
}


class TestStreamVp8Encoder:
    def test_default_bitrate(self):
        enc = StreamVp8Encoder()
        assert enc.target_bitrate == STREAM_VIDEO_DEFAULT_BITRATE

    def test_clamps_above_max(self):
        enc = StreamVp8Encoder()
        enc.target_bitrate = 999_999_999
        assert enc.target_bitrate == STREAM_VIDEO_MAX_BITRATE

    def test_clamps_below_min(self):
        enc = StreamVp8Encoder()
        enc.target_bitrate = 1
        assert enc.target_bitrate == STREAM_VIDEO_MIN_BITRATE

    def test_accepts_in_range(self):
        enc = StreamVp8Encoder()
        enc.target_bitrate = 2_000_000
        assert enc.target_bitrate == 2_000_000


class TestStreamH264Encoder:
    def test_default_bitrate(self):
        enc = StreamH264Encoder()
        assert enc.target_bitrate == STREAM_VIDEO_DEFAULT_BITRATE

    def test_clamps_above_max(self):
        enc = StreamH264Encoder()
        enc.target_bitrate = 999_999_999
        assert enc.target_bitrate == STREAM_VIDEO_MAX_BITRATE

    def test_clamps_below_min(self):
        enc = StreamH264Encoder()
        enc.target_bitrate = 1
        assert enc.target_bitrate == STREAM_VIDEO_MIN_BITRATE

    def test_accepts_in_range(self):
        enc = StreamH264Encoder()
        enc.target_bitrate = 2_000_000
        assert enc.target_bitrate == 2_000_000


class TestBitratePatchDisabled:
    @pytest.mark.parametrize("env_val", [None, "", "1", "true", "yes", "on"])
    def test_enabled_by_default(self, monkeypatch, env_val):
        """BITRATE_PATCH_DISABLED is False when env var is unset or truthy."""
        if env_val is None:
            monkeypatch.delenv("STREAM_PATCH_AIORTC_BITRATES", raising=False)
        else:
            monkeypatch.setenv("STREAM_PATCH_AIORTC_BITRATES", env_val)

        import getstream.video.rtc.encoders_patches as mod

        importlib.reload(mod)
        assert mod.BITRATE_PATCH_DISABLED is False

    @pytest.mark.parametrize("env_val", ["0", "false", "no", "off"])
    def test_disabled_via_env(self, monkeypatch, env_val):
        """BITRATE_PATCH_DISABLED is True when env var is a falsy value."""
        monkeypatch.setenv("STREAM_PATCH_AIORTC_BITRATES", env_val)

        import getstream.video.rtc.encoders_patches as mod

        importlib.reload(mod)
        assert mod.BITRATE_PATCH_DISABLED is True


class TestPatchSenderEncoder:
    @pytest.mark.asyncio
    async def test_installs_vp8_encoder(self):
        sender = MagicMock()
        sender._RTCRtpSender__encoder = None

        async def _orig_coro(codec):
            return None

        sender._next_encoded_frame = _orig_coro
        patch_sender_encoder(sender)

        codec = MagicMock()
        codec.mimeType = "video/VP8"
        await sender._next_encoded_frame(codec)

        from getstream.video.rtc.encoders_patches import StreamVp8Encoder as Vp8Cls

        assert isinstance(sender._RTCRtpSender__encoder, Vp8Cls)

    @pytest.mark.asyncio
    async def test_installs_h264_encoder(self):
        sender = MagicMock()
        sender._RTCRtpSender__encoder = None

        async def _orig_coro(codec):
            return None

        sender._next_encoded_frame = _orig_coro
        patch_sender_encoder(sender)

        codec = MagicMock()
        codec.mimeType = "video/H264"
        await sender._next_encoded_frame(codec)

        from getstream.video.rtc.encoders_patches import StreamH264Encoder as H264Cls

        assert isinstance(sender._RTCRtpSender__encoder, H264Cls)

    @pytest.mark.asyncio
    async def test_does_not_replace_existing_encoder(self):
        """Already-set encoder is not replaced."""
        sender = MagicMock()
        existing_encoder = MagicMock()
        sender._RTCRtpSender__encoder = existing_encoder

        async def _orig_coro(codec):
            return None

        sender._next_encoded_frame = _orig_coro
        patch_sender_encoder(sender)

        codec = MagicMock()
        codec.mimeType = "video/H264"
        await sender._next_encoded_frame(codec)
        assert sender._RTCRtpSender__encoder is existing_encoder

    def test_noop_when_encoders_none(self, monkeypatch):
        """patch_sender_encoder is a no-op when encoder classes failed to load."""
        import getstream.video.rtc.encoders_patches as mod

        monkeypatch.setattr(mod, "StreamVp8Encoder", None)
        sender = MagicMock()
        orig = sender._next_encoded_frame
        mod.patch_sender_encoder(sender)
        assert sender._next_encoded_frame is orig


class TestUpstreamAssumptions:
    def test_upstream_assumptions_hold(self):
        """Canary: fails if aiortc changes its internal API.

        Our per-sender patching relies on name-mangled attributes and
        the _next_encoded_frame method. If this breaks after an aiortc
        upgrade, review the upstream code and update accordingly.
        """
        vp8 = Vp8Encoder()
        assert hasattr(vp8, "target_bitrate"), "Vp8Encoder lost target_bitrate"

        h264 = H264Encoder()
        assert hasattr(h264, "target_bitrate"), "H264Encoder lost target_bitrate"

        # Name-mangled __target_bitrate is accessible from subclasses
        assert hasattr(vp8, "_Vp8Encoder__target_bitrate"), (
            "Vp8Encoder name-mangled __target_bitrate changed"
        )
        assert hasattr(h264, "_H264Encoder__target_bitrate"), (
            "H264Encoder name-mangled __target_bitrate changed"
        )

        # RTCRtpSender has _next_encoded_frame and uses __encoder
        import inspect

        from aiortc.rtcrtpsender import RTCRtpSender

        assert hasattr(RTCRtpSender, "_next_encoded_frame"), (
            "RTCRtpSender lost _next_encoded_frame"
        )
        source = inspect.getsource(RTCRtpSender._next_encoded_frame)
        assert "self.__encoder" in source, (
            "RTCRtpSender._next_encoded_frame no longer uses self.__encoder"
        )
