use getstream::rtc::proto::models;
use pyo3::prelude::*;

#[pyclass(
    frozen,
    eq,
    eq_int,
    skip_from_py_object,
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

impl TrackType {
    pub fn from_i32(value: i32) -> Self {
        models::TrackType::try_from(value).map_or(Self::Unspecified, Self::from)
    }
}

#[pyclass(frozen, skip_from_py_object)]
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
        }
    }
}

#[pyclass(frozen)]
pub struct CallStateSnapshot {
    #[pyo3(get)]
    participants: Vec<RemoteParticipant>,
    #[pyo3(get)]
    own_capabilities: Vec<String>,
}

impl From<getstream::rtc::CallStateSnapshot> for CallStateSnapshot {
    fn from(state: getstream::rtc::CallStateSnapshot) -> Self {
        Self {
            participants: state.participants.into_iter().map(Into::into).collect(),
            own_capabilities: state.own_capabilities,
        }
    }
}
