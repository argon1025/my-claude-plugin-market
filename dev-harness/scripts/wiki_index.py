#!/usr/bin/env python3
"""Wiki index — parse the project's `.harness/docs/` frontmatter and emit a filterable table.

Run from the project root (docs path resolves relative to cwd); override with --docs-root.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_DOCS_ROOT = ".harness/docs"
REQUIRED_FIELDS = ("description", "scope", "created", "updated")
HEADERS = ("PATH", "SCOPE", "UPDATED", "HARVESTED", "LINES", "DESCRIPTION")


def warn(msg: str) -> None:
    print(f"warn: {msg}", file=sys.stderr)


def parse_scope_list(raw: str) -> list[str] | None:
    s = raw.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return []
    items: list[str] = []
    for token in inner.split(","):
        t = token.strip()
        if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
            t = t[1:-1]
        if not t:
            return None
        items.append(t)
    return items


def parse_frontmatter(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        warn(f"{path}: read failed ({e})")
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        warn(f"{path}: missing frontmatter")
        return None

    body: list[str] = []
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        body.append(line)
    if not closed:
        warn(f"{path}: unclosed frontmatter")
        return None

    fields: dict[str, object] = {}
    for raw_line in body:
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            warn(f"{path}: malformed line `{line}`")
            return None
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "scope":
            parsed = parse_scope_list(value)
            if parsed is None:
                warn(f"{path}: scope must be inline list, got `{value}`")
                return None
            fields[key] = parsed
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            fields[key] = value

    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    if missing:
        warn(f"{path}: missing field(s) {','.join(missing)}")
        return None

    fields["__lines__"] = len(lines)  # total file lines — cheap size signal for harvest ranking
    return fields


def glob_to_regex(pattern: str) -> re.Pattern:
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("".join(out))


def scope_matches(file_scopes: list[str], input_glob: str) -> bool:
    input_re = glob_to_regex(input_glob)
    for fs in file_scopes:
        if input_re.fullmatch(fs):
            return True
        if glob_to_regex(fs).fullmatch(input_glob):
            return True
    return False


def collect(root: Path) -> list[tuple[Path, dict]]:
    if not root.is_dir():
        warn(f"{root}: directory not found")
        return []
    rows: list[tuple[Path, dict]] = []
    for path in sorted(root.rglob("*.md")):
        fm = parse_frontmatter(path)
        if fm is None:
            continue
        rows.append((path, fm))
    return rows


def format_table(rows: list[tuple[Path, dict]]) -> str:
    cells: list[tuple[str, str, str, str, str, str]] = []
    for path, fm in rows:
        scope_val = ",".join(fm["scope"]) if isinstance(fm["scope"], list) else str(fm["scope"])
        harvested_val = str(fm.get("harvested", ""))
        lines_val = str(fm.get("__lines__", ""))
        cells.append((str(path), scope_val, str(fm["updated"]), harvested_val, lines_val, str(fm["description"])))

    widths = [len(h) for h in HEADERS]
    for row in cells:
        for i, val in enumerate(row):
            if len(val) > widths[i]:
                widths[i] = len(val)

    def fmt(row: tuple[str, str, str, str, str, str]) -> str:
        return " | ".join(val.ljust(widths[i]) for i, val in enumerate(row))

    lines = [fmt(HEADERS)]
    for row in cells:
        lines.append(fmt(row))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse the project's .harness/docs/ frontmatter and print an index table.",
    )
    parser.add_argument(
        "--scope",
        metavar="GLOB",
        help="Filter to files whose scope bidirectionally matches GLOB.",
    )
    parser.add_argument(
        "--docs-root",
        metavar="PATH",
        default=DEFAULT_DOCS_ROOT,
        help=f"Wiki docs root (default: {DEFAULT_DOCS_ROOT}, relative to cwd).",
    )
    args = parser.parse_args()

    rows = collect(Path(args.docs_root))
    if args.scope:
        rows = [(p, fm) for p, fm in rows if scope_matches(fm["scope"], args.scope)]

    print(format_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
