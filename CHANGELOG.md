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

- Structured logging ([CHA-2957](https://linear.app/stream/issue/CHA-2957)).
  New `logger: logging.Logger | None` and `log_bodies: bool = False` kwargs on
  `Stream(...)` and `AsyncStream(...)`. Off by default: nothing is emitted
  unless a logger is passed. Four events, each carrying structured fields via
  the stdlib logging `extra={}` mechanism:
    - `client.initialized` (INFO, once at construction): SDK name/version,
      resolved pool knobs, `gzip_enabled`, `user_http_client`, `log_bodies`.
      Replaces the old plain-text pool-config INFO line.
    - `http.request.sent` (DEBUG, before each request): method, path,
      redacted query, `stream.endpoint_name`.
    - `http.response.received` (DEBUG, after any response including
      4xx/5xx): status code, response size, `duration_ms`. HTTP error
      status codes are data, not failures.
    - `http.request.failed` (ERROR, transport failure only, no HTTP
      response received): `error.type` (`connection_reset` / `timeout` /
      `dns_failure` / `tls_handshake_failed` / `unknown`), `error.message`.
  Query values for `api_key`/`api_secret`/`token` and top-level JSON body
  keys `api_secret`/`token`/`password` are always redacted; no opt-out.
  Bodies are never logged by default; `log_bodies=True` adds redacted
  request/response bodies and emits one WARNING at construction.

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
- Regenerated from the latest chat OpenAPI spec. New endpoints: `moderation.analyze`,
  `moderation.bulk_action_appeals`, `moderation.get_setup_session`,
  `moderation.upsert_setup_session`; `feeds.get_or_create_follow`,
  `feeds.get_or_create_unfollow`, `feeds.get_user_interests`; `chat.create_segment`,
  `chat.update_segment`, `chat.add_segment_targets`; `common.cancel_import_v2_task`;
  `video.report_client_call_event`, together with the request/response models backing them.
- New webhook event types `moderation.image_analysis.complete` and
  `moderation.text_analysis.complete`, with `ModerationImageAnalysisCompleteEvent`
  and `ModerationTextAnalysisCompleteEvent` models.

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
- `FlagResponse` now represents the full flag record (`created_at`, `updated_at`,
  `target_message`, `target_user`, `user`, `reason`, `details`, `custom`, and related
  fields). The moderation flag-action acknowledgement, which carries `item_id` and
  `duration`, moved to the new `FlagItemResponse`; `moderation.flag()` now returns
  `FlagItemResponse`. The `/api/v2/moderation/flag` wire response is unchanged, so code
  reading `item_id`/`duration` off the parsed response is unaffected. Code referencing
  the `FlagResponse` type for those two fields should switch to `FlagItemResponse`.
- `ChannelInput.config_overrides` and `ChannelDataUpdate.config_overrides` are now typed
  as `ChannelConfigOverrides` (the override-specific field set) instead of `ChannelConfig`.
- `enabled` on `DeliveryReceiptsResponse`, `ReadReceiptsResponse`, and
  `TypingIndicatorsResponse` is now a required `bool` (was `Optional[bool]`).
- `LLMRule.description`, `TargetResolution.bitrate`, and `TranslationSettings.languages` /
  `TranslationSettings.enabled` are now optional.

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
