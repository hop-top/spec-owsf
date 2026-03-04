# OWSF Versioning Policy

## Version Scheme

OWSF uses semantic versioning for published artifacts and schemas:

- `MAJOR`: Breaking normative or schema changes
- `MINOR`: Backward-compatible additions/clarifications
- `PATCH`: Editorial fixes, typo fixes, non-semantic corrections

## Compatibility Rules

- Consumers MUST reject unknown major versions by default.
- Consumers MAY accept newer minor versions if required fields remain compatible.
- Producers SHOULD include explicit `owsf_version` in every artifact.
- Schema validation and semantic validation are both required for conformance.

## Change Classification

Breaking examples:

- Removing required fields
- Changing field semantics incompatibly
- Altering ordering rules incompatibly

Non-breaking examples:

- Adding optional fields
- Adding profile-level extensions
- Clarifying ambiguous language without semantic change

## Release Coupling

For every spec release:

- `docs/spec/` and `schemas/` MUST be updated together when normative behavior changes.
- `examples/` MUST include at least one valid artifact for the released schema.
- If schema and spec diverge, release is blocked.
