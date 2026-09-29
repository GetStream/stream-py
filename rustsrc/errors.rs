use pyo3::PyErr;
use pyo3::create_exception;
use pyo3::exceptions::PyException;

create_exception!(_native, Error, PyException);
create_exception!(_native, RtcError, Error);

pub fn sdk_error(err: getstream::Error) -> PyErr {
    Error::new_err(err.to_string())
}

pub fn rtc_error(err: getstream::rtc::RtcError) -> PyErr {
    RtcError::new_err(err.to_string())
}
