#!/bin/bash
# 매 턴 dev-harness 핵심 리마인드를 주입한다. .harness/ 없는 프로젝트는 무음 skip.
# 전체 규약은 SessionStart가 주입하는 agent-guide.md가 담당한다 — 여기는
# 긴 세션에서 감쇠하는 규칙(feedback 즉시 append, 플랜 모드 스킬 로드)만 되짚는다.
set -euo pipefail

[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/.harness" ] || exit 0

REMINDER='DEV-HARNESS ACTIVE: 알게 된 사실은 즉시 feedback.md에 append(해당 태스크 커밋에 포함). 플랜 모드면 /dev-harness:planning 스킬 필수 로드. 규약은 세션 컨텍스트의 dev-harness 가이드.'

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$REMINDER"
