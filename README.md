# OWSF

Open Workspace Schema Framework (OWSF) defines a portable, append-only workspace artifact model for execution continuity, replay, handoff, and forking across tools.

## Scope

OWSF specifies artifact structure and invariants. It does not define runtime orchestration or transport protocols.

Normative core reference:

- `specs/v1.0/core.md`

## Repository Layout

The versioned spec surface lives under `specs/<version>/`; everything outside it
is unversioned tooling and governance.

- `specs/v1.0/core.md` - normative core specification
- `specs/v1.0/profiles/agent-loop.md` - agent-loop payload profile (agent-domain event semantics)
- `specs/v1.0/profiles/hooks.md` - hooks payload profile (hook firings, wiring snapshots, handler failures)
- `specs/v1.0/schemas/core.schema.json` - machine-readable core schema
- `specs/v1.0/schemas/profiles/agent-loop.schema.json` - agent-loop profile payload schema
- `specs/v1.0/schemas/profiles/hooks.schema.json` - hooks profile payload schema
- `specs/v1.0/examples/minimal-owsf.json` - minimal valid example payload
- `specs/v1.0/examples/agent-loop-owsf.json` - worked agent-loop profile example
- `specs/v1.0/examples/hooks-owsf.json` - worked hooks profile example (composed with agent-loop)
- `specs/v1.0/examples/claude-code-session-owsf.json` - converter output for the synthetic session fixture
- `docs/governance/versioning-policy.md` - spec versioning and compatibility rules
- `docs/governance/release-checklist.md` - release checklist for tagged spec versions
- `docs/integration/clear.md` - integration notes for CLEAR and similar protocol consumers
- `docs/integration/stem-crtx.md` - layering vs the crtx session envelope format and its stem runtime
- `tools/convert_claude_jsonl.py` - bidirectional Claude Code session JSONL reference converter

## Status

- Version line: `v1.0`
- Maturity: released

## Release Model

1. Update spec and schema together.
2. Run schema and semantic validation.
   `jq . specs/v1.0/schemas/core.schema.json >/dev/null`
   `jq . specs/v1.0/examples/minimal-owsf.json >/dev/null`
   `scripts/validate_owsf_semantics.py specs/v1.0/examples/minimal-owsf.json`
3. Tag release (`owsf-v1.0/vX.Y.Z`) after checklist completion.

## Contributing

See `CONTRIBUTING.md`.
