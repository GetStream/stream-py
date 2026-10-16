use std::sync::{Mutex, PoisonError};

use numpy::{PyReadonlyArray1, PyUntypedArrayMethods};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::errors::rtc_error;
use crate::tracks::PcmFrameData;

/// One stream of interleaved int16 PCM resampled to a fixed rate. The filter
/// state carries over between calls.
#[pyclass(frozen, module = "getstream_rtc")]
pub struct StreamResampler {
    inner: Mutex<getstream::rtc::StreamResampler>,
}

#[pymethods]
impl StreamResampler {
    #[new]
    fn new(sample_rate: u32, channels: u16) -> Self {
        Self {
            inner: Mutex::new(getstream::rtc::StreamResampler::new(sample_rate, channels)),
        }
    }

    /// Copies `samples` (interleaved int16) and resamples them.
    fn push(
        &self,
        py: Python<'_>,
        samples: PyReadonlyArray1<'_, i16>,
        sample_rate: u32,
        channels: u16,
    ) -> PyResult<PcmFrameData> {
        // numpy's `as_array` requires an aligned buffer.
        if !samples.is_aligned() {
            return Err(PyValueError::new_err(
                "samples must be an aligned int16 array",
            ));
        }
        let frame =
            getstream::rtc::PcmFrame::new(samples.as_array().to_vec(), sample_rate, channels);
        py.detach(|| {
            self.inner
                .lock()
                .unwrap_or_else(PoisonError::into_inner)
                .push(&frame)
        })
        .map(PcmFrameData)
        .map_err(rtc_error)
    }

    fn flush(&self, py: Python<'_>) -> PyResult<PcmFrameData> {
        py.detach(|| {
            self.inner
                .lock()
                .unwrap_or_else(PoisonError::into_inner)
                .flush()
        })
        .map(PcmFrameData)
        .map_err(rtc_error)
    }
}
