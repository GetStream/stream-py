//! Queues Rust log records for Python `logging`.
//!
//! The SDK emits `tracing` events and third-party crates emit `log` records
//! (routed into `tracing` by `LogTracer`). A thread that logs only puts the
//! record into a bounded queue: it never blocks and never takes the GIL, so it
//! may hold an SDK lock. The Python thread `getstream-logging`
//! (`getstream_rtc/logging.py`) takes the records with `_next_logs`, which
//! waits without the GIL. Rust never calls Python to log.

use std::error::Error as StdError;
use std::fmt;
use std::sync::atomic::{AtomicU8, AtomicU64, Ordering};
use std::sync::mpsc::{Receiver, RecvError, SyncSender, TryRecvError, sync_channel};
use std::sync::{Mutex, OnceLock};
use std::time::{SystemTime, UNIX_EPOCH};

use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};
use tracing::field::{Field, Visit};
use tracing::level_filters::LevelFilter;
use tracing::{Event, Level, Metadata, Subscriber};
use tracing_log::{AsLog, NormalizeEvent};
use tracing_subscriber::layer::{Context, Layer, SubscriberExt};

const QUEUE_CAPACITY: usize = 1024;
/// The most records that one `_next_logs` returns, so the Python thread soon
/// reaches a marker and holds the GIL for a bounded time.
const BATCH_SIZE: usize = 256;
const SDK_CRATE: &str = "getstream";
/// Records of this crate use the SDK level.
const WRAPPER_CRATE: &str = env!("CARGO_CRATE_NAME");
/// Index = the value stored in the filter atomics.
const FILTERS: [LevelFilter; 6] = [
    LevelFilter::OFF,
    LevelFilter::ERROR,
    LevelFilter::WARN,
    LevelFilter::INFO,
    LevelFilter::DEBUG,
    LevelFilter::TRACE,
];

static SINK: OnceLock<Sink> = OnceLock::new();

struct Sink {
    sender: SyncSender<Message>,
    /// Taken only by the Python thread `getstream-logging`, without the GIL.
    receiver: Mutex<Receiver<Message>>,
    dropped: AtomicU64,
    sdk_filter: AtomicU8,
    third_party_filter: AtomicU8,
}

enum Message {
    Record(Box<Captured>),
    /// Put by `_push_log_marker`; it ends the batch that contains it.
    Marker(u64),
}

struct Captured {
    level: Level,
    target: String,
    file: Option<String>,
    line: Option<u32>,
    message: String,
    fields: Vec<(&'static str, FieldValue)>,
    created_ns: u64,
}

enum FieldValue {
    Bool(bool),
    I64(i64),
    U64(u64),
    F64(f64),
    Str(String),
}

impl Sink {
    /// Queues nothing until `_set_log_filters` enables a level.
    fn new() -> Self {
        let (sender, receiver) = sync_channel(QUEUE_CAPACITY);
        Self {
            sender,
            receiver: Mutex::new(receiver),
            dropped: AtomicU64::new(0),
            sdk_filter: AtomicU8::new(encode(LevelFilter::OFF)),
            third_party_filter: AtomicU8::new(encode(LevelFilter::OFF)),
        }
    }

    fn enabled(&self, target: &str, level: &Level) -> bool {
        let filter = if is_sdk_target(target) {
            &self.sdk_filter
        } else {
            &self.third_party_filter
        };
        *level <= decode(filter.load(Ordering::Relaxed))
    }

    fn max_filter(&self) -> LevelFilter {
        decode(self.sdk_filter.load(Ordering::Relaxed))
            .max(decode(self.third_party_filter.load(Ordering::Relaxed)))
    }

    fn set_filters(&self, sdk: LevelFilter, third_party: LevelFilter) {
        self.sdk_filter.store(encode(sdk), Ordering::Relaxed);
        self.third_party_filter
            .store(encode(third_party), Ordering::Relaxed);
    }

    /// Never blocks: a record that does not fit into the queue is counted.
    fn send(&self, record: Captured) {
        if self
            .sender
            .try_send(Message::Record(Box::new(record)))
            .is_err()
        {
            self.dropped.fetch_add(1, Ordering::Relaxed);
        }
    }
}

struct ForwardingLayer;

impl<S: Subscriber> Layer<S> for ForwardingLayer {
    fn enabled(&self, metadata: &Metadata<'_>, _ctx: Context<'_, S>) -> bool {
        SINK.get()
            .is_some_and(|sink| sink.enabled(metadata.target(), metadata.level()))
    }

    fn max_level_hint(&self) -> Option<LevelFilter> {
        SINK.get().map(Sink::max_filter)
    }

    fn on_event(&self, event: &Event<'_>, _ctx: Context<'_, S>) {
        let Some(sink) = SINK.get() else {
            return;
        };
        // Records from `LogTracer` carry their real target in their fields.
        let normalized = event.normalized_metadata();
        let metadata = normalized.as_ref().unwrap_or_else(|| event.metadata());
        if !sink.enabled(metadata.target(), metadata.level()) {
            return;
        }
        let mut visitor = FieldVisitor::default();
        event.record(&mut visitor);
        sink.send(Captured {
            level: *metadata.level(),
            target: metadata.target().to_owned(),
            file: metadata.file().map(str::to_owned),
            line: metadata.line(),
            message: visitor.message.unwrap_or_default(),
            fields: visitor.fields,
            created_ns: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map_or(0, |elapsed| {
                    u64::try_from(elapsed.as_nanos()).unwrap_or(u64::MAX)
                }),
        });
    }
}

#[derive(Default)]
struct FieldVisitor {
    message: Option<String>,
    fields: Vec<(&'static str, FieldValue)>,
}

impl FieldVisitor {
    fn push(&mut self, field: &Field, value: FieldValue) {
        match field.name() {
            "message" => self.message = Some(value.to_string()),
            // `LogTracer` metadata, already used through `normalized_metadata`.
            name if name.starts_with("log.") => {}
            name => self.fields.push((name, value)),
        }
    }
}

impl Visit for FieldVisitor {
    fn record_bool(&mut self, field: &Field, value: bool) {
        self.push(field, FieldValue::Bool(value));
    }

    fn record_i64(&mut self, field: &Field, value: i64) {
        self.push(field, FieldValue::I64(value));
    }

    fn record_u64(&mut self, field: &Field, value: u64) {
        self.push(field, FieldValue::U64(value));
    }

    fn record_f64(&mut self, field: &Field, value: f64) {
        self.push(field, FieldValue::F64(value));
    }

    fn record_str(&mut self, field: &Field, value: &str) {
        self.push(field, FieldValue::Str(value.to_owned()));
    }

    fn record_error(&mut self, field: &Field, value: &(dyn StdError + 'static)) {
        let mut text = value.to_string();
        let mut source = value.source();
        while let Some(error) = source {
            text.push_str(": ");
            text.push_str(&error.to_string());
            source = error.source();
        }
        self.push(field, FieldValue::Str(text));
    }

    fn record_debug(&mut self, field: &Field, value: &dyn fmt::Debug) {
        self.push(field, FieldValue::Str(format!("{value:?}")));
    }
}

impl fmt::Display for FieldValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Bool(value) => value.fmt(f),
            Self::I64(value) => value.fmt(f),
            Self::U64(value) => value.fmt(f),
            Self::F64(value) => value.fmt(f),
            Self::Str(value) => value.fmt(f),
        }
    }
}

impl FieldValue {
    fn into_python<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        match self {
            Self::Bool(value) => value.into_bound_py_any(py),
            Self::I64(value) => value.into_bound_py_any(py),
            Self::U64(value) => value.into_bound_py_any(py),
            Self::F64(value) => value.into_bound_py_any(py),
            Self::Str(value) => value.into_bound_py_any(py),
        }
    }
}

/// Installs the `tracing` subscriber and `LogTracer`. Nothing is queued until
/// `_set_log_filters` enables a level.
pub fn install() -> PyResult<()> {
    if SINK.get().is_some() {
        return Ok(());
    }
    tracing::subscriber::set_global_default(tracing_subscriber::registry().with(ForwardingLayer))
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    tracing_log::LogTracer::builder()
        .with_max_level(log::LevelFilter::Off)
        .init()
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    // Last: if a global subscriber or logger was already set, each import
    // raises instead of running without a subscriber.
    let _ = SINK.set(Sink::new());
    Ok(())
}

/// Queues SDK records at `level` or above, and third-party records at the less
/// verbose of `level` and `third_party_level`; `level=None` queues none.
#[pyfunction]
#[pyo3(name = "_set_log_filters")]
pub fn set_log_filters(py: Python<'_>, level: Option<i32>, third_party_level: i32) -> PyResult<()> {
    let sink = sink()?;
    let sdk = level.map_or(LevelFilter::OFF, filter_from_python);
    let third_party = sdk.min(filter_from_python(third_party_level));
    py.detach(|| {
        sink.set_filters(sdk, third_party);
        tracing::callsite::rebuild_interest_cache();
        log::set_max_level(sdk.max(third_party).as_log());
    });
    Ok(())
}

/// Waits without the GIL for queued records. Returns the number of records
/// dropped since the last call, at most `BATCH_SIZE` records as the arguments
/// of `getstream_rtc.logging.handle_record` after its logger, and the marker
/// that ended the batch, if any.
#[pyfunction]
#[pyo3(name = "_next_logs")]
pub fn next_logs(py: Python<'_>) -> PyResult<(u64, Vec<Bound<'_, PyTuple>>, Option<u64>)> {
    let sink = sink()?;
    let (records, marker) = py
        .detach(|| {
            let receiver = sink
                .receiver
                .lock()
                .unwrap_or_else(|error| error.into_inner());
            take_batch(&receiver)
        })
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    let dropped = sink.dropped.swap(0, Ordering::Relaxed);
    let records = records
        .into_iter()
        .map(|record| record_args(py, record))
        .collect::<PyResult<_>>()?;
    Ok((dropped, records, marker))
}

/// Puts `marker` into the queue after the records queued before it. Waits
/// without the GIL while the queue is full.
#[pyfunction]
#[pyo3(name = "_push_log_marker")]
pub fn push_log_marker(py: Python<'_>, marker: u64) -> PyResult<()> {
    let sink = sink()?;
    py.detach(|| sink.sender.send(Message::Marker(marker)))
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))
}

fn sink() -> PyResult<&'static Sink> {
    SINK.get()
        .ok_or_else(|| PyRuntimeError::new_err("the logging is not installed"))
}

/// Waits for the first message, then takes the queued messages until the
/// batch has `BATCH_SIZE` records or a marker ends it.
fn take_batch(receiver: &Receiver<Message>) -> Result<(Vec<Captured>, Option<u64>), RecvError> {
    let mut records = Vec::new();
    let mut message = receiver.recv()?;
    loop {
        match message {
            Message::Marker(marker) => return Ok((records, Some(marker))),
            Message::Record(record) => records.push(*record),
        }
        if records.len() == BATCH_SIZE {
            return Ok((records, None));
        }
        message = match receiver.try_recv() {
            Ok(message) => message,
            Err(TryRecvError::Empty | TryRecvError::Disconnected) => return Ok((records, None)),
        };
    }
}

/// The arguments of `getstream_rtc.logging.handle_record` after its logger.
fn record_args(py: Python<'_>, record: Captured) -> PyResult<Bound<'_, PyTuple>> {
    let fields = PyDict::new(py);
    for (name, value) in record.fields {
        fields.set_item(name.replace('.', "_"), value.into_python(py)?)?;
    }
    (
        logger_name(&record.target),
        python_level(record.level),
        record.file.unwrap_or_default(),
        record.line.unwrap_or_default(),
        record.message,
        record.created_ns,
        record.target,
        fields,
    )
        .into_pyobject(py)
}

/// The Python logger name below the configured logger, or `None` for the
/// configured logger itself. SDK targets drop the crate name
/// (`getstream::rtc::join` -> `rtc.join`); third-party targets keep it
/// (`webrtc_ice::agent` -> `webrtc_ice.agent`).
fn logger_name(target: &str) -> Option<String> {
    match target.strip_prefix(SDK_CRATE) {
        Some("") => None,
        Some(rest) if rest.starts_with("::") => Some(rest[2..].replace("::", ".")),
        _ => Some(target.replace("::", ".")),
    }
}

fn is_sdk_target(target: &str) -> bool {
    [SDK_CRATE, WRAPPER_CRATE].into_iter().any(|name| {
        target
            .strip_prefix(name)
            .is_some_and(|rest| rest.is_empty() || rest.starts_with("::"))
    })
}

fn python_level(level: Level) -> i32 {
    match level {
        Level::ERROR => 40,
        Level::WARN => 30,
        Level::INFO => 20,
        Level::DEBUG => 10,
        Level::TRACE => 5,
    }
}

fn filter_from_python(level: i32) -> LevelFilter {
    match level {
        ..=5 => LevelFilter::TRACE,
        6..=10 => LevelFilter::DEBUG,
        11..=20 => LevelFilter::INFO,
        21..=30 => LevelFilter::WARN,
        31..=50 => LevelFilter::ERROR,
        _ => LevelFilter::OFF,
    }
}

fn encode(filter: LevelFilter) -> u8 {
    FILTERS
        .iter()
        .position(|candidate| *candidate == filter)
        .and_then(|index| u8::try_from(index).ok())
        .unwrap_or_default()
}

fn decode(value: u8) -> LevelFilter {
    FILTERS
        .get(usize::from(value))
        .copied()
        .unwrap_or(LevelFilter::OFF)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn captured(message: &str) -> Captured {
        Captured {
            level: Level::INFO,
            target: "getstream::rtc".to_owned(),
            file: None,
            line: None,
            message: message.to_owned(),
            fields: Vec::new(),
            created_ns: 0,
        }
    }

    fn messages(records: &[Captured]) -> Vec<&str> {
        records
            .iter()
            .map(|record| record.message.as_str())
            .collect()
    }

    #[test]
    fn wrapper_records_use_the_sdk_level() {
        let sink = Sink::new();
        sink.set_filters(LevelFilter::DEBUG, LevelFilter::WARN);

        assert!(sink.enabled("_bindings::call", &Level::DEBUG));
        assert!(sink.enabled("getstream::rtc::join", &Level::DEBUG));
        assert!(!sink.enabled("webrtc_ice::agent", &Level::DEBUG));
    }

    #[test]
    fn a_marker_ends_the_batch() {
        let sink = Sink::new();
        sink.send(captured("before"));
        sink.sender
            .send(Message::Marker(7))
            .expect("room in the queue");
        sink.send(captured("after"));
        let receiver = sink.receiver.lock().expect("an unpoisoned lock");

        let (records, marker) = take_batch(&receiver).expect("a batch");
        assert_eq!(messages(&records), ["before"]);
        assert_eq!(marker, Some(7));

        let (records, marker) = take_batch(&receiver).expect("a batch");
        assert_eq!(messages(&records), ["after"]);
        assert_eq!(marker, None);
    }

    #[test]
    fn a_batch_holds_at_most_batch_size_records() {
        let sink = Sink::new();
        for _ in 0..=BATCH_SIZE {
            sink.send(captured("record"));
        }
        let receiver = sink.receiver.lock().expect("an unpoisoned lock");

        let (records, _) = take_batch(&receiver).expect("a batch");
        assert_eq!(records.len(), BATCH_SIZE);

        let (records, _) = take_batch(&receiver).expect("a batch");
        assert_eq!(records.len(), 1);
    }

    #[test]
    fn records_that_do_not_fit_are_counted() {
        let sink = Sink::new();
        for _ in 0..QUEUE_CAPACITY + 2 {
            sink.send(captured("record"));
        }

        assert_eq!(sink.dropped.load(Ordering::Relaxed), 2);
    }
}
