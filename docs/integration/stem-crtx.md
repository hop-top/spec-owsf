# stem / crtx Integration Note

crtx (<https://hop.top/crtx>) is a cross-CLI session envelope format; stem
(<https://hop.top/stem>) is its runtime. Sessions from agent CLIs normalize to
crtx envelopes for interchange and resume.

OWSF and crtx occupy different layers:

- crtx normalizes session content across CLIs.
- OWSF specifies the durable workspace artifact: append-only history,
  deterministic replay ordering, fork lineage, space topology, and
  integrity metadata.

The recommended integration point is an adapter at the stem layer: stem
emits OWSF artifacts from crtx envelopes (and can ingest them back). One
mapping there inherits every CLI stem supports.

Concept mapping for an adapter:

- crtx session identity/source → `doc_id` / `producer`
- crtx `parent_id` + `fork_point` → `fork`
- crtx `dispatched_from` → `dispatched_from` (core Section 8.2); child
  envelope references on tool results → `child_doc_id` (agent-loop profile)
- crtx injected turn ranges → `context.inject` events (agent-loop profile):
  OWSF records injection as an event with materialized content, never as
  structural splicing
- crtx turn position → `lamport` / `seq`; content parts → agent-loop payloads

`tools/convert_claude_jsonl.py` is a standalone reference converter for a
single source format. It demonstrates lossless capture and agent-loop
profile conformance with no runtime dependency; it is not the integration
path for crtx-aware consumers.
