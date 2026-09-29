use std::sync::Arc;

use getstream::rtc::CallEvent;
use pyo3::exceptions::PyStopAsyncIteration;
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use tokio::sync::broadcast::Receiver;
use tokio::sync::broadcast::error::RecvError;
use tokio::sync::{Mutex, watch};

use crate::call::CallingState;
use crate::call_end::{self, CallEnd};
use crate::errors::RtcError;
use crate::participants::{RemoteParticipant, TrackType};

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct ParticipantJoined {
    #[pyo3(get)]
    participant: RemoteParticipant,
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct ParticipantLeft {
    #[pyo3(get)]
    participant: RemoteParticipant,
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct TrackPublished {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    track_type: TrackType,
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct TrackUnpublished {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    track_type: TrackType,
}

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct CallEnded;

#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct CallingStateChanged {
    #[pyo3(get)]
    state: CallingState,
}

enum Event {
    ParticipantJoined(ParticipantJoined),
    ParticipantLeft(ParticipantLeft),
    TrackPublished(TrackPublished),
    TrackUnpublished(TrackUnpublished),
    CallEnded(CallEnded),
    CallingStateChanged(CallingStateChanged),
}

impl Event {
    /// Returns `None` for SDK events that have no Python class.
    fn from_sdk(event: CallEvent) -> Option<Self> {
        Some(match event {
            CallEvent::ParticipantJoined(participant) => {
                Self::ParticipantJoined(ParticipantJoined {
                    participant: participant.into(),
                })
            }
            CallEvent::ParticipantLeft(participant) => Self::ParticipantLeft(ParticipantLeft {
                participant: participant.into(),
            }),
            CallEvent::TrackPublished {
                user_id,
                session_id,
                track_type,
            } => Self::TrackPublished(TrackPublished {
                user_id,
                session_id,
                track_type: TrackType::from_i32(track_type),
            }),
            CallEvent::TrackUnpublished {
                user_id,
                session_id,
                track_type,
            } => Self::TrackUnpublished(TrackUnpublished {
                user_id,
                session_id,
                track_type: TrackType::from_i32(track_type),
            }),
            CallEvent::CallEnded => Self::CallEnded(CallEnded),
            CallEvent::CallingStateChanged(state) => {
                Self::CallingStateChanged(CallingStateChanged {
                    state: state.into(),
                })
            }
            _ => return None,
        })
    }
}

impl<'py> IntoPyObject<'py> for Event {
    type Target = PyAny;
    type Output = Bound<'py, PyAny>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        Ok(match self {
            Self::ParticipantJoined(event) => Bound::new(py, event)?.into_any(),
            Self::ParticipantLeft(event) => Bound::new(py, event)?.into_any(),
            Self::TrackPublished(event) => Bound::new(py, event)?.into_any(),
            Self::TrackUnpublished(event) => Bound::new(py, event)?.into_any(),
            Self::CallEnded(event) => Bound::new(py, event)?.into_any(),
            Self::CallingStateChanged(event) => Bound::new(py, event)?.into_any(),
        })
    }
}

struct EventStreamState {
    receiver: Receiver<CallEvent>,
    finished: bool,
}

/// Async iterator over the call's events. Each stream has its own SDK
/// subscription, so it sees only events sent after it was created. It ends
/// after the event that ends the call, or at once if the call had already
/// ended when the stream was created.
#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct EventStream {
    state: Arc<Mutex<EventStreamState>>,
    end: watch::Receiver<CallEnd>,
    start: Option<u64>,
}

impl EventStream {
    pub fn new(receiver: Receiver<CallEvent>, end: watch::Receiver<CallEnd>) -> Self {
        Self {
            state: Arc::new(Mutex::new(EventStreamState {
                receiver,
                finished: false,
            })),
            start: call_end::start(&end),
            end,
        }
    }
}

#[pymethods]
impl EventStream {
    fn __aiter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __anext__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let state = self.state.clone();
        let ended = call_end::ended(self.end.clone(), self.start);
        future_into_py(py, async move {
            let mut state = state.lock().await;
            let EventStreamState { receiver, finished } = &mut *state;
            tokio::pin!(ended);
            loop {
                if *finished {
                    return Err(PyStopAsyncIteration::new_err(()));
                }
                // Biased: events that are already buffered, including the event
                // that ends the call, are returned before the stream stops.
                let event = tokio::select! {
                    biased;
                    event = receiver.recv() => Some(event),
                    () = &mut ended => None,
                };
                match event {
                    Some(Ok(event)) => {
                        let ends = call_end::ends_call(&event);
                        if let Some(event) = Event::from_sdk(event) {
                            *finished = ends;
                            return Ok(event);
                        }
                    }
                    Some(Err(RecvError::Lagged(skipped))) => {
                        return Err(RtcError::new_err(format!(
                            "event stream lagged: {skipped} SDK events were dropped, \
                             including events that have no Python class"
                        )));
                    }
                    Some(Err(RecvError::Closed)) | None => *finished = true,
                }
            }
        })
    }
}
