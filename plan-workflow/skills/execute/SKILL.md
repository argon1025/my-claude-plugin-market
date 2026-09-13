---
name: execute
description: Use when implementing an approved plan snapshot saved at .ai-docs/workspace/{slug}/plan.md, typically in a fresh session after planning ("계획 실행", "플랜 실행", "execute the plan") — reads the plan first, one task → verification → one commit, stops and re-plans on deviation, appends feedback.md as facts surface. NOT for writing a plan (that is /plan-workflow:planning's job).
---

승인된 계획이 계약이며, 계획에서 벗어나는 결정은 사용자에게 되돌립니다. 기록 규칙은 세션에 주입된 작업 기록 규약을 따릅니다.

## 1. 사전 확인

- **위치**: 세션 `## 현재 워크스페이스` 블록의 slug와 주입된 `feedback.md`를 확인하고, `.ai-docs/workspace/{slug}/plan.md` 전문을 `## 의도`부터 읽음
- **부재 시 정지**: `plan.md`가 없으면 즉석에서 계획을 만들지 않고 멈춰서 물음
- **관례**: 손댈 파일 주변 코드가 세운 관례를 따름

## 2. 실행 루프

- **커밋 단위**: 계획의 커밋 분해 순서대로 태스크 하나 → 그 검증 → 커밋 하나를 반복하며 Conventional Commits를 씀
- **더 낮은 단**: 계획이 예견하지 못한 기존 헬퍼·표준 라이브러리가 있으면 더 작은 변경이므로 취하고 커밋 메시지에 밝힘
- **재계획**: API 형태·의존성 부재처럼 현실이 계획과 어긋나면 멈춰 증거를 보고하고, 합의된 변경을 `plan.md` 끝에 `## Re-plan YYYY-MM-DD` 절로 덧붙인 뒤 이어감
- **실패 시 정지**: 검증이 실패하면 멈추고 보고하며, 재시도 루프·`--no-verify`·테스트 건너뛰기는 하지 않음
- **합의 밖**: 모호한 지점이나 합의 밖의 결정이 나오면 멈추고 물음
- **기록**: 사실이 드러날 때 `feedback.md`에 덧붙이고 늦어도 그 사실을 쓰는 커밋에 함께 담음

## 3. 완료

- **최종 확인**: 계획된 커밋이 모두 끝나고 검증이 통과하면 브랜치를 한 번 훑어 빠진 `feedback.md` 항목을 보충 커밋함
- **보고**: 커밋별 검증 결과를 보고하며, PR 생성은 요청 시에만 함
