use pyo3::prelude::*;

mod call;
mod call_end;
mod errors;
mod events;
mod logging;
mod participants;
mod repr;
mod subscriptions;
mod tracks;

#[pymodule]
fn bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_class::<call::Client>()?;
    m.add_class::<call::Call>()?;
    m.add_class::<call::CallingState>()?;
    m.add_class::<participants::TrackType>()?;
    m.add_class::<participants::RemoteParticipant>()?;
    m.add_class::<participants::CallStateSnapshot>()?;
    m.add_class::<subscriptions::TrackSubscriptionConfig>()?;
    m.add_class::<subscriptions::SubscriptionConfig>()?;
    m.add_class::<events::EventStream>()?;
    m.add_class::<events::CallEventBase>()?;
    m.add_class::<events::ParticipantJoined>()?;
    m.add_class::<events::ParticipantLeft>()?;
    m.add_class::<events::TrackPublished>()?;
    m.add_class::<events::TrackUnpublished>()?;
    m.add_class::<events::CallEnded>()?;
    m.add_class::<events::CallingStateChanged>()?;
    m.add_class::<events::CoordinatorEvent>()?;
    m.add_class::<events::ParticipantUpdated>()?;
    m.add_class::<events::DominantSpeakerChanged>()?;
    m.add_class::<events::AudioLevel>()?;
    m.add_class::<events::AudioLevelChanged>()?;
    m.add_class::<events::ConnectionQualityInfo>()?;
    m.add_class::<events::ConnectionQualityChanged>()?;
    m.add_class::<events::ParticipantCountChanged>()?;
    m.add_class::<events::Pin>()?;
    m.add_class::<events::PinsChanged>()?;
    m.add_class::<events::InboundVideoState>()?;
    m.add_class::<events::InboundStateNotification>()?;
    m.add_class::<events::CallGrants>()?;
    m.add_class::<events::CallGrantsUpdated>()?;
    m.add_class::<events::IceRestart>()?;
    m.add_class::<events::Codec>()?;
    m.add_class::<events::VideoDimension>()?;
    m.add_class::<events::AudioBitrate>()?;
    m.add_class::<events::PublishOption>()?;
    m.add_class::<events::ChangePublishOptions>()?;
    m.add_class::<events::AudioSender>()?;
    m.add_class::<events::VideoLayerSetting>()?;
    m.add_class::<events::VideoSender>()?;
    m.add_class::<events::ChangePublishQuality>()?;
    m.add_class::<events::ErrorDetails>()?;
    m.add_class::<events::SfuError>()?;
    m.add_class::<events::EventsLagged>()?;
    m.add_class::<tracks::TrackStream>()?;
    m.add_class::<tracks::RemoteTrack>()?;
    m.add_class::<tracks::PcmFrame>()?;
    m.add_class::<tracks::VideoFrame>()?;
    m.add_class::<tracks::VideoFrameStream>()?;
    m.add_class::<tracks::LocalAudioTrack>()?;
    m.add_class::<tracks::LocalVideoTrack>()?;
    m.add_function(wrap_pyfunction!(logging::configure_logging, m)?)?;
    logging::install(m)?;
    Ok(())
}
