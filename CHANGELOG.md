# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Standardized error hierarchy ([CHA-2958](https://linear.app/stream/issue/CHA-2958)).
  New exception classes importable from `getstream` (also re-exported from
  `getstream.exceptions`):
    - `StreamException`: abstract base for every SDK error.
    - `StreamApiException`: any HTTP 4xx/5xx response. Carries `status_code`,
      `code`, `message`, `exception_fields`, `unrecoverable`,
      `raw_response_body`, `more_info`, `details`. The `unrecoverable` flag
      from `APIError` is now surfaced (was previously dropped on most paths).
    - `StreamRateLimitException`: subclass of `StreamApiException` raised on
      HTTP 429. Adds `retry_after: datetime.timedelta | None`, parsed from
      `Retry-After` per RFC 7231 (integer seconds or HTTP-date). Missing or
      unparseable headers map to `None`; past HTTP-dates clamp to `0`.
    - `StreamTransportException`: raised when a network-layer failure (no
      HTTP response received) propagates out of `httpx` — connection reset,
      timeout, TLS handshake failure, DNS failure. Carries `error_type`
      enum (`connection_reset` / `timeout` / `dns_failure` /
      `tls_handshake_failed` / `unknown`). The original `httpx` exception
      is preserved as `__cause__`.
    - `StreamTaskException`: raised by `wait_for_task` when the polled task
      ends in `status='failed'`. Carries `task_id`, `error_type`,
      `description`, `stack_trace`, `version`.
- `Stream.wait_for_task(task_id, *, poll_interval=1.0, timeout=60.0)` and
  the matching async coroutine on `AsyncStream`. Polls `get_task` until the
  task reaches a terminal state. On `completed` returns the
  `StreamResponse[GetTaskResponse]`; on `failed` raises
  `StreamTaskException` populated from `ErrorResult`; on timeout raises
  `StreamTransportException(error_type='timeout')`.

- Explicit HTTP connection pool configuration ([CHA-2956](https://linear.app/stream/issue/CHA-2956/connection-pooling)).
  Four new kwargs on `Stream(...)` and `AsyncStream(...)`:
    - `max_conns_per_host: int`: default `5`
    - `idle_timeout: float` (seconds): default `55.0`
    - `connect_timeout: float` (seconds): default `10.0`
    - `request_timeout: float` (seconds): default `30.0` (was `6.0`; see Behavior changes)

  These tune the underlying `httpx.Limits` and `httpx.Timeout`. The existing `http_client=` and `transport=` kwargs continue to act as escape hatches; when `http_client` is set, none of the four new kwargs apply. Env-var fallbacks for the new kwargs: `STREAM_MAX_CONNS_PER_HOST`, `STREAM_IDLE_TIMEOUT`, `STREAM_CONNECT_TIMEOUT`, `STREAM_REQUEST_TIMEOUT`.
- INFO log on client construction (logger `getstream`) lists the effective pool config and whether a user-supplied `http_client` is in use.

- Webhook handling spec helpers (CHA-2961): `UnknownEvent` dataclass for
  forward-compat; `gunzip_payload`, `decode_sqs_payload`, `decode_sns_payload`
  primitives; `parse_event` (returns typed event or `UnknownEvent` for
  unrecognized discriminators); `verify_signature` canonical alias of
  `verify_webhook_signature`; `verify_and_parse_webhook` HTTP composite
  (gunzip + verify + parse); `parse_sqs` and `parse_sns` queue composites
  (no signature parameter: queue transports are authenticated by AWS IAM,
  so the backend emits no HMAC for queue messages today). Transparent gzip
  via magic-byte detection.
- New instance methods on `Stream` and `AsyncStream`:
  `verify_signature(body, signature)` and
  `verify_and_parse_webhook(body, signature)` that drop the api_secret parameter
  in favor of the client's stored secret. Dual API: the module-level functions
  in `getstream.webhook` remain available for callers who want explicit
  secret control.
- New instance methods on `Stream` / `AsyncStream`: `parse_sqs(message_body)`,
  `parse_sns(notification_body)` (no signature; AWS IAM).
- `InvalidWebhookError` exception type covering both signature mismatches and
  malformed payloads. Distinguish failure modes via the exception message or
  `__cause__` chain.
- Conformance fixture suite under `tests/fixtures/webhooks/` (13 happy-path
  event directories + 8 negative cases) for SDK conformance testing across
  language ports.

### Changed

- HTTP request errors raised by `httpx` (the `httpx.RequestError` family —
  `ConnectError`, `ReadTimeout`, etc.) are now wrapped at the SDK boundary
  in `StreamTransportException` so callers handle one Stream error category
  instead of catching `httpx.RequestError` separately. The original `httpx`
  exception is preserved via `__cause__` (CHA-2958).
- **Default `request_timeout` is now `30.0` seconds (was `6.0`).** Aligns stream-py with the cross-SDK contract in CHA-2956. Existing callers using `timeout=` are unaffected; `timeout` is kept as an alias for `request_timeout`. Callers relying on the 6s ceiling for fail-fast behavior should pass `request_timeout=6.0` (or `timeout=6.0`) explicitly.
- Default HTTP transport now caps connections per host at `5` and closes idle sockets after `55.0s`. Previous default was httpx's `100` max-connections with `5.0s` keep-alive expiry.
- No breaking changes. All existing webhook helpers (`verify_webhook_signature`,
  `parse_webhook_event`, `get_event_type`, event type constants) are preserved.

### Deprecated

- `getstream.base.StreamAPIException` (capital `API`) is now an alias for
  `getstream.exceptions.StreamApiException` (lowercase `Api`). Importing the
  old name emits `DeprecationWarning`; existing `isinstance` / `except` /
  `pytest.raises` checks continue to work because the alias resolves to the
  same class. The legacy spelling will be removed one minor cycle after this
  release (CHA-2958 §10).

### Notes

- Per-call `timeout=httpx.Timeout(...)` continues to work through `.get(...)`, `.post(...)`, etc., and pre-empts the client-level `request_timeout`.

## [3.0.0b1] - 2026-02-27

### Breaking Changes

- Type names across all products now follow the OpenAPI spec naming convention: response types are suffixed with `Response`, input types with `Request`. See [MIGRATION_v2_to_v3.md](./MIGRATION_v2_to_v3.md) for the complete rename mapping.
- `Event` (WebSocket envelope type) renamed to `WSEvent`. Base event type renamed from `BaseEvent` to `Event` (with field `type` instead of `T`).
- Event composition changed from monolithic `*Preset` embeds to modular `Has*` types.
- `Pager` renamed to `PagerResponse` and migrated from offset-based to cursor-based pagination (`next`/`prev` tokens).
- Types that were previously `dict` or `TypedDict` (e.g., `User`, `Channel`, `Message`) are now full dataclasses with typed fields.

### Added

- Full product coverage: Chat, Video, Moderation, and Feeds APIs are all supported in a single SDK.
- **Feeds**: activities, feeds, feed groups, follows, comments, reactions, collections, bookmarks, membership levels, feed views, and more.
- **Video**: calls, recordings, transcription, closed captions, SFU, call statistics, user feedback analytics, and more.
- **Moderation**: flags, review queue, moderation rules, config, appeals, moderation logs, and more.
- Push notification types, preferences, and templates.
- Webhook support: `WHEvent` envelope class for receiving webhook payloads, utility functions for decoding and verifying webhook signatures, and a full set of individual typed event dataclasses for every event across all products (Chat, Video, Moderation, Feeds) usable as discriminated event types.
- Cursor-based pagination across all list endpoints.

## [2.7.1] - 2026-02-18

## [2.7.0] - 2026-02-03

## [2.6.0] - 2025-12-11

## [2.5.22] - 2025-10-15
