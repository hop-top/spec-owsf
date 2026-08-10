# stem / crtx Integration Note

crtx is a cross-CLI session envelope format; stem is its runtime. Sessions
from agent CLIs normalize to crtx envelopes for interchange and resume.

OWSF and crtx occupy different layers:

- crtx normalizes session content across CLIs.
- OWSF specifies the durable workspace artifact: append-only history,
  deterministic replay ordering, fork lineage, space topology, and
  integrity metadata.

The recommended integration point is an adapter at the stem layer: stem
emits OWSF artifacts from crtx envelopes (and can ingest them back). One
mapping there inherits every CLI stem supports.

`tools/convert_claude_jsonl.py` is a standalone reference converter for a
single source format. It demonstrates lossless capture and agent-loop
profile conformance with no runtime dependency; it is not the integration
path for crtx-aware consumers.
