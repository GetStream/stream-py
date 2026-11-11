use pyo3::IntoPyObjectExt;
use pyo3::prelude::*;

/// Python `repr()` of `value`, so `__repr__` shows field values as Python
/// shows them (quoted strings, `TrackType.AUDIO`, nested reprs).
pub fn repr<'py, T: IntoPyObject<'py>>(py: Python<'py>, value: T) -> PyResult<String> {
    Ok(value.into_bound_py_any(py)?.repr()?.to_string())
}
