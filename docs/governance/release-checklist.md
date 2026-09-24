# OWSF Release Checklist

## Pre-Release

- [ ] Spec changes finalized in `specs/<version>/`
- [ ] Schema changes finalized in `specs/<version>/schemas/`
- [ ] Examples updated in `specs/<version>/examples/`
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
  - [ ] `lamport` causally consistent with `depends_on` (dependency `lamport` strictly less than dependent's)
  - [ ] `fork` / `dispatched_from` `parent_doc_id` differs from `doc_id`

## Release

- [ ] Version number updated where required
- [ ] Tag created (`owsf-<version>/vX.Y.Z`)
- [ ] Release notes published
