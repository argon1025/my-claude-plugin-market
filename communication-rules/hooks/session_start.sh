#!/bin/bash
# rules/ 아래 실질(substance)·문체(style) 규칙을 세션 컨텍스트로 주입한다.
set -euo pipefail

SUBSTANCE_FILE="${CLAUDE_PLUGIN_ROOT}/rules/substance.md"
STYLE_FILE="${CLAUDE_PLUGIN_ROOT}/rules/style.md"

python3 - "$SUBSTANCE_FILE" "$STYLE_FILE" <<'PY'
import json
import sys

parts = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        parts.append(f.read().strip())

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n---\n\n".join(parts),
    }
}, ensure_ascii=False))
PY
