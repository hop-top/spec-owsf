# Contributing

## Principles

- Keep invariants explicit and testable.
- Keep normative text (`MUST`, `SHOULD`, `MAY`) precise.
- Keep schema and examples aligned with spec changes.
- Distinguish schema validity from semantic conformance (both matter).

## Pull Request Requirements

1. Describe the change and rationale.
2. Identify compatibility impact (`major`, `minor`, `patch`).
3. Update `schemas/` and `examples/` when behavior changes.
4. Update `CHANGELOG.md`.
5. Run `scripts/validate_owsf_semantics.py` on modified examples.

## Review Focus

- Determinism
- Replay safety
- Backward compatibility
- Clarity of normative language
