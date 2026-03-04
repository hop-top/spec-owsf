# OWSF Release Checklist

## Pre-Release

- [ ] Spec changes finalized in `docs/spec/`
- [ ] Schema changes finalized in `schemas/`
- [ ] Examples updated in `examples/`
- [ ] Compatibility impact assessed (`major` / `minor` / `patch`)
- [ ] Changelog entry added

## Validation

- [ ] Schema is valid JSON Schema
- [ ] Examples validate against current schema
- [ ] Normative language reviewed for ambiguity
- [ ] `scripts/validate_owsf_semantics.py` passes for release examples
- [ ] Semantic conformance checks pass:
  - [ ] unique `event_id` within document
  - [ ] monotonic `seq` per `writer_id`
  - [ ] strict-tree space topology (single parent, no cycles)
  - [ ] causal dependencies resolve and are acyclic

## Release

- [ ] Version number updated where required
- [ ] Tag created (`vX.Y.Z`)
- [ ] Release notes published
