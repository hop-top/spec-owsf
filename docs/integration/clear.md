# CLEAR Integration Note

This note describes one integration profile where a CLEAR contract includes workspace context in `input_payload` (optional at protocol level, template-dependent in practice):

- `workspace` (opaque identifier), or
- `workspace_ref` (resolvable reference)

For WSM-backed flows, one profile is:

- `workspace_ref = "wsm://workspace/<workspace_id>"`

OWSF artifacts provide execution context and replay lineage. CLEAR remains authoritative for economic invariants and settlement semantics.
