use getstream::rtc::proto::models;
use prost_types::value::Kind;
use prost_types::{Struct, Timestamp, Value};
use pyo3::IntoPyObjectExt;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::repr::repr;

#[pyclass(
    frozen,
    module = "getstream._rust.bindings",
    eq,
    eq_int,
    from_py_object,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum TrackType {
    Unspecified,
    Audio,
    Video,
    ScreenShare,
    ScreenShareAudio,
}

impl From<models::TrackType> for TrackType {
    fn from(track_type: models::TrackType) -> Self {
        match track_type {
            models::TrackType::Unspecified => Self::Unspecified,
            models::TrackType::Audio => Self::Audio,
            models::TrackType::Video => Self::Video,
            models::TrackType::ScreenShare => Self::ScreenShare,
            models::TrackType::ScreenShareAudio => Self::ScreenShareAudio,
        }
    }
}

impl From<TrackType> for models::TrackType {
    fn from(track_type: TrackType) -> Self {
        match track_type {
            TrackType::Unspecified => Self::Unspecified,
            TrackType::Audio => Self::Audio,
            TrackType::Video => Self::Video,
            TrackType::ScreenShare => Self::ScreenShare,
            TrackType::ScreenShareAudio => Self::ScreenShareAudio,
        }
    }
}

impl TrackType {
    pub fn from_i32(value: i32) -> Self {
        models::TrackType::try_from(value).map_or(Self::Unspecified, Self::from)
    }
}

/// The fields of the SFU `Participant` message, except `track_lookup_prefix`.
/// Protobuf enum fields keep their `int` values.
#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct RemoteParticipant {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    image: String,
    #[pyo3(get)]
    roles: Vec<String>,
    #[pyo3(get)]
    published_tracks: Vec<TrackType>,
    #[pyo3(get)]
    connection_quality: i32,
    #[pyo3(get)]
    is_speaking: bool,
    #[pyo3(get)]
    is_dominant_speaker: bool,
    #[pyo3(get)]
    audio_level: f32,
    #[pyo3(get)]
    source: i32,
    /// Unix time in seconds, or `None` if the SFU did not send it.
    #[pyo3(get)]
    joined_at: Option<f64>,
    custom: Option<Struct>,
}

#[pymethods]
impl RemoteParticipant {
    /// The custom data as a `dict`; empty if the SFU did not send it.
    #[getter]
    fn custom<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        match &self.custom {
            Some(custom) => struct_to_dict(py, custom),
            None => Ok(PyDict::new(py)),
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "RemoteParticipant(user_id={}, session_id={}, published_tracks={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            repr(py, self.published_tracks.clone())?,
        ))
    }
}

impl From<getstream::rtc::RemoteParticipant> for RemoteParticipant {
    fn from(participant: getstream::rtc::RemoteParticipant) -> Self {
        Self {
            user_id: participant.user_id,
            session_id: participant.session_id,
            name: participant.name,
            image: participant.image,
            roles: participant.roles,
            published_tracks: participant
                .published_tracks
                .into_iter()
                .map(TrackType::from)
                .collect(),
            connection_quality: participant.connection_quality as i32,
            is_speaking: participant.is_speaking,
            is_dominant_speaker: participant.is_dominant_speaker,
            audio_level: participant.audio_level,
            source: participant.source as i32,
            joined_at: participant.joined_at.map(unix_seconds),
            custom: participant.custom,
        }
    }
}

impl From<models::Participant> for RemoteParticipant {
    fn from(participant: models::Participant) -> Self {
        Self {
            user_id: participant.user_id,
            session_id: participant.session_id,
            name: participant.name,
            image: participant.image,
            roles: participant.roles,
            published_tracks: participant
                .published_tracks
                .into_iter()
                .map(TrackType::from_i32)
                .collect(),
            connection_quality: participant.connection_quality,
            is_speaking: participant.is_speaking,
            is_dominant_speaker: participant.is_dominant_speaker,
            audio_level: participant.audio_level,
            source: participant.source,
            joined_at: participant.joined_at.map(unix_seconds),
            custom: participant.custom,
        }
    }
}

fn unix_seconds(timestamp: Timestamp) -> f64 {
    timestamp.seconds as f64 + f64::from(timestamp.nanos) / 1e9
}

/// The same `dict` as `MessageToDict` of the protobuf `Struct`: numbers are
/// `float`.
fn struct_to_dict<'py>(py: Python<'py>, value: &Struct) -> PyResult<Bound<'py, PyDict>> {
    let dict = PyDict::new(py);
    for (key, field) in &value.fields {
        dict.set_item(key, value_to_py(py, field)?)?;
    }
    Ok(dict)
}

fn value_to_py<'py>(py: Python<'py>, value: &Value) -> PyResult<Bound<'py, PyAny>> {
    Ok(match &value.kind {
        None | Some(Kind::NullValue(_)) => py.None().into_bound(py),
        Some(Kind::NumberValue(number)) => number.into_bound_py_any(py)?,
        Some(Kind::StringValue(string)) => string.into_bound_py_any(py)?,
        Some(Kind::BoolValue(boolean)) => boolean.into_bound_py_any(py)?,
        Some(Kind::StructValue(value)) => struct_to_dict(py, value)?.into_any(),
        Some(Kind::ListValue(list)) => PyList::new(
            py,
            list.values
                .iter()
                .map(|value| value_to_py(py, value))
                .collect::<PyResult<Vec<_>>>()?,
        )?
        .into_any(),
    })
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct CallStateSnapshot {
    #[pyo3(get)]
    participants: Vec<RemoteParticipant>,
    #[pyo3(get)]
    own_capabilities: Vec<String>,
}

#[pymethods]
impl CallStateSnapshot {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "CallStateSnapshot(participants={}, own_capabilities={})",
            repr(py, self.participants.clone())?,
            repr(py, &self.own_capabilities)?,
        ))
    }
}

impl From<getstream::rtc::CallStateSnapshot> for CallStateSnapshot {
    fn from(state: getstream::rtc::CallStateSnapshot) -> Self {
        Self {
            participants: state.participants.into_iter().map(Into::into).collect(),
            own_capabilities: state.own_capabilities,
        }
    }
}
