---
name: execute
description: Use when implementing an approved plan snapshot saved as plan.md in the session's workspace folder, typically in a fresh session after planning ("계획 실행", "플랜 실행", "execute the plan") — reads the plan first, one task → verification → one commit, stops and re-plans on deviation, appends feedback.md as facts surface. NOT for writing a plan (that is this plugin's planning skill's job).
---

승인된 계획이 계약이며, 계획에서 벗어나는 결정은 사용자에게 되돌립니다. 기록 규칙은 세션에 주입된 작업 기록 규약을 따릅니다.

## 1. 사전 확인

- **위치**: 세션 `## 현재 워크스페이스` 블록의 slug·기록 폴더를 확인하고 `plan.md` 전문을 `## 의도`부터 읽음. 주입된 `feedback.md`는 최근 일부일 수 있으므로 관련 원본 기록도 읽어 정정·철회·위임을 확인함
- **선행 읽기**: `plan.md`의 `## 선행 읽기` 문서를 코드보다 먼저 읽고, 세션에 주입된 사전 정보에 손대는 파일을 다루는 문서가 더 있으면 함께 읽음
- **부재 시 정지**: `plan.md`가 없으면 즉석에서 계획을 만들지 않고 멈춰서 물음
- **실행 대상 판정**: 절이 여럿이면 앞에서부터 각 절의 커밋 분해가 git log와 코드에 이미 반영됐는지 대조해 미실행 절만 실행하고, 폐기 선언된 절과 항목은 건너뛰며, 완료 여부가 갈리면 멈춰 물음
- **관례**: 손댈 파일 주변 코드가 세운 관례를 따름
- **판단 범위**: 계획의 확정 요구사항과 명시적으로 위임된 구현 재량을 구분함. 위임 범위·제약·검증 조건 안의 선택은 수행하고 이유를 기록하며, 누락된 요구사항을 구현 재량으로 간주하지 않음

## 2. 실행 루프

- **커밋 단위**: 계획의 커밋 분해 순서대로 태스크 하나 → 그 검증 → 커밋 하나를 반복하며 Conventional Commits를 씀
- **더 낮은 단**: 계획이 예견하지 못한 기존 헬퍼·표준 라이브러리는 합의한 동작·계약·제약을 유지하는 구현 재사용일 때 취하고 커밋 메시지에 밝힘. 더 짧다는 이유로 합의한 구조나 요구사항을 바꾸지 않음
- **재계획**: API 형태·의존성 부재처럼 현실이 계획과 어긋나면 해당 작업을 멈추고 증거를 보고함. [planning의 인터뷰 반복](../planning/SKILL.md)을 따라 새 결정을 하나씩 합의하고 연관된 계약·검증을 재점검한 뒤, 승인된 변경을 `plan.md` 끝의 `## Re-plan YYYY-MM-DD — {한 줄 계기}` 절에 덧붙여 이어감
- **실패 시 정지**: 검증이 실패하면 멈추고 보고하며, 재시도 루프·`--no-verify`·테스트 건너뛰기는 하지 않음
- **합의 밖**: 모호한 지점이나 위임 범위를 벗어난 결정은 추정하지 않고 한 항목씩 질문함. 기존의 다른 항목에 대한 `동의`·위임을 이번 결정의 승인으로 확대하지 않음
- **기록**: 사실이 드러날 때 `feedback.md`에 덧붙이고 늦어도 그 사실을 쓰는 커밋에 함께 담음

## 3. 완료

- **최종 확인**: 계획된 커밋이 모두 끝나고 검증이 통과하면 브랜치를 한 번 훑어 빠진 `feedback.md` 항목을 보충 커밋함
- **보고**: 커밋별 검증 결과를 보고하며, PR 생성은 요청 시에만 함
