# OWSF Core Specification v1.0

Status: Released  
Normative keywords in this document use RFC 2119 semantics: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`.

## 1. Purpose

OWSF defines a portable workspace artifact model with:

- append-only history
- deterministic replay ordering
- explicit fork lineage
- optional multi-writer timelines

The objective is interoperability of execution context artifacts across tools. OWSF is designed to **complement** and **augment** existing standards like OCSF (for event semantics) and OASF (for agent identity) by providing the stateful, deterministic glue between them.

## 2. Non-Goals

OWSF does not define:

- runtime orchestration
- transport/session protocols
- tool negotiation semantics
- merge semantics or CRDT convergence rules

## 3. Core Document Model

An OWSF core document `MUST` include:

- `owsf_version`
- `doc_id`
- `created_at`
- `producer`
- `spaces`
- `events`

Optional top-level fields:

- `fork`
- `dispatched_from`
- `writers`
- `export`
- `integrity`

If `writers` is present, every event `writer_id` `MUST` reference a registered writer entry.

### 3.1 Required Field Semantics

- `owsf_version`: version string identifying the OWSF core contract used by this artifact.
- `doc_id`: globally unique artifact identifier.
- `created_at`: RFC3339 timestamp (`Z`/UTC preferred).
- `producer`: emitting tool identity and version.
- `spaces`: immutable space topology descriptors.
- `events`: append-only interaction/mutation timeline.
- `writer_id`: SHOULD be a URI resolvable via OASF Agent Record protocols.

## 4. Space Model

A space is a bounded execution environment.

Each `space` `MUST` define:

- `id`
- `type`
- `parent` (`null` for root)
- `boundary`
- `capabilities`
- `trust_level`

### 4.1 Space Invariants

- Space containment `MUST` form a strict tree (single parent per node).
- A document `MUST` contain exactly one root space (`parent: null`).
- `space.id`, `space.parent`, and `space.type` are immutable after creation.
- Reparenting is prohibited. If topology changes materially, a new space must be introduced via events.
- `boundary`: SHOULD be defined using OCSF Observable types (e.g., `file_path`, `process_id`, `container_id`) where applicable.
- `capabilities`: SHOULD use taxonomy defined in OASF Skill and Domain annotations.

Note: tree/cycle checks are semantic validations and cannot be fully guaranteed by JSON Schema alone.

## 5. Event Model

Each event `MUST` include:

- `event_id`
- `writer_id`
- `space_id`
- `type`
- `lamport`
- `seq`
- `timestamp`
- `payload`

Optional:

- `depends_on` (causal dependencies)
- `meta`

### 5.1 Event Invariants

- Event log is append-only.
- Historical events `MUST NOT` be edited or removed.
- `event_id` must be unique within document.
- `seq` `MUST` be strictly increasing per `writer_id`.
- `payload`: SHOULD utilize OCSF Event Class definitions for system-level activities (File, Network, Process, Registry) to ensure semantic interoperability.

## 6. Deterministic Ordering

Consumers `MUST` compute canonical order deterministically from identical input:

1. Respect explicit causal dependencies (`depends_on`) where present.
2. Sort by `lamport` ascending.
3. Tie-break by `writer_id` lexicographically.
4. Tie-break by `seq` ascending.
5. Tie-break by `event_id` lexicographically.

If causal references are invalid (missing, cyclic, or lamport-inconsistent), consumers `MUST` fail validation before replay. A causal reference is lamport-inconsistent when an event listed in `depends_on` does not have a `lamport` strictly less than the dependent event's `lamport`.

## 7. Replay Contract

Given identical OWSF input and identical ordering algorithm, replay `MUST` produce identical derived state.

OWSF replay `MUST NOT` require hidden external state.

## 8. Lineage: Fork, Dispatch, and No-Merge Invariant

Core defines two optional, single-valued lineage edges. Both are pure
provenance metadata: they `MUST NOT` affect replay, and consumers `MUST NOT`
require the referenced parent document to replay this document.

### 8.1 Fork (continuation)

Forking is allowed via optional `fork` metadata:

- single parent only
- explicit `parent_doc_id`
- explicit `parent_event_id`

A fork continues the parent's history: events up to `parent_event_id` are a
shared prefix.

### 8.2 Dispatch (causation)

A document `MAY` declare optional `dispatched_from` metadata:

- explicit `parent_doc_id` (the dispatching document)
- explicit `parent_event_id` (the event, typically a tool call, that spawned this document)

Dispatch records causation, not continuation: the child history is fresh and
shares no prefix with the parent. `dispatched_from.parent_doc_id` `MUST NOT`
equal the document's own `doc_id`. `fork` and `dispatched_from` are
independent and `MAY` both be present.

### 8.3 No-Merge Invariant

Core OWSF prohibits merge semantics:

- multi-parent history lineage is invalid (`fork` is single-valued)
- merged histories are out of scope
- dispatch edges record provenance only; they do not compose histories

## 9. Export Profiles

`export.kind` may be:

- `full`
- `partial`

If `partial`, producer `MUST` declare:

- scope basis
- dependency omissions
- determinism level (`full`, `best_effort`, `none`)

Consumers `MUST NOT` assume omitted dependencies are available.

## 10. Integrity and Provenance Metadata

OWSF supports optional layered integrity metadata:

- `manifest_hash`
- `signature`
- provenance references

These fields improve trust but do not change replay semantics.

## 11. Conformance Responsibilities

Implementations should run two validation phases:

1. Schema validation (shape/type validation)
2. Semantic validation (tree integrity, uniqueness, monotonicity, causal validity)

Schema pass alone does not imply full conformance.

## 12. Versioning and Compatibility

Versioning policy is defined in:

- `../../docs/governance/versioning-policy.md`

## 13. Framework Interoperability (OCSF & OASF)

OWSF acts as the stateful timeline that binds agent identity (OASF) with event semantics (OCSF).

### 13.1 OASF (Agent Identity)
- **Identity:** `writer_id` SHOULD be a URI resolvable to an OASF Agent Record.
- **Capabilities:** `space.capabilities` SHOULD use the taxonomy defined in OASF Skill and Domain annotations to ensure agent-to-environment capability matching.

### 13.2 OCSF (Event Semantics)
- **Payloads:** For events involving system activity (e.g., filesystem, network, process), the `payload` SHOULD follow the OCSF Event Class structure for that activity.
- **Observables:** `space.boundary` definitions SHOULD map to OCSF Observable types to enable unified security and observability across tools.
