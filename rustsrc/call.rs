use std::sync::Arc;

use getstream::ClientConfig;
use getstream::rtc::{JoinCallData, SubscriptionConfig};
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use tokio::sync::{Mutex, watch};

use crate::call_end::{self, CallEnd};
use crate::errors::{rtc_error, sdk_error};
use crate::events::EventStream;
use crate::participants::{CallStateSnapshot, RemoteParticipant};
use crate::tracks::{LocalAudioTrack, LocalVideoTrack, TrackQueue, TrackStream};

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct Client {
    inner: getstream::Stream,
}

#[pymethods]
impl Client {
    #[new]
    #[pyo3(signature = (api_key, api_secret, base_url=None, ws_url=None, log_bodies=false))]
    fn new(
        api_key: String,
        api_secret: String,
        base_url: Option<String>,
        ws_url: Option<String>,
        log_bodies: bool,
    ) -> PyResult<Self> {
        let mut config = ClientConfig::default();
        if let Some(base_url) = base_url {
            config.base_url = base_url;
        }
        if let Some(ws_url) = ws_url {
            config.coordinator_ws_url = ws_url;
        }
        config.log_bodies = log_bodies;
        let inner =
            getstream::Stream::with_config(api_key, api_secret, config).map_err(sdk_error)?;
        Ok(Self { inner })
    }

    fn call(&self, call_type: String, call_id: String) -> Call {
        let inner = self.inner.video().call(call_type, call_id);
        let end = call_end::watch_call_end(inner.subscribe());
        let tracks = TrackQueue::register(&inner);
        Call {
            inner,
            tracks,
            end,
            join_lock: Arc::default(),
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct Call {
    inner: getstream::Call,
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

    fn events(&self, py: Python<'_>) -> EventStream {
        EventStream::new(py.detach(|| self.inner.subscribe()), self.end.clone())
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

    #[pyo3(signature = (audio=true, video=false, screen_share=false, video_dimension=None))]
    fn update_subscriptions<'py>(
        &self,
        py: Python<'py>,
        audio: bool,
        video: bool,
        screen_share: bool,
        video_dimension: Option<(u32, u32)>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let call = self.inner.clone();
        let config = SubscriptionConfig {
            audio,
            video,
            screen_share,
            video_dimension,
        };
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
