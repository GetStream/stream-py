import importlib

import pytest

import aiortc.codecs.h264 as h264_codec
import aiortc.codecs.vpx as vpx_codec
from aiortc.codecs.h264 import H264Encoder
from aiortc.codecs.vpx import Vp8Encoder

# Original values from upstream aiortc
ORIGINAL_VPX = {
    "DEFAULT_BITRATE": 500_000,
    "MIN_BITRATE": 250_000,
    "MAX_BITRATE": 1_500_000,
}
ORIGINAL_H264 = {
    "DEFAULT_BITRATE": 1_000_000,
    "MIN_BITRATE": 500_000,
}

# Patched values from _patch_aiortc_video_bitrates
PATCHED_VPX = {
    "DEFAULT_BITRATE": 2_500_000,
    "MIN_BITRATE": 1_500_000,
    "MAX_BITRATE": 3_000_000,
}
PATCHED_H264 = {
    "DEFAULT_BITRATE": 2_500_000,
    "MIN_BITRATE": 1_500_000,
}


def _reset_codec_defaults():
    """Restore upstream aiortc codec constants."""
    for attr, val in ORIGINAL_VPX.items():
        setattr(vpx_codec, attr, val)
    for attr, val in ORIGINAL_H264.items():
        setattr(h264_codec, attr, val)


def _reload_rtc():
    """Reload the rtc __init__ module so the top-level patching code re-runs."""
    import getstream.video.rtc as rtc_mod

    importlib.reload(rtc_mod)


class TestBitratePatch:
    @pytest.fixture(autouse=True, scope="class")
    def _restore_codecs(self):
        """Ensure codec constants are restored after every test."""
        yield
        _reset_codec_defaults()

    @pytest.mark.parametrize("env_val", [None, "", "1", "true", "yes", "on"])
    def test_patch_applied(self, monkeypatch, env_val):
        """Patching is applied by default (env var unset or truthy)."""
        _reset_codec_defaults()
        if env_val is None:
            monkeypatch.delenv("STREAM_PATCH_AIORTC_BITRATES", raising=False)
        else:
            monkeypatch.setenv("STREAM_PATCH_AIORTC_BITRATES", env_val)

        _reload_rtc()

        # Verify via actual encoder instances — newly created encoders
        # pick up DEFAULT_BITRATE and the setter clamps to [MIN, MAX].
        vp8 = Vp8Encoder()
        assert vp8.target_bitrate == PATCHED_VPX["DEFAULT_BITRATE"]

        h264 = H264Encoder()
        assert h264.target_bitrate == PATCHED_H264["DEFAULT_BITRATE"]

        # Setting above MAX should clamp to patched MAX
        vp8.target_bitrate = 999_999_999
        assert vp8.target_bitrate == PATCHED_VPX["MAX_BITRATE"]

        # Setting below MIN should clamp to patched MIN
        vp8.target_bitrate = 1
        assert vp8.target_bitrate == PATCHED_VPX["MIN_BITRATE"]

        h264.target_bitrate = 1
        assert h264.target_bitrate == PATCHED_H264["MIN_BITRATE"]

    @pytest.mark.parametrize("env_val", ["0", "false", "no", "off"])
    def test_patch_disabled(self, monkeypatch, env_val):
        """Patching is skipped when env var is a falsy value."""
        _reset_codec_defaults()
        monkeypatch.setenv("STREAM_PATCH_AIORTC_BITRATES", env_val)

        _reload_rtc()

        # Encoders should use original upstream defaults
        vp8 = Vp8Encoder()
        assert vp8.target_bitrate == ORIGINAL_VPX["DEFAULT_BITRATE"]

        h264 = H264Encoder()
        assert h264.target_bitrate == ORIGINAL_H264["DEFAULT_BITRATE"]

        # Clamping should use original bounds
        vp8.target_bitrate = 999_999_999
        assert vp8.target_bitrate == ORIGINAL_VPX["MAX_BITRATE"]

        vp8.target_bitrate = 1
        assert vp8.target_bitrate == ORIGINAL_VPX["MIN_BITRATE"]

    def test_upstream_assumptions_hold(self):
        """Canary: fails if aiortc changes its codec API or constants.

        Our monkey-patching relies on specific module-level attributes and
        encoder classes with a target_bitrate property that clamps via those
        attributes. If this breaks after an aiortc upgrade, review the new
        upstream code and update _patch_aiortc_video_bitrates() accordingly.
        """
        _reset_codec_defaults()

        # Module-level constants we patch must exist
        for attr in ("DEFAULT_BITRATE", "MIN_BITRATE", "MAX_BITRATE"):
            assert hasattr(vpx_codec, attr), f"aiortc vpx module lost {attr}"
            assert hasattr(h264_codec, attr), f"aiortc h264 module lost {attr}"

        # Encoder classes must exist and expose target_bitrate
        vp8 = Vp8Encoder()
        assert hasattr(vp8, "target_bitrate"), "Vp8Encoder lost target_bitrate"

        h264 = H264Encoder()
        assert hasattr(h264, "target_bitrate"), "H264Encoder lost target_bitrate"

        # target_bitrate setter must clamp using the module constants
        # (set MIN high, verify the encoder respects it)
        vpx_codec.MIN_BITRATE = 999_999
        vp8.target_bitrate = 1
        assert vp8.target_bitrate == 999_999, (
            "Vp8Encoder.target_bitrate setter no longer clamps via vpx.MIN_BITRATE"
        )

        h264_codec.MIN_BITRATE = 888_888
        h264.target_bitrate = 1
        assert h264.target_bitrate == 888_888, (
            "H264Encoder.target_bitrate setter no longer clamps via h264.MIN_BITRATE"
        )

    def test_idempotent(self):
        """Calling the patch function multiple times produces the same result."""
        _reset_codec_defaults()
        from getstream.video.rtc import _patch_aiortc_video_bitrates

        _patch_aiortc_video_bitrates()
        _patch_aiortc_video_bitrates()

        vp8 = Vp8Encoder()
        assert vp8.target_bitrate == PATCHED_VPX["DEFAULT_BITRATE"]

        h264 = H264Encoder()
        assert h264.target_bitrate == PATCHED_H264["DEFAULT_BITRATE"]
