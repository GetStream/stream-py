use std::sync::Arc;

use getstream::rtc::proto::event;
use getstream::rtc::proto::models::{self, CallEndedReason};
use getstream::rtc::{ClientCallEvent, SfuCallEvent};
use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyStopAsyncIteration;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3_async_runtimes::tokio::future_into_py;
use tokio::sync::broadcast::Receiver;
use tokio::sync::broadcast::error::RecvError;
use tokio::sync::{Mutex, watch};

use crate::call::CallingState;
use crate::call_end::{self, CallEnd};
use crate::participants::{RemoteParticipant, TrackType};
use crate::repr::repr;

/// The base class of all events. `name` is the stable SDK event name: the
/// `SfuEvent` oneof field name for SFU events, the `type` for coordinator events.
#[pyclass(
    frozen,
    subclass,
    name = "CallEvent",
    module = "getstream._rust.bindings"
)]
pub struct CallEventBase {
    #[pyo3(get)]
    name: String,
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ParticipantJoined {
    /// The cid of this call, `"<type>:<id>"`.
    #[pyo3(get)]
    call_cid: String,
    #[pyo3(get)]
    participant: RemoteParticipant,
}

#[pymethods]
impl ParticipantJoined {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ParticipantJoined(call_cid={}, participant={})",
            repr(py, &self.call_cid)?,
            repr(py, self.participant.clone())?
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ParticipantLeft {
    /// The cid of this call, `"<type>:<id>"`.
    #[pyo3(get)]
    call_cid: String,
    #[pyo3(get)]
    participant: RemoteParticipant,
}

#[pymethods]
impl ParticipantLeft {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ParticipantLeft(call_cid={}, participant={})",
            repr(py, &self.call_cid)?,
            repr(py, self.participant.clone())?
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct TrackPublished {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    track_type: TrackType,
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    participant: Option<RemoteParticipant>,
}

#[pymethods]
impl TrackPublished {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "TrackPublished(user_id={}, session_id={}, track_type={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            repr(py, self.track_type)?,
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct TrackUnpublished {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    track_type: TrackType,
    /// The protobuf `TrackUnpublishReason` value.
    #[pyo3(get)]
    cause: i32,
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    participant: Option<RemoteParticipant>,
}

#[pymethods]
impl TrackUnpublished {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "TrackUnpublished(user_id={}, session_id={}, track_type={}, cause={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            repr(py, self.track_type)?,
            self.cause,
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct CallEnded {
    /// The protobuf `CallEndedReason` value.
    #[pyo3(get)]
    reason: i32,
}

#[pymethods]
impl CallEnded {
    /// For an end that comes without the SFU `call_ended`, for example when the
    /// coordinator ends the call.
    #[new]
    fn new() -> PyClassInitializer<Self> {
        let name = SfuCallEvent::CallEnded {
            reason: CallEndedReason::Unspecified,
        }
        .name();
        PyClassInitializer::from(CallEventBase {
            name: name.to_owned(),
        })
        .add_subclass(Self {
            reason: CallEndedReason::Unspecified as i32,
        })
    }

    fn __repr__(&self) -> String {
        format!("CallEnded(reason={})", self.reason)
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct CallingStateChanged {
    #[pyo3(get)]
    state: CallingState,
}

#[pymethods]
impl CallingStateChanged {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "CallingStateChanged(state={})",
            repr(py, self.state)?
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ParticipantUpdated {
    /// The cid of this call, `"<type>:<id>"`.
    #[pyo3(get)]
    call_cid: String,
    #[pyo3(get)]
    participant: RemoteParticipant,
}

#[pymethods]
impl ParticipantUpdated {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ParticipantUpdated(call_cid={}, participant={})",
            repr(py, &self.call_cid)?,
            repr(py, self.participant.clone())?
        ))
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct DominantSpeakerChanged {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
}

#[pymethods]
impl DominantSpeakerChanged {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "DominantSpeakerChanged(user_id={}, session_id={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?
        ))
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct AudioLevel {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    /// 0.0 is silence, 1.0 the loudest.
    #[pyo3(get)]
    level: f32,
    #[pyo3(get)]
    is_speaking: bool,
}

#[pymethods]
impl AudioLevel {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "AudioLevel(user_id={}, session_id={}, level={}, is_speaking={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            self.level,
            repr(py, self.is_speaking)?
        ))
    }
}

impl From<event::AudioLevel> for AudioLevel {
    fn from(level: event::AudioLevel) -> Self {
        Self {
            user_id: level.user_id,
            session_id: level.session_id,
            level: level.level,
            is_speaking: level.is_speaking,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct AudioLevelChanged {
    #[pyo3(get)]
    audio_levels: Vec<AudioLevel>,
}

#[pymethods]
impl AudioLevelChanged {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "AudioLevelChanged(audio_levels={})",
            repr(py, self.audio_levels.clone())?
        ))
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct ConnectionQualityInfo {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    /// The protobuf `ConnectionQuality` value.
    #[pyo3(get)]
    connection_quality: i32,
}

#[pymethods]
impl ConnectionQualityInfo {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ConnectionQualityInfo(user_id={}, session_id={}, connection_quality={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            self.connection_quality
        ))
    }
}

impl From<event::ConnectionQualityInfo> for ConnectionQualityInfo {
    fn from(info: event::ConnectionQualityInfo) -> Self {
        Self {
            user_id: info.user_id,
            session_id: info.session_id,
            connection_quality: info.connection_quality,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ConnectionQualityChanged {
    #[pyo3(get)]
    connection_quality_updates: Vec<ConnectionQualityInfo>,
}

#[pymethods]
impl ConnectionQualityChanged {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ConnectionQualityChanged(connection_quality_updates={})",
            repr(py, self.connection_quality_updates.clone())?
        ))
    }
}

/// Sent by the SDK when the SFU's participant count changes.
#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ParticipantCountChanged {
    #[pyo3(get)]
    total: u32,
    #[pyo3(get)]
    anonymous: u32,
}

#[pymethods]
impl ParticipantCountChanged {
    fn __repr__(&self) -> String {
        format!(
            "ParticipantCountChanged(total={}, anonymous={})",
            self.total, self.anonymous
        )
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct Pin {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
}

#[pymethods]
impl Pin {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "Pin(user_id={}, session_id={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?
        ))
    }
}

impl From<models::Pin> for Pin {
    fn from(pin: models::Pin) -> Self {
        Self {
            user_id: pin.user_id,
            session_id: pin.session_id,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct PinsChanged {
    #[pyo3(get)]
    pins: Vec<Pin>,
}

#[pymethods]
impl PinsChanged {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "PinsChanged(pins={})",
            repr(py, self.pins.clone())?
        ))
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct InboundVideoState {
    #[pyo3(get)]
    user_id: String,
    #[pyo3(get)]
    session_id: String,
    #[pyo3(get)]
    track_type: TrackType,
    #[pyo3(get)]
    paused: bool,
}

#[pymethods]
impl InboundVideoState {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "InboundVideoState(user_id={}, session_id={}, track_type={}, paused={})",
            repr(py, &self.user_id)?,
            repr(py, &self.session_id)?,
            repr(py, self.track_type)?,
            repr(py, self.paused)?
        ))
    }
}

impl From<event::InboundVideoState> for InboundVideoState {
    fn from(state: event::InboundVideoState) -> Self {
        Self {
            user_id: state.user_id,
            session_id: state.session_id,
            track_type: TrackType::from_i32(state.track_type),
            paused: state.paused,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct InboundStateNotification {
    #[pyo3(get)]
    inbound_video_states: Vec<InboundVideoState>,
}

#[pymethods]
impl InboundStateNotification {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "InboundStateNotification(inbound_video_states={})",
            repr(py, self.inbound_video_states.clone())?
        ))
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct CallGrants {
    #[pyo3(get)]
    can_publish_audio: bool,
    #[pyo3(get)]
    can_publish_video: bool,
    #[pyo3(get)]
    can_screenshare: bool,
}

#[pymethods]
impl CallGrants {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "CallGrants(can_publish_audio={}, can_publish_video={}, can_screenshare={})",
            repr(py, self.can_publish_audio)?,
            repr(py, self.can_publish_video)?,
            repr(py, self.can_screenshare)?
        ))
    }
}

impl From<models::CallGrants> for CallGrants {
    fn from(grants: models::CallGrants) -> Self {
        Self {
            can_publish_audio: grants.can_publish_audio,
            can_publish_video: grants.can_publish_video,
            can_screenshare: grants.can_screenshare,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct CallGrantsUpdated {
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    current_grants: Option<CallGrants>,
    #[pyo3(get)]
    message: String,
}

#[pymethods]
impl CallGrantsUpdated {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "CallGrantsUpdated(current_grants={}, message={})",
            repr(py, self.current_grants.clone())?,
            repr(py, &self.message)?
        ))
    }
}

/// Sent after the SDK has handled the SFU's ICE restart request.
#[pyclass(
    frozen,
    extends = CallEventBase,
    name = "ICERestart",
    module = "getstream._rust.bindings"
)]
pub struct IceRestart {
    /// The protobuf `PeerType` value.
    #[pyo3(get)]
    peer_type: i32,
}

#[pymethods]
impl IceRestart {
    fn __repr__(&self) -> String {
        format!("ICERestart(peer_type={})", self.peer_type)
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct Codec {
    #[pyo3(get)]
    payload_type: u32,
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    clock_rate: u32,
    #[pyo3(get)]
    encoding_parameters: String,
    #[pyo3(get)]
    fmtp: String,
}

#[pymethods]
impl Codec {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "Codec(name={}, payload_type={}, clock_rate={})",
            repr(py, &self.name)?,
            self.payload_type,
            self.clock_rate
        ))
    }
}

impl From<models::Codec> for Codec {
    fn from(codec: models::Codec) -> Self {
        Self {
            payload_type: codec.payload_type,
            name: codec.name,
            clock_rate: codec.clock_rate,
            encoding_parameters: codec.encoding_parameters,
            fmtp: codec.fmtp,
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct VideoDimension {
    #[pyo3(get)]
    width: u32,
    #[pyo3(get)]
    height: u32,
}

#[pymethods]
impl VideoDimension {
    fn __repr__(&self) -> String {
        format!(
            "VideoDimension(width={}, height={})",
            self.width, self.height
        )
    }
}

impl From<models::VideoDimension> for VideoDimension {
    fn from(dimension: models::VideoDimension) -> Self {
        Self {
            width: dimension.width,
            height: dimension.height,
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct AudioBitrate {
    /// The protobuf `AudioBitrateProfile` value.
    #[pyo3(get)]
    profile: i32,
    #[pyo3(get)]
    bitrate: i32,
}

#[pymethods]
impl AudioBitrate {
    fn __repr__(&self) -> String {
        format!(
            "AudioBitrate(profile={}, bitrate={})",
            self.profile, self.bitrate
        )
    }
}

impl From<models::AudioBitrate> for AudioBitrate {
    fn from(bitrate: models::AudioBitrate) -> Self {
        Self {
            profile: bitrate.profile,
            bitrate: bitrate.bitrate,
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct PublishOption {
    #[pyo3(get)]
    track_type: TrackType,
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    codec: Option<Codec>,
    #[pyo3(get)]
    bitrate: i32,
    #[pyo3(get)]
    fps: i32,
    #[pyo3(get)]
    max_spatial_layers: i32,
    #[pyo3(get)]
    max_temporal_layers: i32,
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    video_dimension: Option<VideoDimension>,
    #[pyo3(get)]
    id: i32,
    #[pyo3(get)]
    use_single_layer: bool,
    #[pyo3(get)]
    audio_bitrate_profiles: Vec<AudioBitrate>,
    /// The protobuf `DegradationPreference` value.
    #[pyo3(get)]
    degradation_preference: i32,
}

#[pymethods]
impl PublishOption {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "PublishOption(id={}, track_type={}, codec={}, bitrate={})",
            self.id,
            repr(py, self.track_type)?,
            repr(py, self.codec.clone())?,
            self.bitrate
        ))
    }
}

impl From<models::PublishOption> for PublishOption {
    fn from(option: models::PublishOption) -> Self {
        Self {
            track_type: TrackType::from_i32(option.track_type),
            codec: option.codec.map(Into::into),
            bitrate: option.bitrate,
            fps: option.fps,
            max_spatial_layers: option.max_spatial_layers,
            max_temporal_layers: option.max_temporal_layers,
            video_dimension: option.video_dimension.map(Into::into),
            id: option.id,
            use_single_layer: option.use_single_layer,
            audio_bitrate_profiles: option
                .audio_bitrate_profiles
                .into_iter()
                .map(Into::into)
                .collect(),
            degradation_preference: option.degradation_preference,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ChangePublishOptions {
    #[pyo3(get)]
    publish_options: Vec<PublishOption>,
    #[pyo3(get)]
    reason: String,
}

#[pymethods]
impl ChangePublishOptions {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ChangePublishOptions(publish_options={}, reason={})",
            repr(py, self.publish_options.clone())?,
            repr(py, &self.reason)?
        ))
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct AudioSender {
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    codec: Option<Codec>,
    #[pyo3(get)]
    track_type: TrackType,
    #[pyo3(get)]
    publish_option_id: i32,
}

#[pymethods]
impl AudioSender {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "AudioSender(codec={}, track_type={}, publish_option_id={})",
            repr(py, self.codec.clone())?,
            repr(py, self.track_type)?,
            self.publish_option_id
        ))
    }
}

impl From<event::AudioSender> for AudioSender {
    fn from(sender: event::AudioSender) -> Self {
        Self {
            codec: sender.codec.map(Into::into),
            track_type: TrackType::from_i32(sender.track_type),
            publish_option_id: sender.publish_option_id,
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct VideoLayerSetting {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    active: bool,
    #[pyo3(get)]
    max_bitrate: i32,
    #[pyo3(get)]
    scale_resolution_down_by: f32,
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    codec: Option<Codec>,
    #[pyo3(get)]
    max_framerate: u32,
    #[pyo3(get)]
    scalability_mode: String,
}

#[pymethods]
impl VideoLayerSetting {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "VideoLayerSetting(name={}, active={}, max_bitrate={})",
            repr(py, &self.name)?,
            repr(py, self.active)?,
            self.max_bitrate
        ))
    }
}

impl From<event::VideoLayerSetting> for VideoLayerSetting {
    fn from(layer: event::VideoLayerSetting) -> Self {
        Self {
            name: layer.name,
            active: layer.active,
            max_bitrate: layer.max_bitrate,
            scale_resolution_down_by: layer.scale_resolution_down_by,
            codec: layer.codec.map(Into::into),
            max_framerate: layer.max_framerate,
            scalability_mode: layer.scalability_mode,
        }
    }
}

#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct VideoSender {
    /// `None` if the SFU did not send it.
    #[pyo3(get)]
    codec: Option<Codec>,
    #[pyo3(get)]
    layers: Vec<VideoLayerSetting>,
    #[pyo3(get)]
    track_type: TrackType,
    #[pyo3(get)]
    publish_option_id: i32,
    /// The protobuf `DegradationPreference` value.
    #[pyo3(get)]
    degradation_preference: i32,
}

#[pymethods]
impl VideoSender {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "VideoSender(codec={}, track_type={}, layers={})",
            repr(py, self.codec.clone())?,
            repr(py, self.track_type)?,
            repr(py, self.layers.clone())?
        ))
    }
}

impl From<event::VideoSender> for VideoSender {
    fn from(sender: event::VideoSender) -> Self {
        Self {
            codec: sender.codec.map(Into::into),
            layers: sender.layers.into_iter().map(Into::into).collect(),
            track_type: TrackType::from_i32(sender.track_type),
            publish_option_id: sender.publish_option_id,
            degradation_preference: sender.degradation_preference,
        }
    }
}

#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct ChangePublishQuality {
    #[pyo3(get)]
    audio_senders: Vec<AudioSender>,
    #[pyo3(get)]
    video_senders: Vec<VideoSender>,
}

#[pymethods]
impl ChangePublishQuality {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ChangePublishQuality(audio_senders={}, video_senders={})",
            repr(py, self.audio_senders.clone())?,
            repr(py, self.video_senders.clone())?
        ))
    }
}

/// The protobuf `models.Error` inside the `Error` event.
#[pyclass(frozen, module = "getstream._rust.bindings", skip_from_py_object)]
#[derive(Clone)]
pub struct ErrorDetails {
    /// The protobuf `ErrorCode` value.
    #[pyo3(get)]
    code: i32,
    #[pyo3(get)]
    message: String,
    #[pyo3(get)]
    should_retry: bool,
}

#[pymethods]
impl ErrorDetails {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "ErrorDetails(code={}, message={}, should_retry={})",
            self.code,
            repr(py, &self.message)?,
            repr(py, self.should_retry)?
        ))
    }
}

#[pyclass(
    frozen,
    extends = CallEventBase,
    name = "Error",
    module = "getstream._rust.bindings"
)]
pub struct SfuError {
    #[pyo3(get)]
    error: ErrorDetails,
    /// The protobuf `WebsocketReconnectStrategy` value.
    #[pyo3(get)]
    reconnect_strategy: i32,
}

#[pymethods]
impl SfuError {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "Error(error={}, reconnect_strategy={})",
            repr(py, self.error.clone())?,
            self.reconnect_strategy
        ))
    }
}

/// Sent by the wrapper when this stream fell behind and lost `skipped` events.
/// The stream continues with the oldest event that is still buffered.
#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct EventsLagged {
    #[pyo3(get)]
    skipped: u64,
}

#[pymethods]
impl EventsLagged {
    fn __repr__(&self) -> String {
        format!("EventsLagged(skipped={})", self.skipped)
    }
}

/// A coordinator event of this call. `name` is its JSON `type`.
#[pyclass(frozen, extends = CallEventBase, module = "getstream._rust.bindings")]
pub struct CoordinatorEvent {
    /// The whole JSON message.
    #[pyo3(get)]
    data: Py<PyAny>,
}

#[pymethods]
impl CoordinatorEvent {
    fn __repr__(slf: PyRef<'_, Self>, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "CoordinatorEvent(name={})",
            repr(py, &slf.as_super().name)?
        ))
    }
}

enum Event {
    ParticipantJoined(ParticipantJoined),
    ParticipantLeft(ParticipantLeft),
    TrackPublished(TrackPublished),
    TrackUnpublished(TrackUnpublished),
    CallEnded(CallEnded),
    ParticipantUpdated(ParticipantUpdated),
    DominantSpeakerChanged(DominantSpeakerChanged),
    AudioLevelChanged(AudioLevelChanged),
    ConnectionQualityChanged(ConnectionQualityChanged),
    ParticipantCountChanged(ParticipantCountChanged),
    PinsChanged(PinsChanged),
    InboundStateNotification(InboundStateNotification),
    CallGrantsUpdated(CallGrantsUpdated),
    IceRestart(IceRestart),
    ChangePublishOptions(ChangePublishOptions),
    ChangePublishQuality(ChangePublishQuality),
    SfuError(SfuError),
    EventsLagged(EventsLagged),
    CallingStateChanged(CallingStateChanged),
    /// The JSON message; it becomes a `dict` when the Python object is made,
    /// with the GIL.
    Coordinator(serde_json::Value),
}

impl Event {
    /// Returns `None` for SDK events that have no Python class.
    fn from_sfu(event: SfuCallEvent, call_cid: &str) -> Option<Self> {
        Some(match event {
            SfuCallEvent::ParticipantJoined(participant) => {
                Self::ParticipantJoined(ParticipantJoined {
                    call_cid: call_cid.to_owned(),
                    participant: participant.into(),
                })
            }
            SfuCallEvent::ParticipantLeft(participant) => Self::ParticipantLeft(ParticipantLeft {
                call_cid: call_cid.to_owned(),
                participant: participant.into(),
            }),
            SfuCallEvent::TrackPublished {
                user_id,
                session_id,
                track_type,
                participant,
            } => Self::TrackPublished(TrackPublished {
                user_id,
                session_id,
                track_type: track_type.into(),
                participant: participant.map(Into::into),
            }),
            SfuCallEvent::TrackUnpublished {
                user_id,
                session_id,
                track_type,
                cause,
                participant,
            } => Self::TrackUnpublished(TrackUnpublished {
                user_id,
                session_id,
                track_type: track_type.into(),
                cause: cause as i32,
                participant: participant.map(Into::into),
            }),
            SfuCallEvent::CallEnded { reason } => Self::CallEnded(CallEnded {
                reason: reason as i32,
            }),
            SfuCallEvent::ParticipantUpdated(participant) => {
                Self::ParticipantUpdated(ParticipantUpdated {
                    call_cid: call_cid.to_owned(),
                    participant: participant.into(),
                })
            }
            SfuCallEvent::DominantSpeakerChanged {
                user_id,
                session_id,
            } => Self::DominantSpeakerChanged(DominantSpeakerChanged {
                user_id,
                session_id,
            }),
            SfuCallEvent::AudioLevelChanged(levels) => Self::AudioLevelChanged(AudioLevelChanged {
                audio_levels: levels.into_iter().map(Into::into).collect(),
            }),
            SfuCallEvent::ConnectionQualityChanged(updates) => {
                Self::ConnectionQualityChanged(ConnectionQualityChanged {
                    connection_quality_updates: updates.into_iter().map(Into::into).collect(),
                })
            }
            SfuCallEvent::ParticipantCountChanged(count) => {
                Self::ParticipantCountChanged(ParticipantCountChanged {
                    total: count.total,
                    anonymous: count.anonymous,
                })
            }
            SfuCallEvent::PinsUpdated(pins) => Self::PinsChanged(PinsChanged {
                pins: pins.into_iter().map(Into::into).collect(),
            }),
            SfuCallEvent::InboundStateChanged(states) => {
                Self::InboundStateNotification(InboundStateNotification {
                    inbound_video_states: states.into_iter().map(Into::into).collect(),
                })
            }
            SfuCallEvent::CallGrantsUpdated(event) => Self::CallGrantsUpdated(CallGrantsUpdated {
                current_grants: event.current_grants.map(Into::into),
                message: event.message,
            }),
            SfuCallEvent::IceRestarted(peer_type) => Self::IceRestart(IceRestart {
                peer_type: peer_type as i32,
            }),
            SfuCallEvent::PublishOptionsChanged {
                publish_options,
                reason,
            } => Self::ChangePublishOptions(ChangePublishOptions {
                publish_options: publish_options.into_iter().map(Into::into).collect(),
                reason,
            }),
            SfuCallEvent::PublishQualityChanged(quality) => {
                Self::ChangePublishQuality(ChangePublishQuality {
                    audio_senders: quality.audio_senders.into_iter().map(Into::into).collect(),
                    video_senders: quality.video_senders.into_iter().map(Into::into).collect(),
                })
            }
            SfuCallEvent::Error(error) => Self::SfuError(SfuError {
                error: ErrorDetails {
                    code: error.code,
                    message: error.message,
                    should_retry: error.should_retry,
                },
                reconnect_strategy: error.reconnect_strategy,
            }),
            _ => return None,
        })
    }

    /// Returns `None` for SDK events that have no Python class.
    fn from_client(event: ClientCallEvent) -> Option<Self> {
        match event {
            ClientCallEvent::CallingStateChanged(state) => {
                Some(Self::CallingStateChanged(CallingStateChanged {
                    state: state.into(),
                }))
            }
            _ => None,
        }
    }
}

/// The SDK receiver of one event stream.
pub enum Source {
    Sfu(Receiver<SfuCallEvent>),
    Coordinator(Receiver<getstream::rtc::CoordinatorEvent>),
    Client(Receiver<ClientCallEvent>),
}

impl Source {
    /// The next event, or `None` for an SDK event that has no Python class. A
    /// receiver that fell behind gives `EventsLagged` and then continues.
    async fn recv(&mut self, call_cid: &str) -> Result<Option<NamedEvent>, RecvError> {
        Ok(match self {
            Self::Sfu(receiver) => match receiver.recv().await {
                Ok(event) => {
                    let name = event.name().to_owned();
                    Event::from_sfu(event, call_cid).map(|event| NamedEvent { name, event })
                }
                Err(RecvError::Lagged(skipped)) => Some(NamedEvent::lagged(skipped)),
                Err(error) => return Err(error),
            },
            Self::Coordinator(receiver) => match receiver.recv().await {
                Ok(event) => Some(NamedEvent {
                    event: Event::Coordinator(event.raw),
                    name: event.event_type,
                }),
                Err(RecvError::Lagged(skipped)) => Some(NamedEvent::lagged(skipped)),
                Err(error) => return Err(error),
            },
            Self::Client(receiver) => match receiver.recv().await {
                Ok(event) => {
                    let name = event.name().to_owned();
                    Event::from_client(event).map(|event| NamedEvent { name, event })
                }
                Err(RecvError::Lagged(skipped)) => Some(NamedEvent::lagged(skipped)),
                Err(error) => return Err(error),
            },
        })
    }
}

struct NamedEvent {
    name: String,
    event: Event,
}

impl NamedEvent {
    fn lagged(skipped: u64) -> Self {
        tracing::warn!(skipped, "stream.rtc.events.lagged");
        Self {
            name: "events_lagged".to_owned(),
            event: Event::EventsLagged(EventsLagged { skipped }),
        }
    }
}

impl<'py> IntoPyObject<'py> for NamedEvent {
    type Target = PyAny;
    type Output = Bound<'py, PyAny>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let base = PyClassInitializer::from(CallEventBase { name: self.name });
        Ok(match self.event {
            Event::ParticipantJoined(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::ParticipantLeft(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::TrackPublished(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::TrackUnpublished(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::CallEnded(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::ParticipantUpdated(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::DominantSpeakerChanged(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::AudioLevelChanged(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::ConnectionQualityChanged(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::ParticipantCountChanged(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::PinsChanged(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::InboundStateNotification(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::CallGrantsUpdated(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::IceRestart(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::ChangePublishOptions(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::ChangePublishQuality(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::SfuError(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::EventsLagged(event) => Bound::new(py, base.add_subclass(event))?.into_any(),
            Event::CallingStateChanged(event) => {
                Bound::new(py, base.add_subclass(event))?.into_any()
            }
            Event::Coordinator(message) => {
                let data = json_to_py(py, &message)?.unbind();
                Bound::new(py, base.add_subclass(CoordinatorEvent { data }))?.into_any()
            }
        })
    }
}

/// The same objects as `json.loads`: integers become `int`, other numbers
/// `float`.
fn json_to_py<'py>(py: Python<'py>, value: &serde_json::Value) -> PyResult<Bound<'py, PyAny>> {
    use serde_json::Value;
    Ok(match value {
        Value::Null => py.None().into_bound(py),
        Value::Bool(boolean) => boolean.into_bound_py_any(py)?,
        Value::Number(number) => match (number.as_i64(), number.as_u64()) {
            (Some(integer), _) => integer.into_bound_py_any(py)?,
            (None, Some(integer)) => integer.into_bound_py_any(py)?,
            (None, None) => number.as_f64().into_bound_py_any(py)?,
        },
        Value::String(string) => string.into_bound_py_any(py)?,
        Value::Array(items) => PyList::new(
            py,
            items
                .iter()
                .map(|item| json_to_py(py, item))
                .collect::<PyResult<Vec<_>>>()?,
        )?
        .into_any(),
        Value::Object(fields) => {
            let dict = PyDict::new(py);
            for (key, field) in fields {
                dict.set_item(key, json_to_py(py, field)?)?;
            }
            dict.into_any()
        }
    })
}

struct EventStreamState {
    source: Source,
    call_cid: String,
    finished: bool,
}

/// Async iterator over one of the call's event streams. Each stream has its own
/// SDK subscription, so it sees only events sent after it was created. It ends
/// when the call ends, after the events that are already buffered, or at once
/// if the call had already ended when the stream was created.
#[pyclass(frozen, module = "getstream._rust.bindings")]
pub struct EventStream {
    state: Arc<Mutex<EventStreamState>>,
    end: watch::Receiver<CallEnd>,
    start: Option<u64>,
}

impl EventStream {
    pub fn new(source: Source, call_cid: String, end: watch::Receiver<CallEnd>) -> Self {
        Self {
            state: Arc::new(Mutex::new(EventStreamState {
                source,
                call_cid,
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
            let EventStreamState {
                source,
                call_cid,
                finished,
            } = &mut *state;
            tokio::pin!(ended);
            loop {
                if *finished {
                    return Err(PyStopAsyncIteration::new_err(()));
                }
                // Biased: events that are already buffered, including the event
                // that ends the call, are returned before the stream stops.
                let event = tokio::select! {
                    biased;
                    event = source.recv(call_cid) => Some(event),
                    () = &mut ended => None,
                };
                match event {
                    Some(Ok(Some(event))) => return Ok(event),
                    Some(Ok(None)) => {}
                    // `Source::recv` turns a lag into `EventsLagged`, so the
                    // only error left is `Closed`.
                    Some(Err(_)) | None => *finished = true,
                }
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn convert(event: SfuCallEvent) -> Event {
        Event::from_sfu(event, "default:call").expect("an event with a Python class")
    }

    #[tokio::test]
    async fn a_lagged_stream_continues_with_the_retained_events() {
        let (sender, receiver) = tokio::sync::broadcast::channel(1);
        let mut source = Source::Sfu(receiver);
        for user_id in ["dropped", "retained"] {
            sender
                .send(SfuCallEvent::DominantSpeakerChanged {
                    user_id: user_id.to_owned(),
                    session_id: String::new(),
                })
                .expect("a receiver");
        }

        let mut next = async || {
            source
                .recv("default:call")
                .await
                .expect("an event")
                .expect("an event with a Python class")
                .event
        };

        let Event::EventsLagged(lagged) = next().await else {
            panic!("expected EventsLagged");
        };
        assert_eq!(lagged.skipped, 1);
        let Event::DominantSpeakerChanged(event) = next().await else {
            panic!("expected DominantSpeakerChanged");
        };
        assert_eq!(event.user_id, "retained");
    }

    #[test]
    fn audio_levels_keep_their_fields() {
        let event = SfuCallEvent::AudioLevelChanged(vec![event::AudioLevel {
            user_id: "user".to_owned(),
            session_id: "session".to_owned(),
            level: 0.5,
            is_speaking: true,
        }]);

        let Event::AudioLevelChanged(event) = convert(event) else {
            panic!("expected AudioLevelChanged");
        };
        let level = &event.audio_levels[0];
        assert_eq!(
            (level.user_id.as_str(), level.session_id.as_str()),
            ("user", "session")
        );
        assert_eq!((level.level, level.is_speaking), (0.5, true));
    }

    #[test]
    fn connection_quality_keeps_the_protobuf_value() {
        let event = SfuCallEvent::ConnectionQualityChanged(vec![event::ConnectionQualityInfo {
            user_id: "user".to_owned(),
            session_id: "session".to_owned(),
            connection_quality: models::ConnectionQuality::Good as i32,
        }]);

        let Event::ConnectionQualityChanged(event) = convert(event) else {
            panic!("expected ConnectionQualityChanged");
        };
        assert_eq!(
            event.connection_quality_updates[0].connection_quality,
            models::ConnectionQuality::Good as i32
        );
    }

    #[test]
    fn participant_count_keeps_both_counts() {
        let event = SfuCallEvent::ParticipantCountChanged(models::ParticipantCount {
            total: 3,
            anonymous: 1,
        });

        let Event::ParticipantCountChanged(event) = convert(event) else {
            panic!("expected ParticipantCountChanged");
        };
        assert_eq!((event.total, event.anonymous), (3, 1));
    }

    #[test]
    fn inbound_state_has_the_track_type() {
        let event = SfuCallEvent::InboundStateChanged(vec![event::InboundVideoState {
            user_id: "user".to_owned(),
            session_id: "session".to_owned(),
            track_type: models::TrackType::ScreenShare as i32,
            paused: true,
        }]);

        let Event::InboundStateNotification(event) = convert(event) else {
            panic!("expected InboundStateNotification");
        };
        let state = &event.inbound_video_states[0];
        assert!(state.track_type == TrackType::ScreenShare && state.paused);
    }

    #[test]
    fn call_grants_are_none_when_absent() {
        let event = SfuCallEvent::CallGrantsUpdated(event::CallGrantsUpdated {
            current_grants: None,
            message: "revoked".to_owned(),
        });

        let Event::CallGrantsUpdated(event) = convert(event) else {
            panic!("expected CallGrantsUpdated");
        };
        assert!(event.current_grants.is_none());
        assert_eq!(event.message, "revoked");
    }

    #[test]
    fn ice_restart_keeps_the_peer_type() {
        let event = SfuCallEvent::IceRestarted(models::PeerType::Subscriber);

        let Event::IceRestart(event) = convert(event) else {
            panic!("expected IceRestart");
        };
        assert_eq!(event.peer_type, models::PeerType::Subscriber as i32);
    }

    #[test]
    fn error_keeps_the_nested_protobuf_shape() {
        let error = getstream::rtc::SfuJoinError::from_event(
            Some(models::Error {
                code: models::ErrorCode::ParticipantNotFound as i32,
                message: "gone".to_owned(),
                should_retry: true,
            }),
            models::WebsocketReconnectStrategy::Rejoin as i32,
        );

        let Event::SfuError(event) = convert(SfuCallEvent::Error(error)) else {
            panic!("expected SfuError");
        };
        assert_eq!(
            event.error.code,
            models::ErrorCode::ParticipantNotFound as i32
        );
        assert_eq!(event.error.message, "gone");
        assert!(event.error.should_retry);
        assert_eq!(
            event.reconnect_strategy,
            models::WebsocketReconnectStrategy::Rejoin as i32
        );
    }

    #[test]
    fn publish_options_keep_their_fields() {
        let event = SfuCallEvent::PublishOptionsChanged {
            publish_options: vec![models::PublishOption {
                track_type: models::TrackType::Video as i32,
                codec: Some(models::Codec {
                    name: "vp9".to_owned(),
                    ..Default::default()
                }),
                bitrate: 1000,
                video_dimension: None,
                audio_bitrate_profiles: vec![models::AudioBitrate {
                    profile: 1,
                    bitrate: 64,
                }],
                ..Default::default()
            }],
            reason: "codec".to_owned(),
        };

        let Event::ChangePublishOptions(event) = convert(event) else {
            panic!("expected ChangePublishOptions");
        };
        let option = &event.publish_options[0];
        assert!(option.track_type == TrackType::Video);
        assert_eq!(
            option.codec.as_ref().map(|codec| codec.name.as_str()),
            Some("vp9")
        );
        assert_eq!(option.bitrate, 1000);
        assert!(option.video_dimension.is_none());
        assert_eq!(option.audio_bitrate_profiles[0].bitrate, 64);
        assert_eq!(event.reason, "codec");
    }

    #[test]
    fn publish_quality_keeps_the_video_layers() {
        let event = SfuCallEvent::PublishQualityChanged(event::ChangePublishQuality {
            audio_senders: vec![],
            video_senders: vec![event::VideoSender {
                layers: vec![event::VideoLayerSetting {
                    name: "f".to_owned(),
                    active: true,
                    max_bitrate: 500,
                    ..Default::default()
                }],
                track_type: models::TrackType::Video as i32,
                ..Default::default()
            }],
        });

        let Event::ChangePublishQuality(event) = convert(event) else {
            panic!("expected ChangePublishQuality");
        };
        let layer = &event.video_senders[0].layers[0];
        assert_eq!(
            (layer.name.as_str(), layer.active, layer.max_bitrate),
            ("f", true, 500)
        );
    }

    #[test]
    fn participant_updated_has_the_call_cid() {
        let event = SfuCallEvent::ParticipantUpdated(models::Participant::default());

        let Event::ParticipantUpdated(event) = convert(event) else {
            panic!("expected ParticipantUpdated");
        };
        assert_eq!(event.call_cid, "default:call");
    }

    #[test]
    fn call_ended_keeps_the_sfu_reason() {
        let event = SfuCallEvent::CallEnded {
            reason: CallEndedReason::Kicked,
        };

        let Some(Event::CallEnded(event)) = Event::from_sfu(event, "default:call") else {
            panic!("expected CallEnded");
        };
        assert_eq!(event.reason, CallEndedReason::Kicked as i32);
    }

    #[test]
    fn participant_joined_has_the_call_cid() {
        let event = SfuCallEvent::ParticipantJoined(models::Participant {
            user_id: "user".to_owned(),
            ..Default::default()
        });

        let Some(Event::ParticipantJoined(event)) = Event::from_sfu(event, "default:call") else {
            panic!("expected ParticipantJoined");
        };
        assert_eq!(event.call_cid, "default:call");
    }
}
