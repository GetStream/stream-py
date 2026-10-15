"""Hands the records that Rust queues to Python `logging`.

Rust only queues records. The thread `getstream-logging` takes them with
`_bindings._next_logs()`, which waits without the GIL, and hands them to the
configured logger. Rust never calls Python to log.
"""

import atexit
import itertools
import logging
import os
import threading
import traceback

from getstream_rtc import _bindings

_lock = threading.Lock()
_logger: logging.Logger | None = None
_thread: threading.Thread | None = None
# The process that started `_thread`. A child of fork() has no `_thread`. It
# changes only once, from `None`, so it is read without `_lock`: a child forked
# while `_lock` was held cannot take it.
_pid: int | None = None
_stop_marker: int | None = None
_markers: dict[int, threading.Event] = {}
_marker_ids = itertools.count()


def configure_logging(
    logger: logging.Logger | None,
    level: int,
    third_party_level: int = logging.WARNING,
) -> None:
    """Send SDK records at `level` or above, and records of third-party Rust
    crates at the less verbose of `level` and `third_party_level`, to `logger`
    and the loggers below it. `logger=None` stops forwarding. Process-wide: the
    last call wins. Returns at once: the thread `getstream-logging` delivers
    the records.

    Raises `RuntimeError` for a `logger` in a process forked after the logging
    was configured: the child has no thread of the parent. Configure the
    logging and use `getstream_rtc` only after fork()."""
    global _logger, _thread, _pid
    if _pid is not None and _pid != os.getpid():
        if logger is None:
            return
        raise RuntimeError(
            "the logging of getstream_rtc was configured before this process "
            "was forked: configure the logging and use getstream_rtc only "
            "after fork()"
        )
    with _lock:
        if _stop_marker is not None:
            return
        _bindings._set_log_filters(None if logger is None else level, third_party_level)
        _logger = logger
        if logger is not None and (_thread is None or not _thread.is_alive()):
            _thread = threading.Thread(
                target=_forward, name="getstream-logging", daemon=True
            )
            _thread.start()
            _pid = os.getpid()


def handle_record(
    base: logging.Logger,
    name: str | None,
    level: int,
    pathname: str,
    lineno: int,
    msg: str,
    created_ns: int,
    rust_target: str,
    fields: dict[str, object],
) -> None:
    logger = base.getChild(name) if name else base
    if not logger.isEnabledFor(level):
        return
    record = logger.makeRecord(logger.name, level, pathname, lineno, msg, (), None)
    for key, value in fields.items():
        setattr(record, f"rust_{key}" if hasattr(record, key) else key, value)
    record.rust_target = rust_target
    # The time of the Rust event, not of this call. LogRecord derives msecs
    # and relativeCreated from the same clock reading as created.
    created = created_ns / 1e9
    record.relativeCreated -= (record.created - created) * 1000
    record.created = created
    record.msecs = (created_ns % 1_000_000_000) // 1_000_000 + 0.0
    logger.handle(record)


def _forward() -> None:
    while True:
        dropped, records, marker = _bindings._next_logs()
        logger = _logger
        if logger is not None:
            # An error of one record is printed, as `logging.Handler.handleError`
            # does, and the thread goes on: a `_flush()` that waits for a
            # marker in the queue needs it.
            if dropped:
                try:
                    logger.warning(
                        "stream.rust.log_records_dropped", extra={"dropped": dropped}
                    )
                except Exception:
                    traceback.print_exc()
            for record in records:
                try:
                    handle_record(logger, *record)
                except Exception:
                    traceback.print_exc()
        if marker is not None:
            _markers.pop(marker).set()
            if marker == _stop_marker:
                return


def _flush() -> None:
    """Return after the records queued before this call are handled.

    Returns at once on the thread `getstream-logging` itself, when that thread
    does not run or is stopping, and in a child of fork(). Do not call it on a
    thread that a handler waits for, for example the event loop that a handler
    runs coroutines on: use `await asyncio.to_thread(_flush)` there.
    """
    if _pid != os.getpid():
        return
    with _lock:
        thread = _thread
        if (
            thread is None
            or not thread.is_alive()
            or _stop_marker is not None
            or threading.current_thread() is thread
        ):
            return
        marker = next(_marker_ids)
        event = _markers[marker] = threading.Event()
    _bindings._push_log_marker(marker)
    event.wait()


def _stop() -> None:
    """At exit, hand the queued records to the logger and stop the thread, so
    it does not call Python while the interpreter finalizes."""
    global _logger, _stop_marker
    if _pid != os.getpid():
        return
    with _lock:
        thread = _thread
        if thread is None or not thread.is_alive() or _stop_marker is not None:
            return
        _bindings._set_log_filters(None, logging.WARNING)
        _stop_marker = marker = next(_marker_ids)
        _markers[marker] = threading.Event()
    _bindings._push_log_marker(marker)
    thread.join()
    _logger = None


# Registered after `logging` registers `logging.shutdown`, so it runs first,
# while the handlers are still open.
atexit.register(_stop)
