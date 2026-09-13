#!/bin/bash
# 산출물 작성 규약(rules/agent-guide.md)을 세션 컨텍스트로 주입한다.
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact 모두에서 다시 돈다.
# 한국어 본문의 JSON 이스케이프는 python3에 맡긴다.
set -euo pipefail

python3 - "${CLAUDE_PLUGIN_ROOT}/rules/agent-guide.md" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    text = handle.read().strip()

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }
}, ensure_ascii=False))
PY
