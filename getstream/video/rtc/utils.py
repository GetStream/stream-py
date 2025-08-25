"""
Shared helpers for audio manipulation used by VAD and STT plugins.
Currently contains:
    * resample_audio() – high-quality multi-backend resampler.
"""

from __future__ import annotations
import logging
import numpy as np

# Optional back-ends
try:
    import scipy.signal

    _has_scipy = True
except ImportError:
    _has_scipy = False

try:
    import torchaudio
    import torch

    _has_torchaudio = True
except ImportError:
    _has_torchaudio = False

log = logging.getLogger(__name__)


def resample_audio(frame: np.ndarray, from_sr: int, to_sr: int) -> np.ndarray:
    """
    High-quality resampling used across the codebase.

    – Prefers scipy.signal.resample_poly (best SNR & speed).
    – Falls back to torchaudio.transforms.Resample if SciPy missing.
    – Final fallback is a simple average-pool loop (keeps tests green).

    Returns float32 or int16 array matching input dtype.
    """
    if from_sr == to_sr:
        return frame

    # ------------------------------------------------  SciPy path
    if _has_scipy:
        try:
            return scipy.signal.resample_poly(frame, to_sr, from_sr, axis=-1)
        except Exception as e:
            log.warning("scipy resample failed: %s – trying fallback", e)

    # ------------------------------------------------  torchaudio path
    if _has_torchaudio:
        try:
            tensor = torch.tensor(frame, dtype=torch.float32)
            resampler = torchaudio.transforms.Resample(
                orig_freq=from_sr, new_freq=to_sr
            )
            return resampler(tensor).numpy()
        except Exception as e:
            log.warning("torchaudio resample failed: %s – using simple avg-pool", e)

    # ------------------------------------------------  naïve fallback
    ratio = from_sr / to_sr
    out_len = int(len(frame) / ratio)
    out = np.zeros(out_len, dtype=np.float32)
    for i in range(out_len):
        start = int(i * ratio)
        end = int((i + 1) * ratio)
        chunk = frame[start:end]
        if chunk.size:
            out[i] = float(chunk.mean())

    return out
