#!/bin/bash
# 세션 시작에 주입된 규약을 가리키는 한 줄만 매 턴 찍는다. 규칙을 여기서 다시 쓰지 않는다.
set -uo pipefail

REMINDER='COMMUNICATION RULES ACTIVE: 세션 시작에 주입된 응답·문서 작성 규칙을 그대로 따릅니다.'

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$REMINDER"
