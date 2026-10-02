use std::sync::Arc;

use getstream::ClientConfig;
use getstream::rtc::proto::models;
use getstream::rtc::{JoinCallData, LocalTrack, RtcCall, RtcClient};
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use tokio::sync::{Mutex, watch};

use crate::call_end::{self, CallEnd};
use crate::errors::{ConfigError, rtc_error, sdk_error};
use crate::events::{EventStream, Source};
use crate::participants::{CallStateSnapshot, RemoteParticipant, TrackType};
use crate::subscriptions::SubscriptionConfig;
use crate::tracks::{LocalAudioTrack, LocalVideoTrack, TrackQueue, TrackStream};

enum Credentials {
    /// Mints a user token for each join.
    ApiSecret(getstream::Stream),
    /// Joins with the user token of one user.
    UserToken(RtcClient),
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct Client {
    inner: Credentials,
}

#[pymethods]
impl Client {
    #[new]
    #[pyo3(signature = (api_key, api_secret=None, *, token=None, base_url=None, ws_url=None, log_bodies=false, call_event_capacity=None))]
    fn new(
        api_key: String,
        api_secret: Option<String>,
        token: Option<String>,
        base_url: Option<String>,
        ws_url: Option<String>,
        log_bodies: bool,
        call_event_capacity: Option<usize>,
    ) -> PyResult<Self> {
        let mut config = ClientConfig::default();
        if let Some(base_url) = base_url {
            config.base_url = base_url;
        }
        if let Some(ws_url) = ws_url {
            config.coordinator_ws_url = ws_url;
        }
        if let Some(call_event_capacity) = call_event_capacity {
            config.call_event_capacity = call_event_capacity;
        }
        config.log_bodies = log_bodies;
        let inner = match (api_secret, token) {
            (Some(api_secret), None) => Credentials::ApiSecret(
                getstream::Stream::with_config(api_key, api_secret, config).map_err(sdk_error)?,
            ),
            (None, Some(token)) => Credentials::UserToken(
                RtcClient::with_config(api_key, token, config).map_err(sdk_error)?,
            ),
            _ => {
                return Err(ConfigError::new_err(
                    "pass exactly one of api_secret or token",
                ));
            }
        };
        Ok(Self { inner })
    }

    fn call(&self, call_type: String, call_id: String) -> Call {
        let cid = format!("{call_type}:{call_id}");
        let inner = match &self.inner {
            Credentials::ApiSecret(stream) => stream.video().call(call_type, call_id).rtc(),
            Credentials::UserToken(client) => client.call(call_type, call_id),
        };
        let end = call_end::watch_call_end(inner.client_events());
        let tracks = TrackQueue::register(&inner);
        Call {
            inner,
            cid,
            tracks,
            end,
            join_lock: Arc::default(),
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct Call {
    inner: RtcCall,
    /// `"<type>:<id>"`, for the `call_cid` of the SFU events.
    cid: String,
    tracks: Arc<TrackQueue>,
    end: watch::Receiver<CallEnd>,
    /// Python sees a cancelled `join()` at once, but the SDK future is dropped
    /// (and resets the call to `Idle`) only later on the tokio runtime. The
    /// next `join()` waits for this lock until that has happened.
    join_lock: Arc<Mutex<()>>,
}

#[pymethods]
impl Call {
    #[pyo3(signature = (user_id, create=true))]
    fn join<'py>(
        &self,
        py: Python<'py>,
        user_id: String,
        create: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let join_lock = self.join_lock.clone();
        let data = if create {
            JoinCallData::create(user_id)
        } else {
            JoinCallData::new(user_id)
        };
        future_into_py(py, async move {
            let _join_guard = join_lock.lock_owned().await;
            // Pinned in a local declared after the guard, so a cancelled join
            // drops the SDK future before it releases the lock.
            let join = call.join(data);
            tokio::pin!(join);
            join.as_mut().await.map_err(rtc_error)
        })
    }

    fn leave<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        future_into_py(py, async move { call.leave().await.map_err(rtc_error) })
    }

    fn session_id<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        future_into_py(py, async move { Ok(call.session_id().await) })
    }

    #[getter]
    fn calling_state(&self, py: Python<'_>) -> CallingState {
        py.detach(|| self.inner.calling_state()).into()
    }

    fn participants(&self, py: Python<'_>) -> Vec<RemoteParticipant> {
        py.detach(|| {
            self.inner
                .participants()
                .into_iter()
                .map(Into::into)
                .collect()
        })
    }

    fn call_state(&self, py: Python<'_>) -> CallStateSnapshot {
        py.detach(|| self.inner.call_state()).into()
    }

    fn sfu_events(&self, py: Python<'_>) -> EventStream {
        let source = Source::Sfu(py.detach(|| self.inner.sfu_events()));
        EventStream::new(source, self.cid.clone(), self.end.clone())
    }

    fn coordinator_events(&self, py: Python<'_>) -> EventStream {
        let source = Source::Coordinator(py.detach(|| self.inner.coordinator_events()));
        EventStream::new(source, self.cid.clone(), self.end.clone())
    }

    fn client_events(&self, py: Python<'_>) -> EventStream {
        let source = Source::Client(py.detach(|| self.inner.client_events()));
        EventStream::new(source, self.cid.clone(), self.end.clone())
    }

    fn tracks(&self) -> TrackStream {
        TrackStream::new(self.tracks.clone(), self.end.clone())
    }

    fn publish_audio<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalAudioTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = track.get().inner.clone();
        future_into_py(py, async move {
            call.publish_audio(track).await.map_err(rtc_error)
        })
    }

    fn publish_video<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalVideoTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = track.get().inner.clone();
        future_into_py(py, async move {
            call.publish_video(track).await.map_err(rtc_error)
        })
    }

    fn publish_screen_share<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalVideoTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = track.get().inner.clone();
        future_into_py(py, async move {
            call.publish_screen_share(track).await.map_err(rtc_error)
        })
    }

    fn stop_publish_audio<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalAudioTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = LocalTrack::Audio(track.get().inner.clone());
        future_into_py(py, async move {
            call.stop_publish(track).await.map_err(rtc_error)
        })
    }

    fn stop_publish_video<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalVideoTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = LocalTrack::Video {
            track: track.get().inner.clone(),
            track_type: models::TrackType::Video,
        };
        future_into_py(py, async move {
            call.stop_publish(track).await.map_err(rtc_error)
        })
    }

    fn stop_publish_screen_share<'py>(
        &self,
        py: Python<'py>,
        track: &Bound<'py, LocalVideoTrack>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let track = LocalTrack::Video {
            track: track.get().inner.clone(),
            track_type: models::TrackType::ScreenShare,
        };
        future_into_py(py, async move {
            call.stop_publish(track).await.map_err(rtc_error)
        })
    }

    fn mute_track<'py>(
        &self,
        py: Python<'py>,
        track_type: TrackType,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        future_into_py(py, async move {
            call.mute_track(track_type.into()).await.map_err(rtc_error)
        })
    }

    fn unmute_track<'py>(
        &self,
        py: Python<'py>,
        track_type: TrackType,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        future_into_py(py, async move {
            call.unmute_track(track_type.into())
                .await
                .map_err(rtc_error)
        })
    }

    fn update_subscriptions<'py>(
        &self,
        py: Python<'py>,
        config: SubscriptionConfig,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let config = getstream::rtc::SubscriptionConfig::from(config);
        future_into_py(py, async move {
            call.update_subscriptions(config).await.map_err(rtc_error)
        })
    }
}

#[pyclass(
    frozen,
    module = "getstream._rust.bindings",
    eq,
    eq_int,
    skip_from_py_object,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum CallingState {
    Idle,
    Joining,
    Joined,
    Reconnecting,
    Migrating,
    ReconnectingFailed,
    Left,
}

impl From<getstream::rtc::CallingState> for CallingState {
    fn from(state: getstream::rtc::CallingState) -> Self {
        use getstream::rtc::CallingState as Sdk;
        match state {
            Sdk::Idle => Self::Idle,
            Sdk::Joining => Self::Joining,
            Sdk::Joined => Self::Joined,
            Sdk::Reconnecting => Self::Reconnecting,
            Sdk::Migrating => Self::Migrating,
            Sdk::ReconnectingFailed => Self::ReconnectingFailed,
            Sdk::Left => Self::Left,
        }
    }
}
