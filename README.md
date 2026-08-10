# OWSF

Open Workspace Schema Framework (OWSF) defines a portable, append-only workspace artifact model for execution continuity, replay, handoff, and forking across tools.

## Scope

OWSF specifies artifact structure and invariants. It does not define runtime orchestration or transport protocols.

Normative core reference:

- `docs/spec/owsf-core-v0.1.md`

## Repository Layout

- `docs/spec/owsf-core-v0.1.md` - normative core specification
- `docs/profiles/agent-loop-v0.1.md` - agent-loop payload profile (agent-domain event semantics)
- `docs/profiles/hooks-v0.1.md` - hooks payload profile (hook firings, wiring snapshots, handler failures)
- `docs/governance/versioning-policy.md` - spec versioning and compatibility rules
- `docs/governance/release-checklist.md` - release checklist for tagged spec versions
- `docs/integration/clear.md` - integration notes for CLEAR and similar protocol consumers
- `docs/integration/stem-crtx.md` - layering vs the crtx session envelope format and its stem runtime
- `schemas/owsf-core-v0.1.schema.json` - machine-readable core schema
- `schemas/profiles/agent-loop-v0.1.schema.json` - agent-loop profile payload schema
- `schemas/profiles/hooks-v0.1.schema.json` - hooks profile payload schema
- `examples/minimal-owsf.json` - minimal valid example payload
- `examples/agent-loop-owsf.json` - worked agent-loop profile example
- `examples/hooks-owsf.json` - worked hooks profile example (composed with agent-loop)
- `examples/claude-code-session-owsf.json` - converter output for the synthetic session fixture
- `tools/convert_claude_jsonl.py` - bidirectional Claude Code session JSONL reference converter

## Status

- Version line: `v0.1`
- Maturity: draft

## Release Model

1. Update spec and schema together.
2. Run schema and semantic validation.
   `jq . schemas/owsf-core-v0.1.schema.json >/dev/null`
   `jq . examples/minimal-owsf.json >/dev/null`
   `scripts/validate_owsf_semantics.py examples/minimal-owsf.json`
3. Tag release (`vX.Y.Z`) after checklist completion.

## Contributing

See `CONTRIBUTING.md`.
