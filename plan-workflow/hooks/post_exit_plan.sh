#!/bin/bash
# ExitPlanMode 승인 직후 하네스가 구현 시작을 지시하므로, 같은 시점에 이 플러그인의
# 핸드오프 규칙(스냅샷 커밋 후 세션 종료)을 한 줄로 되새긴다. 규칙 본문은 planning 스킬의 승인·인계 절이
# 담당하며 여기서 다시 쓰지 않는다. 활성 조건은 session_start.sh와 같고 어떤 실패에도 조용히 끝낸다.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

REMINDER='계획 핸드오프: 최종 계획이 승인되었습니다. 별도 사용자 지시가 없으면 planning 스킬의 승인·인계 절대로 plan.md·feedback.md 스냅샷을 커밋하고 새 세션의 execute 스킬을 안내한 뒤 턴을 끝냅니다. 계획 승인만으로 구현을 시작하지 않습니다.'
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$REMINDER"
