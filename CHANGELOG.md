# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
