use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex as StdMutex, PoisonError};
use std::time::Duration;

use getstream::rtc::{LocalAudioTrackConfig, RtcCall};
use numpy::{PyArray1, PyReadonlyArray1, PyUntypedArrayMethods};
use pyo3::exceptions::{PyStopAsyncIteration, PyValueError};
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use tokio::sync::{Mutex, mpsc, watch};

use crate::call_end::{self, CallEnd};
use crate::errors::{RtcError, rtc_error};
use crate::participants::{RemoteParticipant, TrackType};
use crate::repr::repr;

const TRACK_QUEUE_CAPACITY: usize = 64;

/// Remote tracks from the SDK `on_track` callback, registered when the call
/// handle is created so tracks that arrive during join are kept.
pub struct TrackQueue {
    receiver: Mutex<mpsc::Receiver<getstream::rtc::RemoteTrack>>,
    overflowed: AtomicBool,
}

impl TrackQueue {
    pub fn register(call: &RtcCall) -> Arc<Self> {
        let (sender, receiver) = mpsc::channel(TRACK_QUEUE_CAPACITY);
        let queue = Arc::new(Self {
            receiver: Mutex::new(receiver),
            overflowed: AtomicBool::new(false),
        });
        // The SDK core owns this callback and the Python handles own the queue.
        // A weak reference lets the queue, with any tracks still in it, be freed
        // together with the Python handles.
        let callback_queue = Arc::downgrade(&queue);
        call.on_track(move |track| {
            if sender.try_send(track).is_err()
                && let Some(queue) = callback_queue.upgrade()
            {
                queue.overflowed.store(true, Ordering::Relaxed);
            }
        });
        queue
    }
}

/// Async iterator over remote tracks. All streams of one call share a single
/// queue, so each track is delivered to exactly one stream. A stream ends when
/// the call ends, or at once if the call had already ended when the stream was
/// created.
#[pyclass(frozen, module = "getstream_rtc")]
pub struct TrackStream {
    queue: Arc<TrackQueue>,
    end: watch::Receiver<CallEnd>,
    start: Option<u64>,
}

impl TrackStream {
    pub fn new(queue: Arc<TrackQueue>, end: watch::Receiver<CallEnd>) -> Self {
        Self {
            queue,
            start: call_end::start(&end),
            end,
        }
    }
}

#[pymethods]
impl TrackStream {
    fn __aiter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __anext__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let queue = self.queue.clone();
        let ended = call_end::ended(self.end.clone(), self.start);
        future_into_py(py, async move {
            if queue.overflowed.swap(false, Ordering::Relaxed) {
                return Err(RtcError::new_err(
                    "track queue overflowed: remote tracks were dropped",
                ));
            }
            let mut receiver = queue.receiver.lock().await;
            // Biased: once the call has ended, tracks still in the queue are
            // not returned.
            let track = tokio::select! {
                biased;
                () = ended => None,
                track = receiver.recv() => track,
            };
            match track {
                Some(track) => Ok(RemoteTrack::new(track)),
                None => Err(PyStopAsyncIteration::new_err(())),
            }
        })
    }
}

#[pyclass(frozen, module = "getstream_rtc")]
pub struct RemoteTrack {
    inner: Arc<getstream::rtc::RemoteTrack>,
    video: Arc<VideoFrames>,
    #[pyo3(get)]
    participant: RemoteParticipant,
    #[pyo3(get)]
    track_type: TrackType,
}

impl RemoteTrack {
    fn new(track: getstream::rtc::RemoteTrack) -> Self {
        let inner = Arc::new(track);
        Self {
            participant: inner.participant().clone().into(),
            track_type: inner.track_type().into(),
            video: Arc::new(VideoFrames {
                track: Arc::clone(&inner),
                latest: watch::Sender::new(LatestFrame::Waiting),
                decoding: StdMutex::new(false),
            }),
            inner,
        }
    }
}

#[pymethods]
impl RemoteTrack {
    /// The next decoded audio frame, or `None` when the track has ended or is
    /// not an audio track.
    fn next_pcm<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let track = self.inner.clone();
        future_into_py(
            py,
            async move { Ok(track.next_pcm().await.map(PcmFrameData)) },
        )
    }

    /// A new stream of the frames decoded after this call.
    fn video_frames(&self) -> VideoFrameStream {
        VideoFrameStream {
            receiver: Arc::new(Mutex::new(self.video.latest.subscribe())),
            frames: Arc::clone(&self.video),
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "RemoteTrack(participant={}, track_type={})",
            repr(py, self.participant.clone())?,
            repr(py, self.track_type)?,
        ))
    }
}

/// Interleaved int16 samples; the array owns the SDK buffer without a copy.
#[pyclass(frozen, module = "getstream_rtc")]
pub struct PcmFrame {
    #[pyo3(get)]
    samples: Py<PyArray1<i16>>,
    #[pyo3(get)]
    sample_rate: u32,
    #[pyo3(get)]
    channels: u16,
    /// The RTP timestamp of the first sample, on the 48 kHz Opus clock. It
    /// wraps at 2^32, like RTP.
    #[pyo3(get)]
    pts: Option<u32>,
}

#[pymethods]
impl PcmFrame {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "PcmFrame(sample_rate={}, channels={}, samples={}, pts={})",
            self.sample_rate,
            self.channels,
            self.samples.bind(py).len(),
            repr(py, self.pts)?
        ))
    }
}

pub(crate) struct PcmFrameData(pub(crate) getstream::rtc::PcmFrame);

impl<'py> IntoPyObject<'py> for PcmFrameData {
    type Target = PcmFrame;
    type Output = Bound<'py, PcmFrame>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> PyResult<Bound<'py, PcmFrame>> {
        let frame = self.0;
        Bound::new(
            py,
            PcmFrame {
                samples: PyArray1::from_vec(py, frame.samples).unbind(),
                sample_rate: frame.sample_rate,
                channels: frame.channels,
                pts: frame.pts,
            },
        )
    }
}

/// Packed I420 pixels; each stream gets its own copy of the SDK buffer.
#[pyclass(frozen, module = "getstream_rtc")]
pub struct VideoFrame {
    #[pyo3(get)]
    width: u32,
    #[pyo3(get)]
    height: u32,
    #[pyo3(get)]
    data: Py<PyArray1<u8>>,
    #[pyo3(get)]
    rtp_timestamp: u32,
}

#[pymethods]
impl VideoFrame {
    fn __repr__(&self) -> String {
        format!(
            "VideoFrame(width={}, height={}, rtp_timestamp={})",
            self.width, self.height, self.rtp_timestamp
        )
    }
}

struct VideoFrameData(Arc<getstream::rtc::VideoFrame>);

impl<'py> IntoPyObject<'py> for VideoFrameData {
    type Target = VideoFrame;
    type Output = Bound<'py, VideoFrame>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> PyResult<Bound<'py, VideoFrame>> {
        let frame = self.0;
        Bound::new(
            py,
            VideoFrame {
                width: frame.width,
                height: frame.height,
                data: PyArray1::from_slice(py, &frame.data).unbind(),
                rtp_timestamp: frame.rtp_timestamp,
            },
        )
    }
}

#[derive(Clone)]
enum LatestFrame {
    /// No frame has been decoded yet.
    Waiting,
    Frame(Arc<getstream::rtc::VideoFrame>),
    /// The last value: the track has ended or has no video decoder.
    TrackEnded,
}

/// The decoded frames of one video track, shared by the track and its
/// streams. One task decodes from the first read of a stream until the track
/// ends or no stream is left, and keeps only the latest frame.
struct VideoFrames {
    track: Arc<getstream::rtc::RemoteTrack>,
    latest: watch::Sender<LatestFrame>,
    /// Whether the task runs; it stays `true` after the track ends.
    decoding: StdMutex<bool>,
}

impl VideoFrames {
    fn start(self: &Arc<Self>) {
        let mut decoding = self.decoding.lock().unwrap_or_else(PoisonError::into_inner);
        if !*decoding {
            *decoding = true;
            pyo3_async_runtimes::tokio::get_runtime().spawn(Arc::clone(self).decode());
        }
    }

    async fn decode(self: Arc<Self>) {
        loop {
            tokio::select! {
                frame = self.track.next_video_frame() => {
                    let Some(frame) = frame else {
                        self.latest.send_replace(LatestFrame::TrackEnded);
                        return;
                    };
                    self.latest.send_replace(LatestFrame::Frame(Arc::new(frame)));
                }
                () = self.latest.closed() => {
                    let mut decoding = self.decoding.lock().unwrap_or_else(PoisonError::into_inner);
                    // A stream created after `closed` resolved can find
                    // `decoding` still set and start no task, so this one
                    // continues for it.
                    if self.latest.receiver_count() == 0 {
                        *decoding = false;
                        return;
                    }
                }
            }
        }
    }
}

/// Async iterator over the decoded frames of one video track. Each stream has
/// its own receiver, so a slow stream skips frames without delaying the others.
#[pyclass(frozen, module = "getstream_rtc")]
pub struct VideoFrameStream {
    frames: Arc<VideoFrames>,
    receiver: Arc<Mutex<watch::Receiver<LatestFrame>>>,
}

#[pymethods]
impl VideoFrameStream {
    fn __aiter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __anext__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        self.frames.start();
        let receiver = Arc::clone(&self.receiver);
        future_into_py(py, async move {
            let mut receiver = receiver.lock().await;
            let ended = matches!(*receiver.borrow(), LatestFrame::TrackEnded);
            // `changed` fails only when the sender is dropped, after the
            // decoding has stopped.
            if ended || receiver.changed().await.is_err() {
                return Err(PyStopAsyncIteration::new_err(()));
            }
            match &*receiver.borrow_and_update() {
                LatestFrame::Frame(frame) => Ok(VideoFrameData(Arc::clone(frame))),
                LatestFrame::Waiting | LatestFrame::TrackEnded => {
                    Err(PyStopAsyncIteration::new_err(()))
                }
            }
        })
    }
}

#[pyclass(frozen, module = "getstream_rtc")]
pub struct LocalAudioTrack {
    pub(crate) inner: getstream::rtc::LocalAudioTrack,
}

#[pymethods]
impl LocalAudioTrack {
    /// `pcm_queue_capacity` is in seconds; `None` keeps the SDK default.
    #[new]
    #[pyo3(signature = (pcm_queue_capacity=None))]
    fn new(pcm_queue_capacity: Option<f64>) -> PyResult<Self> {
        let mut config = LocalAudioTrackConfig::default();
        if let Some(capacity) = pcm_queue_capacity {
            let capacity = Duration::try_from_secs_f64(capacity)
                .map_err(|error| PyValueError::new_err(error.to_string()))?;
            config = config.with_pcm_queue_capacity(capacity);
        }
        Ok(Self {
            inner: getstream::rtc::LocalAudioTrack::opus_with_config(config).map_err(rtc_error)?,
        })
    }

    /// Copies `samples` (interleaved int16) into the SDK queue.
    fn write_pcm<'py>(
        &self,
        py: Python<'py>,
        samples: PyReadonlyArray1<'py, i16>,
        sample_rate: u32,
        channels: u16,
    ) -> PyResult<Bound<'py, PyAny>> {
        // numpy's `as_array` requires an aligned buffer.
        if !samples.is_aligned() {
            return Err(PyValueError::new_err(
                "samples must be an aligned int16 array",
            ));
        }
        let frame =
            getstream::rtc::PcmFrame::new(samples.as_array().to_vec(), sample_rate, channels);
        let track = self.inner.clone();
        future_into_py(py, async move {
            track.write_pcm(frame).await.map_err(rtc_error)
        })
    }

    fn flush(&self, py: Python<'_>) {
        py.detach(|| self.inner.flush());
    }
}

#[pyclass(frozen, module = "getstream_rtc")]
pub struct LocalVideoTrack {
    pub(crate) inner: getstream::rtc::LocalVideoTrack,
}

#[pymethods]
impl LocalVideoTrack {
    #[staticmethod]
    fn vp8() -> PyResult<Self> {
        Ok(Self {
            inner: getstream::rtc::LocalVideoTrack::vp8().map_err(rtc_error)?,
        })
    }

    #[staticmethod]
    fn vp9() -> PyResult<Self> {
        Ok(Self {
            inner: getstream::rtc::LocalVideoTrack::vp9().map_err(rtc_error)?,
        })
    }

    /// Copies `data` (packed I420) and encodes it; `duration` is in seconds.
    fn write_i420<'py>(
        &self,
        py: Python<'py>,
        data: PyReadonlyArray1<'py, u8>,
        width: u32,
        height: u32,
        duration: f64,
    ) -> PyResult<Bound<'py, PyAny>> {
        let duration = Duration::try_from_secs_f64(duration)
            .map_err(|error| PyValueError::new_err(error.to_string()))?;
        let data = data.as_array().to_vec();
        let track = self.inner.clone();
        future_into_py(py, async move {
            track
                .write_i420(&data, width, height, duration)
                .await
                .map_err(rtc_error)
        })
    }
}
