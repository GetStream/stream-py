"""Turns records forwarded by ``getstream._rust`` into Python log records."""

import logging


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
