# OWSF Hooks Payload Profile v0.1

Status: Draft  
Normative keywords in this document use RFC 2119 semantics: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`.

This profile layers on the OWSF Core Specification v0.1 (`docs/spec/owsf-core-v0.1.md`). It alters no core requirement.

## 1. Purpose

Reactive machinery — hooks, handlers, guardrails — is runtime territory and an explicit OWSF core non-goal. What belongs in the artifact is the record: which hook fired, at which moment, triggered by what, deciding what. This profile defines portable payload semantics for those records. Replay reads what fired; it `MUST NOT` re-fire anything.

## 2. Profile Identifier and Versioning

- Profile identifier: `hooks`
- Profile version: `0.1`
- Machine-readable schema: `schemas/profiles/hooks-v0.1.schema.json`

Versioning follows `docs/governance/versioning-policy.md`. Adding optional payload fields or new registry types is a `MINOR` change; removing or re-typing a required payload field, or removing a registry type, is a `MAJOR` change.

## 3. Conformance and Composition

This is an **open** profile, with the same conformance model as the agent-loop profile:

- An artifact conforms to this profile if and only if every event whose `type` appears in the registry (Section 4) carries a `payload` valid against that type's payload schema (Section 5).
- Event types not in the registry `MAY` appear and are not constrained by this profile.
- Registered payloads are open objects: producers `MAY` include properties beyond those defined here, and consumers `MUST` ignore unknown payload properties.

Open profiles compose: an artifact `MAY` conform to several profiles at once, because each constrains only its own registered types. This profile registers only `hook.*` types; composed profiles `MUST` have disjoint registries. The worked example (Section 8) conforms to this profile and the agent-loop profile simultaneously.

## 4. Event Type Registry

| Type | Semantics |
|---|---|
| `hook.fired` | A hook ran: which hook, on which runtime event, deciding what. |
| `hook.config` | A full snapshot of the hook wiring registered at that moment. |
| `hook.error` | A hook handler failed. |

## 5. Payload Definitions

All fields not marked required are optional. Every payload additionally allows `raw` (Section 6).

### 5.1 `hook.fired`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `hook` | yes | string | Stable hook identifier. |
| `event` | no | string | Runtime event name the hook fired on. |
| `action` | no | string enum: `allow`, `warn`, `block`, `rewrite` | Handler decision. |
| `message` | no | string | Human-readable handler message. |

`hook` is required because a firing without an identity is uninterpretable. The trigger is not a payload field: the event envelope's `depends_on` `SHOULD` reference the triggering event, which makes trigger-before-firing a validated ordering invariant (core Section 6) rather than an annotation.

### 5.2 `hook.config`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `hooks` | yes | array of hook objects | Complete wiring registered at this moment. Each entry requires `hook` (string identifier); further fields (event matchers, configuration) are open. |

Each `hook.config` is a full snapshot, not a delta: during replay the latest `hook.config` in canonical order describes the wiring then in force. The snapshot is annotative — it records what was registered so auditors can answer "what could have fired?"; consumers `MUST NOT` execute it.

### 5.3 `hook.error`

| Field | Required | Type | Meaning |
|---|---|---|---|
| `hook` | yes | string | Hook whose handler failed. |
| `error` | yes | string | Failure description. |
| `event` | no | string | Runtime event name being handled when the failure occurred. |

Hook runtimes commonly fail open (a crashed handler lets the event proceed); a `hook.error` therefore records a gap in enforcement, which is exactly what an auditor needs surfaced.

## 6. The `raw` Property

Every registered payload schema allows an optional `raw` object: a verbatim passthrough of the source-format record a converter produced the event from, per the same contract as the agent-loop profile. Consumers `MUST NOT` require `raw`.

## 7. Relationship to nerv

This profile is protocol-neutral: any hooks runtime can produce conforming events. The reference hooks contract is nerv (`hop-top/poly-nerv`). Producers recording nerv activity `SHOULD` use nerv event registry names in `event` (e.g. `PreToolUse`, `PostToolUse`, `SessionStart`) and `SHOULD` map `action` from the nerv handler contract's decision vocabulary, which this profile's enum mirrors. Wiring shape inside `hook.config` entries `MAY` follow nerv's hook definition schema.

## 8. Schema Application

The profile schema is a single whole-document schema that constrains only `events[*].payload`, conditionally on `events[*].type` (one `if`/`then` branch per registry entry). It duplicates no core constraint and `MUST` be applied in addition to the core schema, alongside any other composed profile schemas.

## 9. Worked Example

`examples/hooks-owsf.json` records a guardrail in action: a `hook.config` snapshot, a `tool.call` (agent-loop type, untouched by this profile), a `hook.fired` with `action: block` depending on that call, the cancelled `tool.result`, and a `hook.error` from an unrelated fail-open handler. It is valid against the core schema, the semantic validator, this profile, and the agent-loop profile — demonstrating composition.
