#!/bin/bash
# 프로젝트에 .harness/가 있으면 dev-harness 운영 규약을 세션 컨텍스트로 주입한다.
# .harness/가 없는 프로젝트에서는 아무것도 출력하지 않고 종료한다.
set -euo pipefail

HARNESS_DIR="${CLAUDE_PROJECT_DIR:-$PWD}/.harness"
[ -d "$HARNESS_DIR" ] || exit 0

GUIDE_FILE="${CLAUDE_PLUGIN_ROOT}/rules/agent-guide.md"

python3 - "$GUIDE_FILE" "$CLAUDE_PLUGIN_ROOT" <<'PY'
import json
import sys

guide_path, plugin_root = sys.argv[1], sys.argv[2]
with open(guide_path, encoding="utf-8") as f:
    text = f.read().strip()

# 규약 본문의 ${CLAUDE_PLUGIN_ROOT} 토큰을 실제 설치 경로로 치환해
# 에이전트가 복사 즉시 실행 가능한 명령을 받게 한다.
text = text.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }
}, ensure_ascii=False))
PY
