#!/bin/bash
# 세션 시작에 주입된 규약을 가리키는 한 줄만 매 턴 찍는다. 규칙을 여기서 다시 쓰지 않는다.
set -uo pipefail

REMINDER='BETTER-COMMUNICATION ACTIVE: 세션 시작에 주입된 산출물 작성 규약을 그대로 따릅니다.'

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$REMINDER"
