# Changelog

All notable changes to OWSF will be documented in this file.

## [Unreleased]

### Added

- agent-loop payload profile v0.1: open event-type registry and per-type payload contracts for agent-domain events (`docs/profiles/`, `schemas/profiles/`), with CI-validated worked example.
- Bidirectional Claude Code session JSONL reference converter (`tools/convert_claude_jsonl.py`): lossless `payload.raw` capture, deterministic output, agent-loop profile payload fields; CI checks determinism and byte-identical round-trip.
- Integration note on crtx/stem layering (`docs/integration/stem-crtx.md`), including adapter concept mapping.
- Core: optional `dispatched_from` lineage metadata (spec Section 8 restructured as fork = continuation, dispatch = causation); semantic validator rejects self-referential lineage.
- agent-loop profile: `context.inject` event type (injection as event, preserving no-merge and self-contained replay) and optional `child_doc_id` on `tool.call`/`tool.result`.

- CI: examples validated against the core JSON Schema (draft 2020-12) via `check-jsonschema`.
- Semantic validator: `lamport` must be a non-negative integer per event.
- Semantic validator: `lamport` causal consistency — dependency `lamport` strictly less than dependent's; matching normative rule in spec Section 6 and release-checklist item.

### Changed

- Spec: event `writer_id` MUST reference a registered writer when `writers` is present (was SHOULD).
- Spec: document MUST contain exactly one root space.
- Spec: `seq` MUST be strictly increasing per `writer_id` (was ambiguous "monotonic").

### Fixed

- Schema: `integrity` object must be non-empty (`minProperties: 1`).
- CI: empty-`examples/` guard now fires (`nullglob`).

## [0.1.0] - 2026-03-04

### Added

- Initial repository scaffold and core specification draft (v0.1).
- Core JSON Schema for event and space definitions.
- Minimal OWSF implementation example.
- Governance policies including versioning and release checklists.
- CI validation workflow and semantic validation scripts.
