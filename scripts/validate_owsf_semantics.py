#!/usr/bin/env python3
"""Lightweight semantic validator for OWSF artifacts.

Checks implemented:
- unique event_id
- monotonic seq per writer_id
- non-negative integer lamport per event
- strict-tree space topology (single parent, parent exists, acyclic)
- causal dependencies resolve and are acyclic
- lamport causal consistency (dependency lamport strictly less than dependent's)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def fail(errors: list[str]) -> int:
    for err in errors:
        print(f"ERROR: {err}")
    return 1


def validate(path: Path) -> int:
    errors: list[str] = []

    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover
        return fail([f"cannot parse JSON: {exc}"])

    spaces = data.get("spaces")
    events = data.get("events")
    writers = data.get("writers")

    if not isinstance(spaces, list):
        errors.append("spaces must be an array")
        return fail(errors)
    if not isinstance(events, list):
        errors.append("events must be an array")
        return fail(errors)

    # --- space checks ---
    space_ids: set[str] = set()
    parent_of: dict[str, str | None] = {}

    for idx, s in enumerate(spaces):
        sid = s.get("id") if isinstance(s, dict) else None
        parent = s.get("parent") if isinstance(s, dict) else None
        if not isinstance(sid, str) or not sid:
            errors.append(f"spaces[{idx}] missing valid id")
            continue
        if sid in space_ids:
            errors.append(f"duplicate space id: {sid}")
            continue
        space_ids.add(sid)
        if parent is not None and not isinstance(parent, str):
            errors.append(f"space {sid} parent must be string or null")
        parent_of[sid] = parent

    roots = [sid for sid, parent in parent_of.items() if parent is None]
    if len(roots) != 1:
        errors.append(f"expected exactly one root space, found {len(roots)}")

    for sid, parent in parent_of.items():
        if parent is not None and parent not in space_ids:
            errors.append(f"space {sid} references missing parent {parent}")

    # cycle detection in parent graph
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs_space(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append(f"space cycle detected at {node}")
            return
        visiting.add(node)
        parent = parent_of.get(node)
        if isinstance(parent, str):
            dfs_space(parent)
        visiting.remove(node)
        visited.add(node)

    for sid in parent_of:
        dfs_space(sid)

    # --- event checks ---
    event_ids: set[str] = set()
    seq_by_writer: dict[str, int] = defaultdict(lambda: -1)
    lamport_by_event: dict[str, int] = {}
    writer_registry: set[str] = set()

    if writers is not None:
        if not isinstance(writers, list):
            errors.append("writers must be an array when present")
        else:
            for idx, w in enumerate(writers):
                wid = w.get("writer_id") if isinstance(w, dict) else None
                if not isinstance(wid, str) or not wid:
                    errors.append(f"writers[{idx}] missing valid writer_id")
                    continue
                if wid in writer_registry:
                    errors.append(f"duplicate writer_id in writers: {wid}")
                writer_registry.add(wid)

    # dependency graph for cycle checks
    deps: dict[str, list[str]] = {}

    for idx, e in enumerate(events):
        if not isinstance(e, dict):
            errors.append(f"events[{idx}] must be object")
            continue

        eid = e.get("event_id")
        writer = e.get("writer_id")
        space_id = e.get("space_id")
        seq = e.get("seq")
        lamport = e.get("lamport")

        if not isinstance(eid, str) or not eid:
            errors.append(f"events[{idx}] missing valid event_id")
            continue

        if eid in event_ids:
            errors.append(f"duplicate event_id: {eid}")
        event_ids.add(eid)

        if not isinstance(writer, str) or not writer:
            errors.append(f"event {eid} missing valid writer_id")
        elif writer_registry and writer not in writer_registry:
            errors.append(f"event {eid} writer_id not present in writers registry: {writer}")
        if not isinstance(space_id, str) or not space_id:
            errors.append(f"event {eid} missing valid space_id")
        elif space_id not in space_ids:
            errors.append(f"event {eid} references unknown space_id {space_id}")

        if not isinstance(seq, int):
            errors.append(f"event {eid} missing integer seq")
        elif isinstance(writer, str) and writer:
            if seq <= seq_by_writer[writer]:
                errors.append(
                    f"non-monotonic seq for writer {writer}: {seq} after {seq_by_writer[writer]}"
                )
            seq_by_writer[writer] = seq

        if not isinstance(lamport, int) or lamport < 0:
            errors.append(f"event {eid} missing non-negative integer lamport")
        else:
            lamport_by_event[eid] = lamport

        depends = e.get("depends_on", [])
        if depends is None:
            depends = []
        if not isinstance(depends, list):
            errors.append(f"event {eid} has non-array depends_on")
            depends = []
        cleaned: list[str] = []
        for dep in depends:
            if not isinstance(dep, str) or not dep:
                errors.append(f"event {eid} has invalid dependency id")
            else:
                cleaned.append(dep)
        deps[eid] = cleaned

    # dependency resolution
    for eid, dep_list in deps.items():
        for dep in dep_list:
            if dep not in event_ids:
                errors.append(f"event {eid} depends on missing event {dep}")

    # lamport causal consistency
    for eid, dep_list in deps.items():
        if eid not in lamport_by_event:
            continue
        for dep in dep_list:
            if dep not in lamport_by_event:
                continue
            if lamport_by_event[dep] >= lamport_by_event[eid]:
                errors.append(
                    f"event {eid} lamport {lamport_by_event[eid]} not greater than "
                    f"dependency {dep} lamport {lamport_by_event[dep]}"
                )

    # dependency cycle detection
    visiting_events: set[str] = set()
    visited_events: set[str] = set()

    def dfs_event(node: str) -> None:
        if node in visited_events:
            return
        if node in visiting_events:
            errors.append(f"event dependency cycle detected at {node}")
            return
        visiting_events.add(node)
        for dep in deps.get(node, []):
            if dep in deps:
                dfs_event(dep)
        visiting_events.remove(node)
        visited_events.add(node)

    for eid in deps:
        dfs_event(eid)

    if errors:
        return fail(errors)

    print("semantic validation OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OWSF semantic invariants.")
    parser.add_argument("artifact", help="Path to OWSF JSON artifact")
    args = parser.parse_args()

    return validate(Path(args.artifact))


if __name__ == "__main__":
    raise SystemExit(main())
