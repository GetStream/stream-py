use getstream::rtc::{CallingState, ClientCallEvent};
use tokio::sync::broadcast::Receiver;
use tokio::sync::broadcast::error::RecvError;
use tokio::sync::watch;

/// The call ends when this participant's state becomes `Left`; the SDK leaves
/// on the SFU `call_ended` and on the coordinator `call.ended`. `ends` counts
/// the ends; a new join clears `ended` and keeps `ends`.
#[derive(Clone, Copy)]
pub struct CallEnd {
    ends: u64,
    ended: bool,
}

/// Watches the call's client events on the pyo3-async-runtimes tokio runtime. The
/// task stops when every receiver is dropped or the SDK core is gone.
pub fn watch_call_end(mut events: Receiver<ClientCallEvent>) -> watch::Receiver<CallEnd> {
    let (sender, receiver) = watch::channel(CallEnd {
        ends: 0,
        ended: false,
    });
    pyo3_async_runtimes::tokio::get_runtime().spawn(async move {
        loop {
            let event = tokio::select! {
                event = events.recv() => event,
                () = sender.closed() => return,
            };
            match event {
                Ok(ClientCallEvent::CallingStateChanged(CallingState::Left)) => {
                    sender.send_modify(|end| {
                        end.ends = end.ends.wrapping_add(1);
                        end.ended = true;
                    });
                }
                Ok(ClientCallEvent::CallingStateChanged(CallingState::Joining)) => {
                    sender.send_modify(|end| end.ended = false);
                }
                Ok(_) | Err(RecvError::Lagged(_)) => {}
                Err(RecvError::Closed) => return,
            }
        }
    });
    receiver
}

/// The end count that a new stream waits for, or `None` if the call has
/// already ended.
pub fn start(end: &watch::Receiver<CallEnd>) -> Option<u64> {
    let end = *end.borrow();
    (!end.ended).then_some(end.ends)
}

/// Resolves when the call has ended after `start` was taken.
pub async fn ended(mut end: watch::Receiver<CallEnd>, start: Option<u64>) {
    if let Some(start) = start {
        // An error means the watcher stopped, which happens only when the SDK
        // core is gone.
        let _ = end.wait_for(|end| end.ends != start).await;
    }
}
