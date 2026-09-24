# Changelog

All notable changes to OWSF will be documented in this file.

## [1.0.0] - unreleased

First public release. OWSF was developed privately under a `v0.1` working
label; `v1.0` is the initial published spec version and no `0.1` artifact
population exists. The `owsf_version` contract value is `1.0`.

### Added

- agent-loop payload profile v1.0: open event-type registry and per-type payload contracts for agent-domain events (`specs/v1.0/profiles/`, `specs/v1.0/schemas/profiles/`), with CI-validated worked example.
- Bidirectional Claude Code session JSONL reference converter (`tools/convert_claude_jsonl.py`): lossless `payload.raw` capture, deterministic output, agent-loop profile payload fields; CI checks determinism and byte-identical round-trip.
- Integration notes: crtx/stem layering (`docs/integration/stem-crtx.md`) with adapter concept mapping, and CLEAR workspace-context profile (`docs/integration/clear.md`).
- Core: optional `dispatched_from` lineage metadata (spec Section 8 restructured as fork = continuation, dispatch = causation); semantic validator rejects self-referential lineage.
- agent-loop profile: `context.inject` event type (injection as event, preserving no-merge and self-contained replay) and optional `child_doc_id` on `tool.call`/`tool.result`.
- hooks payload profile v1.0 (`specs/v1.0/profiles/hooks.md`, `specs/v1.0/schemas/profiles/`): `hook.fired`/`hook.config`/`hook.error` records aligned with the nerv hooks contract; worked example demonstrating open-profile composition with agent-loop.

- CI: examples validated against the core JSON Schema (draft 2020-12) via `check-jsonschema`.
- Semantic validator: `lamport` must be a non-negative integer per event.
- Semantic validator: `lamport` causal consistency — dependency `lamport` strictly less than dependent's; matching normative rule in spec Section 6 and release-checklist item.

### Changed

- Spec: event `writer_id` MUST reference a registered writer when `writers` is present (was SHOULD).
- Spec: document MUST contain exactly one root space.
- Spec: `seq` MUST be strictly increasing per `writer_id` (was ambiguous "monotonic").

### Fixed

- Schema: `integrity` object must be non-empty (`minProperties: 1`).
- CI: empty-examples guard now fires (`nullglob`).

### Foundation

Carried forward from the private working phase, first published here:

- Core specification and JSON Schema for event and space definitions.
- Minimal OWSF example artifact.
- Governance policies: versioning and release checklists.
- CI validation workflow and semantic validation script.
