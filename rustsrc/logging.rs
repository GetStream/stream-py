//! Forwards Rust log records to Python `logging`.
//!
//! The SDK emits `tracing` events and third-party crates emit `log` records
//! (routed into `tracing` by `LogTracer`). Threads that log only put records
//! into a bounded queue; one forwarding thread, which holds no SDK locks, takes
//! the GIL and calls Python. A thread that logs never waits for the GIL, so a
//! Python thread that holds the GIL and waits for an SDK lock cannot deadlock
//! with it.

use std::error::Error as StdError;
use std::fmt;
use std::sync::OnceLock;
use std::sync::atomic::{AtomicU8, AtomicU64, Ordering};
use std::sync::mpsc::{Receiver, SyncSender, sync_channel};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use tracing::field::{Field, Visit};
use tracing::level_filters::LevelFilter;
use tracing::{Event, Level, Metadata, Subscriber};
use tracing_log::{AsLog, NormalizeEvent};
use tracing_subscriber::layer::{Context, Layer, SubscriberExt};

const QUEUE_CAPACITY: usize = 1024;
const SDK_CRATE: &str = "getstream";
const PYTHON_WARNING: i32 = 30;
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
    dropped: AtomicU64,
    sdk_filter: AtomicU8,
    third_party_filter: AtomicU8,
}

enum Message {
    Record(Box<Captured>),
    Dropped(u64),
    Configure {
        logger: Option<Py<PyAny>>,
        done: SyncSender<()>,
    },
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
        let dropped = self.dropped.swap(0, Ordering::Relaxed);
        if dropped > 0 && self.sender.try_send(Message::Dropped(dropped)).is_err() {
            self.dropped.fetch_add(dropped, Ordering::Relaxed);
        }
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

/// Installs the `tracing` subscriber, `LogTracer` and the forwarding thread.
/// Nothing is forwarded until `configure_logging` sets a logger.
pub fn install(module: &Bound<'_, PyModule>) -> PyResult<()> {
    let (sender, receiver) = sync_channel(QUEUE_CAPACITY);
    let sink = Sink {
        sender,
        dropped: AtomicU64::new(0),
        sdk_filter: AtomicU8::new(encode(LevelFilter::OFF)),
        third_party_filter: AtomicU8::new(encode(LevelFilter::OFF)),
    };
    if SINK.set(sink).is_err() {
        return Ok(());
    }
    thread::Builder::new()
        .name("getstream-logging".to_owned())
        .spawn(move || forward(receiver))
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    tracing::subscriber::set_global_default(tracing_subscriber::registry().with(ForwardingLayer))
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    tracing_log::LogTracer::builder()
        .with_max_level(log::LevelFilter::Off)
        .init()
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    // The forwarding thread must not call into Python after finalization.
    let py = module.py();
    py.import("atexit")?.call_method1(
        "register",
        (module.getattr("configure_logging")?, py.None(), 0),
    )?;
    Ok(())
}

/// Sends SDK records at `level` or above, and third-party records at the less
/// verbose of `level` and `third_party_level`, to `logger` and the loggers
/// below it. `logger=None` stops forwarding. Returns after the records queued
/// before the call have been delivered.
#[pyfunction]
#[pyo3(signature = (logger, level, third_party_level = PYTHON_WARNING))]
pub fn configure_logging(
    py: Python<'_>,
    logger: Option<Py<PyAny>>,
    level: i32,
    third_party_level: i32,
) {
    let sink = SINK.get().expect("installed when the module is imported");
    let enable = logger.is_some();
    let sdk = if enable {
        filter_from_python(level)
    } else {
        LevelFilter::OFF
    };
    let third_party = if enable {
        sdk.min(filter_from_python(third_party_level))
    } else {
        LevelFilter::OFF
    };
    // GIL released: the forwarding thread may be waiting for the GIL.
    py.detach(|| {
        if !enable {
            sink.set_filters(sdk, third_party);
        }
        let (done, delivered) = sync_channel(1);
        if sink
            .sender
            .send(Message::Configure { logger, done })
            .is_ok()
        {
            // Err only if the forwarding thread has stopped.
            let _ = delivered.recv();
        }
        if enable {
            sink.set_filters(sdk, third_party);
        }
        tracing::callsite::rebuild_interest_cache();
        log::set_max_level(sdk.max(third_party).as_log());
    });
}

fn forward(receiver: Receiver<Message>) {
    let mut logger: Option<Py<PyAny>> = None;
    for message in receiver {
        match message {
            Message::Configure { logger: next, done } => {
                logger = next;
                // Err only if the caller that waits for it is gone.
                let _ = done.send(());
            }
            Message::Record(record) => {
                if let Some(logger) = &logger {
                    Python::attach(|py| report(py, deliver(logger.bind(py), *record)));
                }
            }
            Message::Dropped(dropped) => {
                if let Some(logger) = &logger {
                    Python::attach(|py| report(py, deliver_dropped(logger.bind(py), dropped)));
                }
            }
        }
    }
}

fn report(py: Python<'_>, result: PyResult<()>) {
    if let Err(error) = result {
        error.write_unraisable(py, None);
    }
}

/// `getstream._native_logging.handle_record` builds and handles the Python
/// record.
fn deliver(logger: &Bound<'_, PyAny>, record: Captured) -> PyResult<()> {
    let py = logger.py();
    let fields = PyDict::new(py);
    for (name, value) in record.fields {
        fields.set_item(name.replace('.', "_"), value.into_python(py)?)?;
    }
    py.import("getstream._native_logging")?.call_method1(
        "handle_record",
        (
            logger,
            logger_name(&record.target),
            python_level(record.level),
            record.file.unwrap_or_default(),
            record.line.unwrap_or_default(),
            record.message,
            record.created_ns,
            record.target,
            fields,
        ),
    )?;
    Ok(())
}

fn deliver_dropped(logger: &Bound<'_, PyAny>, dropped: u64) -> PyResult<()> {
    let py = logger.py();
    let extra = PyDict::new(py);
    extra.set_item("dropped", dropped)?;
    let kwargs = PyDict::new(py);
    kwargs.set_item("extra", extra)?;
    logger.call_method("warning", ("native.log_records_dropped",), Some(&kwargs))?;
    Ok(())
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
    target
        .strip_prefix(SDK_CRATE)
        .is_some_and(|rest| rest.is_empty() || rest.starts_with("::"))
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
