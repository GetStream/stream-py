use pyo3::PyErr;
use pyo3::import_exception;

import_exception!(getstream_rtc.errors, RustError);
import_exception!(getstream_rtc.errors, ConfigError);
import_exception!(getstream_rtc.errors, RtcError);
import_exception!(getstream_rtc.errors, ApiError);
import_exception!(getstream_rtc.errors, CoordinatorError);
import_exception!(getstream_rtc.errors, IllegalStateError);
import_exception!(getstream_rtc.errors, MediaError);
import_exception!(getstream_rtc.errors, PermissionDeniedError);
import_exception!(getstream_rtc.errors, PcmQueueOverflowError);

pub fn sdk_error(err: getstream::Error) -> PyErr {
    let message = err.to_string();
    match err {
        getstream::Error::Config(_) => ConfigError::new_err(message),
        _ => RustError::new_err(message),
    }
}

pub fn rtc_error(err: getstream::rtc::RtcError) -> PyErr {
    use getstream::rtc::RtcError as Sdk;
    let message = err.to_string();
    match err {
        Sdk::Api(api) => ApiError::new_err((
            message,
            api.code,
            api.status,
            api.message,
            api.unrecoverable,
        )),
        Sdk::Coordinator(_) => CoordinatorError::new_err(message),
        Sdk::IllegalState(_) => IllegalStateError::new_err(message),
        Sdk::Media(_) => MediaError::new_err(message),
        Sdk::PermissionDenied { capability } => {
            PermissionDeniedError::new_err((message, capability))
        }
        Sdk::PcmQueueOverflow {
            dropped_samples,
            capacity_samples,
        } => PcmQueueOverflowError::new_err((message, dropped_samples, capacity_samples)),
        _ => RtcError::new_err(message),
    }
}
