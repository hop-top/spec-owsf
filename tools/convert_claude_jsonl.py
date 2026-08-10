#!/usr/bin/env python3
"""Bidirectional converter: Claude Code session JSONL <-> OWSF core artifact.

Forward:  convert_claude_jsonl.py <session.jsonl> -o <artifact.json>
Reverse:  convert_claude_jsonl.py --reverse <artifact.json> -o <session.jsonl>

Claude Code session logs are JSONL files where each line is one record.
Chained records (``user``, ``assistant``, ``system``, ``attachment``) carry a
``uuid`` and a ``parentUuid`` linking them to the preceding record, plus a
shared envelope (``sessionId``, ``timestamp``, ``cwd``, ``gitBranch``,
``version``, ``entrypoint``, ``userType``, ``isSidechain``). Sidecar metadata
records (``ai-title``, ``last-prompt``, ``queue-operation``, ``summary``, ...)
may lack ``uuid``/``parentUuid``/``timestamp``.

Record type -> OWSF event type mapping:

    user (message.content has a tool_result block)  -> tool.result
    user (otherwise)                                -> message.user
    assistant (message.content has a tool_use block)-> tool.call
    assistant (otherwise)                           -> message.assistant
    system                                          -> message.system
    summary                                         -> context.summary
    anything else (attachment, ai-title,
      last-prompt, queue-operation, mode, ...)      -> record.other (generic)

``session.start`` and ``session.end`` are reserved taxonomy slots: no Claude
Code record type observed in the wild denotes a session lifecycle boundary,
so the converter never emits them today.

Conversion is lossless: every event's ``payload.raw`` holds the original
record verbatim, and the reverse pass re-serializes ``payload.raw`` (compact
separators, ``ensure_ascii=False``) one record per line in lamport order.
Output is deterministic: no randomness, no wall-clock reads.

Payloads for registry event types carry the agent-loop profile's structured
fields (``docs/profiles/agent-loop-v0.1.md``) extracted from the record —
``content`` for messages, ``tool``/``call_id``/``arguments`` for tool.call,
``status``/``call_id``/``output`` for tool.result, ``summary`` for
context.summary — with ``raw`` remaining authoritative.

Mapping invariants:
    - doc_id derived from sessionId (or content hash when absent)
    - created_at = first record timestamp, normalized to RFC3339 Z
    - one root filesystem space bounded by the session cwd
    - one writer per emitted role (claude-code:user/assistant/system)
    - event_id = record uuid (fallback ``rec-<index>`` for uuid-less records)
    - lamport = record index; seq strictly increasing per writer
    - depends_on = parentUuid, only when it resolves to an earlier record
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone

PRODUCER_NAME = "convert_claude_jsonl"
PRODUCER_VERSION = "0.1.0"

EPOCH_TS = "1970-01-01T00:00:00.000Z"

_TS_FRACTION = re.compile(r"(\.\d+)")


def dumps_compact(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def normalize_timestamp(value):
    """Normalize an ISO-8601 timestamp to RFC3339 UTC with ms and Z suffix."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"

    def _pad(match):
        digits = match.group(1)[1:]
        return "." + (digits + "000000")[:6]

    text = _TS_FRACTION.sub(_pad, text, count=1)
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".%03dZ" % (dt.microsecond // 1000)


def content_block_types(record):
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [b.get("type") for b in content if isinstance(b, dict)]


def classify_event_type(record):
    rtype = record.get("type")
    blocks = content_block_types(record)
    if rtype == "user":
        return "tool.result" if "tool_result" in blocks else "message.user"
    if rtype == "assistant":
        return "tool.call" if "tool_use" in blocks else "message.assistant"
    if rtype == "system":
        return "message.system"
    if rtype == "summary":
        return "context.summary"
    return "record.other"


def writer_for(record):
    rtype = record.get("type")
    if rtype == "user":
        return "claude-code:user"
    if rtype == "assistant":
        return "claude-code:assistant"
    return "claude-code:system"


def text_content(record):
    message = record.get("message")
    if not isinstance(message, dict):
        content = record.get("content")
        if isinstance(content, str):
            return content
        subtype = record.get("subtype")
        return subtype if isinstance(subtype, str) else ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            b.get("text")
            for b in content
            if isinstance(b, dict)
            and b.get("type") == "text"
            and isinstance(b.get("text"), str)
        ]
        return "".join(parts)
    return ""


def message_blocks(record, block_type):
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict) and b.get("type") == block_type]


def build_payload(record, event_type):
    payload = {"raw": record}
    message = record.get("message")
    if isinstance(message, dict) and isinstance(message.get("role"), str):
        payload["role"] = message["role"]
    if event_type in ("message.user", "message.assistant", "message.system"):
        payload["content"] = text_content(record)
        if event_type == "message.assistant":
            model = message.get("model") if isinstance(message, dict) else None
            if isinstance(model, str):
                payload["model"] = model
            stop_reason = message.get("stop_reason") if isinstance(message, dict) else None
            if isinstance(stop_reason, str):
                payload["stop_reason"] = stop_reason
    elif event_type == "tool.call":
        blocks = message_blocks(record, "tool_use")
        names = [b.get("name") for b in blocks if isinstance(b.get("name"), str)]
        if names:
            payload["tool"] = names[0]
        ids = [b.get("id") for b in blocks if isinstance(b.get("id"), str)]
        if ids:
            payload["call_id"] = ids[0]
        if blocks and isinstance(blocks[0].get("input"), dict):
            payload["arguments"] = blocks[0]["input"]
        payload["tools"] = names
    elif event_type == "tool.result":
        blocks = message_blocks(record, "tool_result")
        if blocks:
            payload["status"] = "error" if blocks[0].get("is_error") is True else "success"
            block_id = blocks[0].get("tool_use_id")
            if isinstance(block_id, str):
                payload["call_id"] = block_id
            if "content" in blocks[0]:
                payload["output"] = blocks[0]["content"]
        payload["tool_use_ids"] = [
            b.get("tool_use_id") for b in blocks if isinstance(b.get("tool_use_id"), str)
        ]
    elif event_type == "context.summary":
        summary = record.get("summary")
        if isinstance(summary, str) and summary:
            payload["summary"] = summary
    return payload


def forward(jsonl_text):
    records = []
    for lineno, line in enumerate(jsonl_text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit("line %d: invalid JSON: %s" % (lineno, exc))
        if not isinstance(parsed, dict):
            raise SystemExit("line %d: record must be a JSON object" % lineno)
        records.append(parsed)
    if not records:
        raise SystemExit("input contains no records")

    session_id = next(
        (r["sessionId"] for r in records if isinstance(r.get("sessionId"), str)),
        None,
    )
    if session_id:
        doc_id = "owsf-claude-code-" + session_id
    else:
        digest = hashlib.sha256(jsonl_text.encode("utf-8")).hexdigest()
        doc_id = "owsf-claude-code-" + digest[:16]

    cwd = next(
        (r["cwd"] for r in records if isinstance(r.get("cwd"), str) and r["cwd"]),
        "/",
    )
    created_at = next(
        (
            ts
            for ts in (normalize_timestamp(r.get("timestamp")) for r in records)
            if ts
        ),
        EPOCH_TS,
    )

    uuid_to_index = {}
    for idx, record in enumerate(records):
        uid = record.get("uuid")
        if isinstance(uid, str) and uid and uid not in uuid_to_index:
            uuid_to_index[uid] = idx

    writers = []
    seq_by_writer = {}
    events = []
    last_ts = created_at

    for idx, record in enumerate(records):
        event_type = classify_event_type(record)
        writer_id = writer_for(record)
        if writer_id not in seq_by_writer:
            seq_by_writer[writer_id] = 0
            writers.append({"writer_id": writer_id})
        seq = seq_by_writer[writer_id]
        seq_by_writer[writer_id] = seq + 1

        uid = record.get("uuid")
        event_id = uid if isinstance(uid, str) and uid else "rec-%04d" % idx

        ts = normalize_timestamp(record.get("timestamp"))
        if ts:
            last_ts = ts
        else:
            ts = last_ts

        event = {
            "event_id": event_id,
            "writer_id": writer_id,
            "space_id": "root",
            "type": event_type,
            "lamport": idx,
            "seq": seq,
            "timestamp": ts,
        }
        parent = record.get("parentUuid")
        if (
            isinstance(parent, str)
            and parent in uuid_to_index
            and uuid_to_index[parent] < idx
        ):
            event["depends_on"] = [parent]
        event["payload"] = build_payload(record, event_type)
        events.append(event)

    return {
        "owsf_version": "0.1",
        "doc_id": doc_id,
        "created_at": created_at,
        "producer": {"name": PRODUCER_NAME, "version": PRODUCER_VERSION},
        "writers": writers,
        "spaces": [
            {
                "id": "root",
                "type": "filesystem",
                "parent": None,
                "boundary": {"kind": "local_path", "ref": cwd},
                "capabilities": ["read", "write"],
                "trust_level": "trusted",
            }
        ],
        "events": events,
        "export": {"kind": "full", "determinism": "full"},
    }


def reverse(artifact_text):
    try:
        doc = json.loads(artifact_text)
    except json.JSONDecodeError as exc:
        raise SystemExit("invalid artifact JSON: %s" % exc)
    events = doc.get("events")
    if not isinstance(events, list) or not events:
        raise SystemExit("artifact has no events")
    ordered = sorted(
        enumerate(events), key=lambda pair: (pair[1].get("lamport", 0), pair[0])
    )
    lines = []
    for _, event in ordered:
        payload = event.get("payload")
        raw = payload.get("raw") if isinstance(payload, dict) else None
        if raw is None:
            raise SystemExit(
                "event %s has no payload.raw; artifact is not reversible"
                % event.get("event_id")
            )
        lines.append(dumps_compact(raw))
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Claude Code session JSONL to an OWSF core "
        "artifact, or back (--reverse)."
    )
    parser.add_argument(
        "input", help="session JSONL (forward) or OWSF artifact JSON (--reverse)"
    )
    parser.add_argument(
        "-o", "--output", help="output path (default: stdout)", default=None
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="reconstruct session JSONL from an OWSF artifact",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise SystemExit("cannot read %s: %s" % (args.input, exc))

    if args.reverse:
        out = reverse(text)
    else:
        out = json.dumps(forward(text), indent=2, ensure_ascii=False) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
