# OWSF Agent-Loop Payload Profile v0.1

Status: Draft  
Normative keywords in this document use RFC 2119 semantics: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`.

This profile layers on the OWSF Core Specification v0.1 (`docs/spec/owsf-core-v0.1.md`). It alters no core requirement.

## 1. Purpose

OWSF core leaves `events[*].payload` unconstrained: artifacts replay deterministically, but consumers cannot interpret agent activity portably. This profile defines payload semantics for the agent interaction loop — sessions, model turns, tool invocations, plans, and context compaction — the event domain OCSF has no classes for.

## 2. Profile Identifier and Versioning

- Profile identifier: `agent-loop`
- Profile version: `0.1`
- Machine-readable schema: `schemas/profiles/agent-loop-v0.1.schema.json`

Versioning follows `docs/governance/versioning-policy.md`. Adding optional payload fields or new registry types is a `MINOR` change; removing or re-typing a required payload field, or removing a registry type, is a `MAJOR` change.

Core v0.1 documents are closed at the top level, so this profile defines no in-document declaration field. Profile application is an out-of-band contract between producer and consumer.

## 3. Conformance

This is an **open** profile.

- An artifact conforms to this profile if and only if every event whose `type` appears in the registry (Section 4) carries a `payload` valid against that type's payload schema (Section 5).
- Event types not in the registry `MAY` appear in a conforming artifact and are not constrained by this profile.
- Registered payloads are open objects: producers `MAY` include properties beyond those defined here, and consumers `MUST` ignore unknown payload properties.
- Profile validation is applied in addition to core schema validation and core semantic validation. Passing this profile alone implies nothing about core conformance.

## 4. Event Type Registry

| Type | Semantics |
|---|---|
| `session.start` | An agent session begins; carries session identity and metadata. |
| `session.end` | The session terminates; carries the end reason. |
| `message.user` | A user-authored turn. |
| `message.assistant` | A model-authored turn with textual output. |
| `message.system` | A system- or tooling-injected instruction or notice. |
| `tool.call` | The agent invokes a named tool. |
| `tool.result` | The outcome of a prior tool invocation. |
| `plan.update` | A full snapshot of the agent's current plan. |
| `context.summary` | A compaction summary standing in for a range of prior events. |
| `topology.space_create` | A space came into existence (root or child). |

## 5. Payload Definitions

All fields not marked required are optional. Every payload additionally allows `raw` (Section 6).

### 5.1 `session.start`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `session_id` | yes | string | Stable session identifier. |
| `title` | no | string | Human-readable session title. |
| `model` | no | string | Default model identity for the session. |

`session_id` is required because it is the only join key correlating session events across forks and partial exports.

### 5.2 `session.end`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `reason` | yes | string | Why the session terminated. |
| `session_id` | no | string | Session being ended. |

`reason` is required so replay consumers can distinguish completed sessions from aborted or truncated ones. Values are free-form; `completed`, `user_abort`, `error`, and `limit` are `RECOMMENDED`.

### 5.3 `message.user`, `message.assistant`, `message.system`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `content` | yes | string | Turn text. |
| `model` | no (`message.assistant` only) | string | Model that produced the turn. |
| `stop_reason` | no (`message.assistant` only) | string | Why generation stopped. |

`content` is required because a message event without content is not replayable. Structured or multimodal source content belongs in `raw`; `content` carries its text projection. Assistant turns that only invoke tools are represented as `tool.call` events; `message.assistant` is emitted only when there is textual output.

### 5.4 `tool.call`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `tool` | yes | string | Tool name. |
| `arguments` | no | object | Tool arguments. |
| `call_id` | no | string | Correlation id matched by `tool.result`. |

`tool` is required because an invocation without a tool name is uninterpretable. `arguments` is optional: some tools take none.

### 5.5 `tool.result`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `status` | yes | string enum: `success`, `error`, `timeout`, `cancelled` | Invocation outcome. |
| `output` | no | any | Tool output. |
| `call_id` | no | string | Correlation id of the originating `tool.call`. |

`status` is required so consumers can replay control flow without parsing `output`.

### 5.6 `plan.update`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `steps` | yes | array of step objects | Complete current plan. |

Each step object requires `title` (string) and `status` (string enum: `pending`, `in_progress`, `completed`, `skipped`). Each `plan.update` is a full snapshot, not a delta: during replay the latest `plan.update` in canonical order is the current plan. `steps` and per-step `status` are required because a plan without step states carries no replayable state.

### 5.7 `context.summary`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `summary` | yes | string | Summary text. |
| `covers` | no | object | Range summarized: `from_event_id` and `to_event_id` (both required strings when present), inclusive, in canonical order (core Section 6). |

`covers` is `OPTIONAL`: many source formats do not record the summarized range, and producers `MUST NOT` fabricate one. Producers `SHOULD` emit `covers` when the range is known. A summary without `covers` is annotative only and `MUST NOT` substitute for the summarized events during replay; when `covers` is present, consumers `MAY` treat the summary as standing in for that range. Consumers `SHOULD` verify the referenced events exist; JSON Schema cannot.

### 5.8 `topology.space_create`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `space_id` | no | string | Id of the created space. |
| `note` | no | string | Free-form annotation. |

No field is required: the created space's identity is already carried by the event envelope's `space_id` (core Section 5). When `payload.space_id` is present it `MUST` equal the envelope `space_id`.

## 6. The `raw` Property

Every registered payload schema allows an optional `raw` object: a verbatim passthrough of the source-format record a converter produced the event from. Producers converting from a native format `SHOULD` preserve the unmodified source record in `raw`. Consumers `MUST NOT` require `raw`. This profile assigns `raw` no semantics beyond preservation.

## 7. Relationship to OCSF

Agent-loop events are outside OCSF scope by design: OCSF classifies system activity (file, network, process, registry), not model turns, tool invocations, or plans. Payloads for system-activity events `SHOULD` continue to use OCSF Event Classes per core Section 13.2; this registry deliberately excludes them. `topology.space_create` is included because space topology is an OWSF-native concern, not an OCSF one.

## 8. Schema Application

The profile schema is a single whole-document schema that constrains only `events[*].payload`, conditionally on `events[*].type` (one `if`/`then` branch per registry entry). It duplicates no core constraint and `MUST` be applied in addition to the core schema. Full conformance requires all three phases: core schema validation, core semantic validation, profile schema validation.

## 9. Worked Example

`examples/agent-loop-owsf.json` records a complete loop — `session.start`, a user/assistant exchange, a tool call and result, a plan update, a context summary, `session.end` — plus the root `topology.space_create` event. It is valid against the core schema, the semantic validator, and this profile.
