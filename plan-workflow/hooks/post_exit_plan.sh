#!/bin/bash
# ExitPlanMode 승인 직후 하네스가 구현 시작을 지시하므로, 같은 시점에 plan-workflow의
# 핸드오프 규칙(스냅샷 커밋 후 세션 종료)을 한 줄로 되새긴다. 규칙 본문은 planning 스킬 7절이
# 담당하며 여기서 다시 쓰지 않는다. 활성 조건은 session_start.sh와 같고 어떤 실패에도 조용히 끝낸다.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

REMINDER='PLAN-WORKFLOW 핸드오프: 계획이 승인되었습니다. 이 세션은 구현을 시작하지 않습니다 — planning 스킬 7절대로 plan.md·feedback.md 스냅샷을 커밋하고 새 세션에서 /plan-workflow:execute로 시작하도록 안내한 뒤 턴을 끝냅니다.'
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$REMINDER"
