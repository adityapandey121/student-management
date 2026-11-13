#!/usr/bin/env python3
"""Summarise a JSON or plain-text file.

JSON  -> record count, fields, and value counts for a chosen field
         (default: "course") when the file holds a list of objects.
Text  -> line, word and character counts plus the most common words.

Usage:
    python scripts/summarize.py FILE [--field NAME] [--top N] [--format text|json]

Exit codes: 0 = success, 2 = missing/unreadable/invalid input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


class SummaryError(Exception):
    """Raised for input problems that should be shown to the user."""


def load_text(path: Path) -> str:
    if not path.exists():
        raise SummaryError(f"file '{path}' not found")
    if path.is_dir():
        raise SummaryError(f"'{path}' is a directory, expected a file")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise SummaryError(f"'{path}' is not UTF-8 text (binary file?)") from None
    except OSError as exc:
        raise SummaryError(f"cannot read '{path}': {exc.strerror}") from None


def summarize_json(raw: str, field: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SummaryError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from None

    if isinstance(data, dict):
        return {"type": "json-object", "keys": sorted(data.keys()), "key_count": len(data)}

    if not isinstance(data, list):
        return {"type": f"json-{type(data).__name__}", "value": data}

    records = [item for item in data if isinstance(item, dict)]
    fields = sorted({key for record in records for key in record})
    summary = {
        "type": "json-list",
        "records": len(data),
        "object_records": len(records),
        "fields": fields,
    }
    if field in fields:
        counts = Counter(str(r[field]) for r in records if field in r)
        summary["field"] = field
        summary["value_counts"] = dict(counts.most_common())
        summary["missing_field"] = len(records) - sum(counts.values())
    return summary


def summarize_text(raw: str, top: int) -> dict:
    words = re.findall(r"[A-Za-z']+", raw.lower())
    return {
        "type": "text",
        "lines": len(raw.splitlines()),
        "words": len(words),
        "characters": len(raw),
        "top_words": Counter(words).most_common(top),
    }


def summarize_file(path: Path, field: str = "course", top: int = 5) -> dict:
    raw = load_text(path)
    if not raw.strip():
        raise SummaryError(f"'{path}' is empty")
    if path.suffix.lower() == ".json":
        result = summarize_json(raw, field)
    else:
        result = summarize_text(raw, top)
    result["file"] = path.as_posix()
    return result


def render_text(summary: dict) -> str:
    lines = [f"Summary of {summary['file']} ({summary['type']})"]
    for key, value in summary.items():
        if key in ("file", "type"):
            continue
        if key == "value_counts":
            lines.append(f"  {summary['field']} breakdown:")
            lines.extend(f"    {name}: {count}" for name, count in value.items())
        elif key == "top_words":
            lines.append("  top words: " + ", ".join(f"{w} ({c})" for w, c in value))
        elif key != "field":
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a whole number, got '{value}'") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarise a JSON or text file.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--field", default="course", help="JSON field to group by (default: course)")
    parser.add_argument("--top", type=positive_int, default=5, help="top N words for text files")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        summary = summarize_file(args.file, args.field, args.top)
    except SummaryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2) if args.format == "json" else render_text(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
