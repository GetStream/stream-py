use getstream::rtc::{CallingState, ClientCallEvent, RtcCall};
use tokio::sync::broadcast::Receiver;
use tokio::sync::broadcast::error::RecvError;
use tokio::sync::watch;

/// The call ends when this participant's state becomes `Left`; the SDK leaves
/// on the SFU `call_ended` and on the coordinator `call.ended`. `ends` counts
/// the ends.
#[derive(Clone, Copy)]
pub struct CallEnd {
    ends: u64,
}

/// Watches the call's client events on the pyo3-async-runtimes tokio runtime. The
/// task stops when every receiver is dropped or the SDK core is gone.
pub fn watch_call_end(mut events: Receiver<ClientCallEvent>) -> watch::Receiver<CallEnd> {
    let (sender, receiver) = watch::channel(CallEnd { ends: 0 });
    pyo3_async_runtimes::tokio::get_runtime().spawn(async move {
        loop {
            let event = tokio::select! {
                event = events.recv() => event,
                () = sender.closed() => return,
            };
            match event {
                Ok(ClientCallEvent::CallingStateChanged(CallingState::Left)) => {
                    sender.send_modify(|end| end.ends = end.ends.wrapping_add(1));
                }
                Ok(_) | Err(RecvError::Lagged(_)) => {}
                Err(RecvError::Closed) => return,
            }
        }
    });
    receiver
}

/// The end count that a new stream waits for, or `None` if the call has
/// already ended. The SDK sets `Left` before `leave()` returns, but the watcher
/// counts that end later, so the state comes from the SDK. Takes the SDK
/// lifecycle lock: call it without the GIL.
pub fn start(call: &RtcCall, end: &watch::Receiver<CallEnd>) -> Option<u64> {
    // Read before the state, so an end between the two reads gives `None`
    // and not a count that the stream would wait past.
    let ends = end.borrow().ends;
    (call.calling_state() != CallingState::Left).then_some(ends)
}

/// Resolves when the call has ended after `start` was taken.
pub async fn ended(mut end: watch::Receiver<CallEnd>, start: Option<u64>) {
    if let Some(start) = start {
        // An error means the watcher stopped, which happens only when the SDK
        // core is gone.
        let _ = end.wait_for(|end| end.ends != start).await;
    }
}

#[cfg(test)]
mod tests {
    use getstream::rtc::RtcClient;

    use super::*;

    #[tokio::test]
    async fn a_stream_created_after_leave_has_ended() {
        let call = RtcClient::new("key", "token")
            .expect("a client")
            .call("default", "call");
        call.leave().await.expect("a leave");
        // No watcher has seen the leave yet.
        let (_sender, end) = watch::channel(CallEnd { ends: 0 });

        assert_eq!(start(&call, &end), None);
    }
}
