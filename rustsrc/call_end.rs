use getstream::rtc::{CallEvent, CallingState};
use tokio::sync::broadcast::Receiver;
use tokio::sync::broadcast::error::RecvError;
use tokio::sync::watch;

/// The call ends on `CallEnded` or when this participant's state becomes
/// `Left`. `ends` counts the ends; a new join clears `ended` and keeps `ends`.
#[derive(Clone, Copy)]
pub struct CallEnd {
    ends: u64,
    ended: bool,
}

/// Returns true for the SDK events that end the call.
pub fn ends_call(event: &CallEvent) -> bool {
    matches!(
        event,
        CallEvent::CallEnded | CallEvent::CallingStateChanged(CallingState::Left)
    )
}

/// Watches the call's SDK events on the pyo3-async-runtimes tokio runtime. The
/// task stops when every receiver is dropped or the SDK core is gone.
pub fn watch_call_end(mut events: Receiver<CallEvent>) -> watch::Receiver<CallEnd> {
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
                Ok(event) if ends_call(&event) => sender.send_modify(|end| {
                    end.ends = end.ends.wrapping_add(1);
                    end.ended = true;
                }),
                Ok(CallEvent::CallingStateChanged(CallingState::Joining)) => {
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
