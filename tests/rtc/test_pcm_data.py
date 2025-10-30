import numpy as np
import pytest

from getstream.video.rtc.track_util import PcmData


def _i16_list_from_bytes(b: bytes):
    return list(np.frombuffer(b, dtype=np.int16))


def test_to_bytes_interleaves_from_channel_major():
    # Create (channels, samples) data: L=[1,2,3,4], R=[-1,-2,-3,-4]
    samples = np.array(
        [
            [1, 2, 3, 4],
            [-1, -2, -3, -4],
        ],
        dtype=np.int16,
    )
    pcm = PcmData(samples=samples, sample_rate=16000, format="s16", channels=2)
    out = _i16_list_from_bytes(pcm.to_bytes())
    assert out == [1, -1, 2, -2, 3, -3, 4, -4]


def test_to_bytes_interleaves_from_time_major():
    # Create (samples, channels) data: time-major
    time_major = np.array(
        [
            [1, -1],
            [2, -2],
            [3, -3],
            [4, -4],
        ],
        dtype=np.int16,
    )
    pcm = PcmData(samples=time_major, sample_rate=16000, format="s16", channels=2)
    out = _i16_list_from_bytes(pcm.to_bytes())
    assert out == [1, -1, 2, -2, 3, -3, 4, -4]


def test_resample_upmix_produces_channel_major_and_interleaved_bytes():
    # Mono ramp 1..10
    mono = np.arange(1, 11, dtype=np.int16)
    pcm_mono = PcmData(samples=mono, sample_rate=16000, format="s16", channels=1)

    # Upmix to stereo (same sample rate)
    pcm_stereo = pcm_mono.resample(16000, target_channels=2)
    assert pcm_stereo.channels == 2
    assert hasattr(pcm_stereo, "samples")
    assert isinstance(pcm_stereo.samples, np.ndarray)
    assert pcm_stereo.samples.ndim == 2
    # Expect (channels, samples) shape
    assert pcm_stereo.samples.shape[0] == 2
    # Sample count may be >= input due to resampler buffering; check prefix
    assert pcm_stereo.samples.shape[1] >= mono.shape[0]
    # Both channels should be identical after upmix
    assert np.array_equal(pcm_stereo.samples[0], pcm_stereo.samples[1])

    # Bytes should be interleaved L0,R0,L1,R1,...
    out_bytes = pcm_stereo.to_bytes()
    # Verify interleaving pattern: L[i] == R[i] for a prefix
    out_i16 = _i16_list_from_bytes(out_bytes)
    # take first 2 * N pairs (N from input)
    pairs = min(len(mono), len(out_i16) // 2)
    left = out_i16[0 : 2 * pairs : 2]
    right = out_i16[1 : 2 * pairs : 2]
    assert left == right


def test_resample_rate_and_stereo_size_scaling():
    # 200 mono samples @16kHz -> expect ~3x samples at 48kHz and x2 for stereo
    mono = np.arange(200, dtype=np.int16)
    pcm_mono = PcmData(samples=mono, sample_rate=16000, format="s16", channels=1)

    pcm_48k_stereo = pcm_mono.resample(48000, target_channels=2)
    out = pcm_48k_stereo.to_bytes()

    # 16-bit stereo -> 4 bytes per sample frame
    # 20ms at 48k is 960 frames = 3840 bytes; our total depends on input size
    # Sanity: output length should be >= input_bytes * 6 - small tolerance
    input_bytes = mono.nbytes
    assert len(out) >= input_bytes * 5  # conservative lower bound


# ===== Bug reproduction tests =====


def test_bug_mono_to_stereo_duration_preserved():
    """
    BUG REPRODUCTION: Converting mono to stereo should preserve duration.
    If duration changes, playback will be slowed down or sped up.
    """
    # Create 1 second of mono audio at 16kHz
    sample_rate = 16000
    duration_sec = 1.0
    num_samples = int(sample_rate * duration_sec)

    # Generate a simple sine wave
    t = np.linspace(0, duration_sec, num_samples, dtype=np.float32)
    audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    pcm_mono = PcmData(samples=audio, sample_rate=sample_rate, format="s16", channels=1)

    # Check initial duration
    mono_duration = pcm_mono.duration
    print(f"\nMono duration: {mono_duration}s (expected ~1.0s)")
    assert abs(mono_duration - duration_sec) < 0.01, (
        f"Mono duration should be ~{duration_sec}s, got {mono_duration}s"
    )

    # Convert to stereo (no resampling, just channel conversion)
    pcm_stereo = pcm_mono.resample(sample_rate, target_channels=2)

    # Duration should be EXACTLY the same
    stereo_duration = pcm_stereo.duration
    print(f"Stereo duration: {stereo_duration}s (expected ~1.0s)")
    print(f"Stereo shape: {pcm_stereo.samples.shape} (expected (2, {num_samples}))")

    assert abs(stereo_duration - duration_sec) < 0.01, (
        f"Stereo duration should be ~{duration_sec}s, got {stereo_duration}s (BUG: playback will be wrong!)"
    )

    # Verify shape is correct (channels, samples)
    assert pcm_stereo.samples.shape[0] == 2, (
        f"First dimension should be channels (2), got shape {pcm_stereo.samples.shape}"
    )
    assert pcm_stereo.samples.shape[1] >= num_samples - 10, (
        f"Second dimension should be ~samples ({num_samples}), got shape {pcm_stereo.samples.shape}"
    )


def test_bug_resample_16khz_to_48khz_quality():
    """
    BUG REPRODUCTION: Resampling 16kHz to 48kHz should produce correct sample count.
    If sample count is wrong, quality will be bad.
    """
    # Create 1 second of mono audio at 16kHz
    sample_rate_in = 16000
    sample_rate_out = 48000
    duration_sec = 1.0
    num_samples_in = int(sample_rate_in * duration_sec)

    # Generate a simple sine wave
    t = np.linspace(0, duration_sec, num_samples_in, dtype=np.float32)
    audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    pcm_16k = PcmData(
        samples=audio, sample_rate=sample_rate_in, format="s16", channels=1
    )

    # Resample to 48kHz
    pcm_48k = pcm_16k.resample(sample_rate_out, target_channels=1)

    # Check that sample count increased by 3x (48k/16k = 3)
    expected_samples = num_samples_in * 3
    actual_samples = (
        len(pcm_48k.samples) if pcm_48k.samples.ndim == 1 else pcm_48k.samples.shape[-1]
    )

    print(f"\n16kHz samples: {num_samples_in}")
    print(f"48kHz samples: {actual_samples} (expected ~{expected_samples})")
    print(f"48kHz shape: {pcm_48k.samples.shape}")
    print(f"48kHz duration: {pcm_48k.duration}s (expected ~1.0s)")

    # Allow some tolerance for resampler edge effects
    assert abs(actual_samples - expected_samples) < 100, (
        f"Expected ~{expected_samples} samples at 48kHz, got {actual_samples} (BUG: quality will be bad!)"
    )

    # Duration should remain the same
    assert abs(pcm_48k.duration - duration_sec) < 0.01, (
        f"Duration should remain ~{duration_sec}s, got {pcm_48k.duration}s"
    )


def test_bug_resample_16khz_to_48khz_stereo_combined():
    """
    BUG REPRODUCTION: The worst case - 16kHz mono to 48kHz stereo.
    This combines both bugs: resampling quality AND duration preservation.
    """
    # Create 1 second of mono audio at 16kHz
    sample_rate_in = 16000
    sample_rate_out = 48000
    duration_sec = 1.0
    num_samples_in = int(sample_rate_in * duration_sec)

    # Generate a simple sine wave
    t = np.linspace(0, duration_sec, num_samples_in, dtype=np.float32)
    audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    pcm_16k = PcmData(
        samples=audio, sample_rate=sample_rate_in, format="s16", channels=1
    )

    # Resample to 48kHz stereo (the problematic case!)
    pcm_48k_stereo = pcm_16k.resample(sample_rate_out, target_channels=2)

    print(f"\n16kHz mono shape: {pcm_16k.samples.shape}")
    print(f"48kHz stereo shape: {pcm_48k_stereo.samples.shape}")
    print(f"48kHz stereo duration: {pcm_48k_stereo.duration}s (expected ~1.0s)")

    # Check shape is correct (channels, samples)
    assert pcm_48k_stereo.samples.ndim == 2, "Should be 2D array"
    assert pcm_48k_stereo.samples.shape[0] == 2, (
        f"First dimension should be channels (2), got shape {pcm_48k_stereo.samples.shape}"
    )

    # Check that sample count increased by 3x (48k/16k = 3)
    expected_samples = num_samples_in * 3
    actual_samples = pcm_48k_stereo.samples.shape[1]

    print(f"Expected ~{expected_samples} samples, got {actual_samples}")

    # Allow some tolerance for resampler edge effects
    assert abs(actual_samples - expected_samples) < 100, (
        f"Expected ~{expected_samples} samples at 48kHz, got {actual_samples}"
    )

    # Duration should remain the same (THIS IS THE CRITICAL BUG)
    assert abs(pcm_48k_stereo.duration - duration_sec) < 0.01, (
        f"Duration should remain ~{duration_sec}s, got {pcm_48k_stereo.duration}s (BUG: causes slow playback!)"
    )


def test_bug_duration_with_different_array_shapes():
    """
    BUG REPRODUCTION: Duration calculation should work with any array shape.
    The bug is that shape[-1] is used, which gives wrong results for (samples, channels) arrays.
    """
    sample_rate = 16000
    num_samples = 16000  # 1 second
    expected_duration = 1.0

    # Test 1: 1D array (mono) - should work
    samples_1d = np.zeros(num_samples, dtype=np.int16)
    pcm_1d = PcmData(
        samples=samples_1d, sample_rate=sample_rate, format="s16", channels=1
    )
    print(f"\n1D mono: shape={pcm_1d.samples.shape}, duration={pcm_1d.duration}s")
    assert abs(pcm_1d.duration - expected_duration) < 0.01

    # Test 2: 2D array (channels, samples) - CORRECT format, should work
    samples_2d_correct = np.zeros((2, num_samples), dtype=np.int16)
    pcm_2d_correct = PcmData(
        samples=samples_2d_correct, sample_rate=sample_rate, format="s16", channels=2
    )
    print(
        f"2D (channels, samples): shape={pcm_2d_correct.samples.shape}, duration={pcm_2d_correct.duration}s"
    )
    assert abs(pcm_2d_correct.duration - expected_duration) < 0.01

    # Test 3: 2D array (samples, channels) - WRONG format but might happen from PyAV
    # This is where the bug manifests!
    samples_2d_wrong = np.zeros((num_samples, 2), dtype=np.int16)
    pcm_2d_wrong = PcmData(
        samples=samples_2d_wrong, sample_rate=sample_rate, format="s16", channels=2
    )
    wrong_duration = pcm_2d_wrong.duration
    print(
        f"2D (samples, channels): shape={pcm_2d_wrong.samples.shape}, duration={wrong_duration}s"
    )

    # With current buggy code using shape[-1], this will give duration = 2/16000 = 0.000125s
    # But we want it to be 1.0s
    # This assertion will FAIL with the bug
    assert abs(wrong_duration - expected_duration) < 0.01, (
        f"Duration with (samples, channels) shape is WRONG: {wrong_duration}s (expected {expected_duration}s)"
    )


def test_to_float32_converts_int16_and_preserves_metadata():
    # Prepare a small mono int16 buffer
    i16 = np.array([-32768, -16384, 0, 16384, 32767], dtype=np.int16)
    sr = 16000
    pcm = PcmData(samples=i16, sample_rate=sr, format="s16", channels=1)

    f32 = pcm.to_float32()

    # Check metadata preserved
    assert f32.sample_rate == sr
    assert f32.channels == 1
    assert f32.format == "f32"

    # Check dtype and shape preserved (mono stays 1D)
    assert isinstance(f32.samples, np.ndarray)
    assert f32.samples.dtype == np.float32
    assert f32.samples.ndim == 1

    # Check value scaling to [-1, 1]
    expected = np.array([-1.0, -0.5, 0.0, 0.5, 32767 / 32768.0], dtype=np.float32)
    assert np.allclose(f32.samples, expected, atol=1e-6)

    # Idempotency when already float32
    f32_2 = f32.to_float32()
    assert f32_2.samples.dtype == np.float32
    assert np.allclose(f32_2.samples, f32.samples, atol=1e-7)


def test_append_mono_s16_concatenates_and_preserves_format():
    sr = 16000
    a = np.array([1, 2, 3, 4], dtype=np.int16)
    b = np.array([5, 6], dtype=np.int16)

    pcm_a = PcmData(samples=a, sample_rate=sr, format="s16", channels=1)
    pcm_b = PcmData(samples=b, sample_rate=sr, format="s16", channels=1)

    out = pcm_a.append(pcm_b)

    assert out.format == "s16"
    assert out.channels == 1
    assert isinstance(out.samples, np.ndarray)
    assert out.samples.dtype == np.int16
    assert out.samples.ndim == 1
    assert out.sample_rate == sr
    assert np.array_equal(out.samples, np.array([1, 2, 3, 4, 5, 6], dtype=np.int16))


def test_append_resamples_and_converts_to_match_target_format():
    # Target is float32 stereo 48kHz
    base = np.array([[0.0, 0.1, -0.1], [0.0, 0.1, -0.1]], dtype=np.float32)
    pcm_target = PcmData(samples=base, sample_rate=48000, format="f32", channels=2)

    # Other is s16 mono 16kHz
    other_raw = np.array([1000, -1000, 1000, -1000, 1000, -1000], dtype=np.int16)
    pcm_other = PcmData(samples=other_raw, sample_rate=16000, format="s16", channels=1)

    # Pre-compute expected resampled length by using the same resample pipeline
    other_resampled = pcm_other.resample(48000, target_channels=2).to_float32()
    if other_resampled.samples.ndim == 2:
        expected_added = other_resampled.samples.shape[1]
    else:
        expected_added = other_resampled.samples.shape[0]

    out = pcm_target.append(pcm_other)

    # Check format/channels preserved and dtype matches
    assert out.format == "f32"
    assert out.channels == 2
    assert isinstance(out.samples, np.ndarray) and out.samples.dtype == np.float32
    assert out.samples.shape[0] == 2

    # First part must equal the original base (append should not alter original)
    assert np.allclose(out.samples[:, : base.shape[1]], base)

    # Total length should be base + resampled other
    assert out.samples.shape[1] == base.shape[1] + expected_added


def test_append_empty_buffer_float32_adjusts_other_and_keeps_meta():
    # Create an empty buffer specifying desired output meta using alternate format name
    buffer = PcmData(format="float32", sample_rate=16000, channels=1)

    # Other is int16 stereo at 48kHz, small ramp
    other = np.array(
        [[1000, -1000, 500, -500], [-1000, 1000, -500, 500]], dtype=np.int16
    )
    pcm_other = PcmData(samples=other, sample_rate=48000, format="s16", channels=2)

    # Expected result if we first resample/downmix then convert to float32
    expected_pcm = pcm_other.resample(16000, target_channels=1).to_float32()

    # Append to the empty buffer
    out = buffer.append(pcm_other)

    # Metadata should be preserved from buffer
    assert out.format in ("f32", "float32")
    assert out.sample_rate == 16000
    assert out.channels == 1

    # Data should match expected (mono float32)
    assert isinstance(out.samples, np.ndarray)
    assert out.samples.dtype == np.float32
    assert out.samples.ndim == 1
    # Normalize expected to 1D if needed
    if isinstance(expected_pcm.samples, np.ndarray) and expected_pcm.samples.ndim == 2:
        expected_samples = expected_pcm.samples.reshape(-1)
    else:
        expected_samples = expected_pcm.samples
    assert np.allclose(out.samples[-expected_samples.shape[0] :], expected_samples)


def test_copy_creates_independent_copy():
    """Test that copy() creates a deep copy that can be modified independently."""
    sr = 16000
    original_samples = np.array([1, 2, 3, 4], dtype=np.int16)
    pcm_original = PcmData(
        sample_rate=sr, format="s16", samples=original_samples.copy(), channels=1
    )

    # Create a copy
    pcm_copy = pcm_original.copy()

    # Verify initial state - both should have same values but different objects
    assert pcm_copy.sample_rate == pcm_original.sample_rate
    assert pcm_copy.format == pcm_original.format
    assert pcm_copy.channels == pcm_original.channels
    assert np.array_equal(pcm_copy.samples, pcm_original.samples)
    assert pcm_copy.samples is not pcm_original.samples  # Different array objects

    # Modify the copy
    pcm_copy.samples[0] = 999

    # Original should be unchanged
    assert pcm_original.samples[0] == 1
    assert pcm_copy.samples[0] == 999


def test_append_modifies_in_place():
    """Test that append() modifies the original PcmData in-place and returns self."""
    sr = 16000
    a = np.array([1, 2, 3, 4], dtype=np.int16)
    b = np.array([5, 6], dtype=np.int16)

    pcm_a = PcmData(sample_rate=sr, format="s16", samples=a, channels=1)
    pcm_b = PcmData(sample_rate=sr, format="s16", samples=b, channels=1)

    # Store the id to verify it's the same object
    original_id = id(pcm_a)

    # Append and check that it returns self
    result = pcm_a.append(pcm_b)

    assert id(result) == original_id  # Same object
    assert result is pcm_a  # Identity check

    # Check that pcm_a was modified in-place
    expected = np.array([1, 2, 3, 4, 5, 6], dtype=np.int16)
    assert np.array_equal(pcm_a.samples, expected)
    assert np.array_equal(result.samples, expected)


def test_copy_append_does_not_modify_original():
    """Test the critical use case: pcm.copy().append(other) doesn't modify pcm."""
    sr = 16000
    a = np.array([1, 2, 3, 4], dtype=np.int16)
    b = np.array([5, 6], dtype=np.int16)

    pcm_a = PcmData(sample_rate=sr, format="s16", samples=a, channels=1)
    pcm_b = PcmData(sample_rate=sr, format="s16", samples=b, channels=1)

    # Create a copy and append to it
    pcm_copy = pcm_a.copy().append(pcm_b)

    # Original should be unchanged
    assert np.array_equal(pcm_a.samples, np.array([1, 2, 3, 4], dtype=np.int16))

    # Copy should have the appended data
    assert np.array_equal(
        pcm_copy.samples, np.array([1, 2, 3, 4, 5, 6], dtype=np.int16)
    )

    # They should be different objects
    assert pcm_a is not pcm_copy
    assert pcm_a.samples is not pcm_copy.samples


def test_copy_preserves_all_metadata():
    """Test that copy() preserves all metadata including timestamps."""
    sr = 16000
    samples = np.array([1, 2, 3], dtype=np.int16)
    pcm_original = PcmData(
        sample_rate=sr,
        format="s16",
        samples=samples,
        channels=2,
        pts=12345,
        dts=67890,
        time_base=0.00001,
    )

    pcm_copy = pcm_original.copy()

    # Verify all metadata is copied
    assert pcm_copy.sample_rate == pcm_original.sample_rate
    assert pcm_copy.format == pcm_original.format
    assert pcm_copy.channels == pcm_original.channels
    assert pcm_copy.pts == pcm_original.pts
    assert pcm_copy.dts == pcm_original.dts
    assert pcm_copy.time_base == pcm_original.time_base
    assert np.array_equal(pcm_copy.samples, pcm_original.samples)


def test_append_chaining_with_copy():
    """Test that append() can be chained and works correctly with copy()."""
    sr = 16000
    a = np.array([1, 2], dtype=np.int16)
    b = np.array([3, 4], dtype=np.int16)
    c = np.array([5, 6], dtype=np.int16)

    pcm_a = PcmData(sample_rate=sr, format="s16", samples=a, channels=1)
    pcm_b = PcmData(sample_rate=sr, format="s16", samples=b, channels=1)
    pcm_c = PcmData(sample_rate=sr, format="s16", samples=c, channels=1)

    # Chain append on a copy
    result = pcm_a.copy().append(pcm_b).append(pcm_c)

    # Original should be unchanged
    assert np.array_equal(pcm_a.samples, np.array([1, 2], dtype=np.int16))

    # Result should have all samples
    assert np.array_equal(result.samples, np.array([1, 2, 3, 4, 5, 6], dtype=np.int16))


# ===== Tests for clear() method (like list.clear()) =====


def test_clear_wipes_samples_like_list_clear():
    """Test that clear() works like list.clear() - removes all items, returns None."""
    sr = 16000
    samples = np.array([1, 2, 3, 4, 5], dtype=np.int16)
    pcm = PcmData(sample_rate=sr, format="s16", samples=samples, channels=1)

    # clear() should return None, like list.clear()
    result = pcm.clear()
    assert result is None

    # Samples should be empty
    assert isinstance(pcm.samples, np.ndarray)
    assert len(pcm.samples) == 0
    assert pcm.samples.dtype == np.int16


def test_clear_preserves_metadata():
    """Test that clear() preserves all metadata like list.clear() preserves list identity."""
    sr = 16000
    samples = np.array([1, 2, 3, 4, 5], dtype=np.int16)
    pcm = PcmData(
        sample_rate=sr,
        format="s16",
        samples=samples,
        channels=2,
        pts=1000,
        dts=2000,
        time_base=0.001,
    )

    # Store original metadata and id
    original_id = id(pcm)
    original_sr = pcm.sample_rate
    original_format = pcm.format
    original_channels = pcm.channels
    original_pts = pcm.pts
    original_dts = pcm.dts
    original_time_base = pcm.time_base

    # Clear
    pcm.clear()

    # Object identity preserved (like list.clear())
    assert id(pcm) == original_id

    # Samples should be empty
    assert len(pcm.samples) == 0

    # Metadata should be preserved
    assert pcm.sample_rate == original_sr
    assert pcm.format == original_format
    assert pcm.channels == original_channels
    assert pcm.pts == original_pts
    assert pcm.dts == original_dts
    assert pcm.time_base == original_time_base


def test_clear_f32_uses_correct_dtype():
    """Test that clear() uses float32 dtype for f32 format."""
    sr = 16000
    samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    pcm = PcmData(sample_rate=sr, format="f32", samples=samples, channels=1)

    pcm.clear()

    # Samples should be empty with float32 dtype
    assert isinstance(pcm.samples, np.ndarray)
    assert len(pcm.samples) == 0
    assert pcm.samples.dtype == np.float32


def test_clear_after_append():
    """Test that clear() can be used to clear accumulated samples."""
    sr = 16000
    a = np.array([1, 2, 3], dtype=np.int16)
    b = np.array([4, 5, 6], dtype=np.int16)

    pcm_a = PcmData(sample_rate=sr, format="s16", samples=a, channels=1)
    pcm_b = PcmData(sample_rate=sr, format="s16", samples=b, channels=1)

    # Append then clear
    pcm_a.append(pcm_b)
    assert len(pcm_a.samples) == 6

    pcm_a.clear()
    assert len(pcm_a.samples) == 0

    # Can append again after clear
    pcm_a.append(pcm_b)
    assert np.array_equal(pcm_a.samples, np.array([4, 5, 6], dtype=np.int16))


def test_clear_returns_none():
    """Test that clear() returns None like list.clear()."""
    sr = 16000
    samples = np.array([1, 2, 3], dtype=np.int16)

    pcm = PcmData(sample_rate=sr, format="s16", samples=samples, channels=1)
    result = pcm.clear()

    # Should return None like list.clear()
    assert result is None

    # Samples should be empty
    assert len(pcm.samples) == 0


def test_clear_multiple_times():
    """Test that clear() can be called multiple times safely."""
    sr = 16000
    samples = np.array([1, 2, 3], dtype=np.int16)
    pcm = PcmData(sample_rate=sr, format="s16", samples=samples, channels=1)

    # Clear multiple times
    pcm.clear()
    assert len(pcm.samples) == 0

    pcm.clear()  # Should work on empty PcmData
    assert len(pcm.samples) == 0

    pcm.clear()  # Should work again
    assert len(pcm.samples) == 0

    # Metadata should still be intact
    assert pcm.sample_rate == sr
    assert pcm.format == "s16"


def test_resample_float32_preserves_float32_dtype():
    """
    REGRESSION TEST: Float32 audio must stay as float32 after resampling.

    Previously, resample() would silently downgrade float32 to int16, then mark
    it as f32 format, completely mangling high-dynamic-range audio.
    """
    # Create float32 audio with high dynamic range
    sample_rate_in = 16000
    sample_rate_out = 48000
    num_samples = 1000

    # Use values that would be truncated if converted to int16
    # E.g., 0.5 becomes 0 when converted to int16 directly
    samples_f32 = np.linspace(-1.0, 1.0, num_samples, dtype=np.float32)

    pcm_16k = PcmData(
        sample_rate=sample_rate_in,
        format="f32",
        samples=samples_f32,
        channels=1,
    )

    # Resample to 48kHz
    pcm_48k = pcm_16k.resample(sample_rate_out)

    # CRITICAL: Format must still be f32
    assert pcm_48k.format == "f32", f"Format should be 'f32', got '{pcm_48k.format}'"

    # CRITICAL: Samples must be float32, not int16
    assert pcm_48k.samples.dtype == np.float32, (
        f"Samples should be float32, got {pcm_48k.samples.dtype}. "
        f"This means float32 audio was silently downgraded to int16!"
    )

    # Verify values are still in float range, not truncated to int16 range
    assert np.any(np.abs(pcm_48k.samples) < 1.0), (
        "No fractional values found - data may have been truncated to integers"
    )


def test_resample_float32_to_stereo_preserves_float32():
    """Test that float32 stays float32 when resampling AND converting to stereo."""
    sample_rate_in = 16000
    sample_rate_out = 48000

    # Create float32 mono audio
    samples_f32 = np.array([0.1, 0.2, 0.3, 0.4, 0.5] * 100, dtype=np.float32)

    pcm_16k_mono = PcmData(
        sample_rate=sample_rate_in,
        format="f32",
        samples=samples_f32,
        channels=1,
    )

    # Resample to 48kHz stereo
    pcm_48k_stereo = pcm_16k_mono.resample(sample_rate_out, target_channels=2)

    # Format must be f32
    assert pcm_48k_stereo.format == "f32"

    # Dtype must be float32
    assert pcm_48k_stereo.samples.dtype == np.float32, (
        f"Expected float32, got {pcm_48k_stereo.samples.dtype}"
    )

    # Should be stereo
    assert pcm_48k_stereo.channels == 2
    assert pcm_48k_stereo.samples.ndim == 2
    assert pcm_48k_stereo.samples.shape[0] == 2


def test_resample_int16_stays_int16():
    """Verify that int16 audio correctly stays int16 (baseline test)."""
    sample_rate_in = 16000
    sample_rate_out = 48000

    # Create int16 audio
    samples_i16 = np.array([100, 200, 300, 400, 500] * 100, dtype=np.int16)

    pcm_16k = PcmData(
        sample_rate=sample_rate_in,
        format="s16",
        samples=samples_i16,
        channels=1,
    )

    # Resample to 48kHz
    pcm_48k = pcm_16k.resample(sample_rate_out)

    # Format must be s16
    assert pcm_48k.format == "s16"

    assert pcm_48k.samples.dtype == np.int16, (
        f"Expected int16, got {pcm_48k.samples.dtype}"
    )


# ===== Tests for constructor default samples dtype =====


def test_constructor_default_samples_respects_f32_format():
    """
    REGRESSION TEST: Constructor must create float32 empty array for f32 format.

    Previously, constructor always created int16 empty array regardless of format,
    causing dtype mismatch when format="f32" but samples.dtype=int16.
    """
    # Create PcmData with f32 format but no samples - should default to float32 empty array
    pcm = PcmData(sample_rate=16000, format="f32", channels=1)

    # Verify format is f32
    assert pcm.format == "f32"

    # CRITICAL: Samples must be float32, not int16
    assert pcm.samples.dtype == np.float32, (
        f"Expected float32 empty array for f32 format, got {pcm.samples.dtype}"
    )

    # Should be empty
    assert len(pcm.samples) == 0


def test_constructor_default_samples_respects_s16_format():
    """Verify constructor creates int16 empty array for s16 format (baseline)."""
    # Create PcmData with s16 format but no samples - should default to int16 empty array
    pcm = PcmData(sample_rate=16000, format="s16", channels=1)

    # Verify format is s16
    assert pcm.format == "s16"

    # Samples must be int16
    assert pcm.samples.dtype == np.int16, (
        f"Expected int16 empty array for s16 format, got {pcm.samples.dtype}"
    )

    # Should be empty
    assert len(pcm.samples) == 0


def test_constructor_default_samples_respects_enum_f32():
    """Verify constructor works with AudioFormat enum for f32."""
    from getstream.video.rtc.track_util import AudioFormat

    # Create PcmData with AudioFormat.F32 enum
    pcm = PcmData(sample_rate=16000, format=AudioFormat.F32, channels=1)

    # Verify format
    assert pcm.format == AudioFormat.F32

    # CRITICAL: Samples must be float32
    assert pcm.samples.dtype == np.float32, (
        f"Expected float32 empty array for AudioFormat.F32, got {pcm.samples.dtype}"
    )

    # Should be empty
    assert len(pcm.samples) == 0


def test_constructor_default_samples_respects_enum_s16():
    """Verify constructor works with AudioFormat enum for s16."""
    from getstream.video.rtc.track_util import AudioFormat

    # Create PcmData with AudioFormat.S16 enum
    pcm = PcmData(sample_rate=16000, format=AudioFormat.S16, channels=1)

    # Verify format
    assert pcm.format == AudioFormat.S16

    # Samples must be int16
    assert pcm.samples.dtype == np.int16, (
        f"Expected int16 empty array for AudioFormat.S16, got {pcm.samples.dtype}"
    )

    # Should be empty
    assert len(pcm.samples) == 0


def test_constructor_default_samples_handles_float32_string():
    """Verify constructor handles 'float32' format string."""
    # Create PcmData with 'float32' format string
    pcm = PcmData(sample_rate=16000, format="float32", channels=1)

    # Verify format
    assert pcm.format == "float32"

    # Samples must be float32
    assert pcm.samples.dtype == np.float32, (
        f"Expected float32 empty array for 'float32' format, got {pcm.samples.dtype}"
    )

    # Should be empty
    assert len(pcm.samples) == 0


# ===== Tests for strict dtype validation =====


def test_constructor_raises_on_int16_with_f32_format():
    """Test that constructor raises TypeError when passing int16 samples with f32 format."""
    samples = np.array([1, 2, 3], dtype=np.int16)

    with pytest.raises(TypeError) as exc_info:
        PcmData(sample_rate=16000, format="f32", samples=samples, channels=1)

    # Verify error message is helpful
    error_msg = str(exc_info.value)
    assert "Dtype mismatch" in error_msg
    assert "format='f32'" in error_msg
    assert "float32" in error_msg
    assert "int16" in error_msg
    assert "to_float32()" in error_msg or "from_data()" in error_msg


def test_constructor_raises_on_float32_with_s16_format():
    """Test that constructor raises TypeError when passing float32 samples with s16 format."""
    samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    with pytest.raises(TypeError) as exc_info:
        PcmData(sample_rate=16000, format="s16", samples=samples, channels=1)

    # Verify error message is helpful
    error_msg = str(exc_info.value)
    assert "Dtype mismatch" in error_msg
    assert "format='s16'" in error_msg
    assert "int16" in error_msg
    assert "float32" in error_msg


def test_constructor_raises_on_int16_with_enum_f32_format():
    """Test that constructor raises TypeError with AudioFormat.F32 enum."""
    from getstream.video.rtc.track_util import AudioFormat

    samples = np.array([1, 2, 3], dtype=np.int16)

    with pytest.raises(TypeError) as exc_info:
        PcmData(sample_rate=16000, format=AudioFormat.F32, samples=samples, channels=1)

    error_msg = str(exc_info.value)
    assert "Dtype mismatch" in error_msg
    assert "float32" in error_msg


def test_constructor_raises_on_float32_with_enum_s16_format():
    """Test that constructor raises TypeError with AudioFormat.S16 enum."""
    from getstream.video.rtc.track_util import AudioFormat

    samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    with pytest.raises(TypeError) as exc_info:
        PcmData(sample_rate=16000, format=AudioFormat.S16, samples=samples, channels=1)

    error_msg = str(exc_info.value)
    assert "Dtype mismatch" in error_msg
    assert "int16" in error_msg


def test_constructor_accepts_matching_int16_with_s16():
    """Verify constructor accepts int16 samples with s16 format (should work)."""
    samples = np.array([1, 2, 3], dtype=np.int16)
    pcm = PcmData(sample_rate=16000, format="s16", samples=samples, channels=1)

    assert pcm.format == "s16"
    assert pcm.samples.dtype == np.int16
    assert np.array_equal(pcm.samples, samples)


def test_constructor_accepts_matching_float32_with_f32():
    """Verify constructor accepts float32 samples with f32 format (should work)."""
    samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    pcm = PcmData(sample_rate=16000, format="f32", samples=samples, channels=1)

    assert pcm.format == "f32"
    assert pcm.samples.dtype == np.float32
    assert np.array_equal(pcm.samples, samples)


def test_from_data_handles_conversion_automatically():
    """Verify from_data() still handles automatic conversion (doesn't go through strict validation the same way)."""
    # from_data should handle conversion internally
    samples_int16 = np.array([1, 2, 3], dtype=np.int16)

    # This should work because from_data converts internally before calling __init__
    pcm = PcmData.from_data(samples_int16, sample_rate=16000, format="s16", channels=1)

    assert pcm.format == "s16"
    assert pcm.samples.dtype == np.int16


def test_direct_float32_to_int16_conversion_needs_clipping():
    """
    Direct test showing that float32→int16 conversion needs clipping and scaling.

    This demonstrates the bug: directly casting float32 to int16 produces wrong values.
    """
    # Test values with typical audio scenarios
    test_values_f32 = np.array([0.5, 1.0, 2.0, -1.5, -1.0, 0.0], dtype=np.float32)

    # What happens with direct cast (THE BUG)?
    buggy_conversion = test_values_f32.astype(np.int16)

    # This produces: [0, 1, 2, -1, -1, 0] - completely wrong!
    # 0.5 becomes 0 (should be ~16383)
    # 2.0 becomes 2 (should be 32767 after clipping)
    assert buggy_conversion[0] == 0  # 0.5 wrongly becomes 0
    assert buggy_conversion[2] == 2  # 2.0 wrongly becomes 2

    # Correct conversion with clipping and scaling
    max_int16 = np.iinfo(np.int16).max  # 32767
    correct_conversion = np.clip(test_values_f32, -1.0, 1.0) * max_int16
    correct_conversion = np.round(correct_conversion).astype(np.int16)

    # Should be: [16384, 32767, 32767, -32767, -32767, 0]
    # Note: 0.5 * 32767 = 16383.5, rounds to 16384
    assert correct_conversion[0] == 16384  # 0.5 * 32767, rounded
    assert correct_conversion[1] == 32767  # 1.0 * 32767
    assert correct_conversion[2] == 32767  # 2.0 clipped to 1.0, then * 32767
    assert correct_conversion[3] == -32767  # -1.5 clipped to -1.0, then * 32767
    assert correct_conversion[4] == -32767  # -1.0 * 32767
    assert correct_conversion[5] == 0  # 0.0 * 32767


def test_resample_with_extreme_values_should_clip():
    """
    Test that resample() properly clips extreme float values when converting to int16.

    Scenario: PyAV might return float32 values outside [-1.0, 1.0] after resampling.
    When converting back to int16, these must be clipped and scaled properly.
    """
    # Create int16 audio with values that when converted to float32 and back
    # might go through the problematic conversion path
    sample_rate_in = 16000
    sample_rate_out = 48000

    # Create int16 samples near the limits
    samples_i16 = np.array([16383, 32767, -16383, -32767, 0], dtype=np.int16)

    pcm_16k = PcmData(
        sample_rate=sample_rate_in,
        format="s16",
        samples=samples_i16,
        channels=1,
    )

    # Resample - this goes through PyAV which may return float32
    pcm_48k = pcm_16k.resample(sample_rate_out)

    # Result should still be int16 with valid range
    assert pcm_48k.format == "s16"
    assert pcm_48k.samples.dtype == np.int16

    # All values should be in valid int16 range
    assert np.all(pcm_48k.samples >= -32768)
    assert np.all(pcm_48k.samples <= 32767)

    # Values should not be close to zero (which would indicate incorrect scaling)
    # After resampling, we should have more samples but similar magnitudes
    max_val = np.max(np.abs(pcm_48k.samples))
    assert max_val > 10000, (
        f"Resampled values seem too small: max={max_val}, might indicate scaling bug"
    )
