use pyo3::prelude::*;

mod call;
mod call_end;
mod errors;
mod events;
mod logging;
mod participants;
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
    m.add_class::<events::EventStream>()?;
    m.add_class::<events::ParticipantJoined>()?;
    m.add_class::<events::ParticipantLeft>()?;
    m.add_class::<events::TrackPublished>()?;
    m.add_class::<events::TrackUnpublished>()?;
    m.add_class::<events::CallEnded>()?;
    m.add_class::<events::CallingStateChanged>()?;
    m.add_class::<tracks::TrackStream>()?;
    m.add_class::<tracks::RemoteTrack>()?;
    m.add_class::<tracks::PcmFrame>()?;
    m.add_class::<tracks::VideoFrame>()?;
    m.add_class::<tracks::LocalAudioTrack>()?;
    m.add_class::<tracks::LocalVideoTrack>()?;
    m.add_function(wrap_pyfunction!(logging::configure_logging, m)?)?;
    logging::install(m)?;
    Ok(())
}
