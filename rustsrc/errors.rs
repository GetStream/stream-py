use pyo3::PyErr;
use pyo3::import_exception;

import_exception!(getstream._rust.errors, RustError);
import_exception!(getstream._rust.errors, RtcError);

pub fn sdk_error(err: getstream::Error) -> PyErr {
    RustError::new_err(err.to_string())
}

pub fn rtc_error(err: getstream::rtc::RtcError) -> PyErr {
    RtcError::new_err(err.to_string())
}
