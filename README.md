# OWSF

Open Workspace Schema Framework (OWSF) defines a portable, append-only workspace artifact model for execution continuity, replay, handoff, and forking across tools.

## Scope

OWSF specifies artifact structure and invariants. It does not define runtime orchestration or transport protocols.

Normative core reference:

- `docs/spec/owsf-core-v0.1.md`

## Repository Layout

- `docs/spec/owsf-core-v0.1.md` - normative core specification
- `docs/governance/versioning-policy.md` - spec versioning and compatibility rules
- `docs/governance/release-checklist.md` - release checklist for tagged spec versions
- `docs/integration/clear.md` - integration notes for CLEAR and similar protocol consumers
- `schemas/owsf-core-v0.1.schema.json` - machine-readable core schema
- `examples/minimal-owsf.json` - minimal valid example payload

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
