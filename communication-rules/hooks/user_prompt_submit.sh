#!/bin/bash
# 매 턴 실질 규칙 리마인드를 주입한다.
# 문체 규칙은 넣지 않는다 — 다른 문체 페르소나(caveman 등)의 매 턴 리마인드와
# 나란히 떠도 충돌하지 않게 하기 위함이다. 문체는 SessionStart의 style.md가 담당한다.
set -euo pipefail

REMINDER='COMMUNICATION-RULES ACTIVE. 최종 산출물 필수: 결정 보고 골격(문제 정의/선택지/효과/권장/검증), 구체 수치, 모호어 금지, 기술 식별자 원형. 문체는 활성 페르소나 따름. PR 본문·문서 파일은 communication-rules 문체 규칙까지 전체 적용.'

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$REMINDER"
