---
name: resolve-issue
description: Use when asked to implement an already planned issue ("이 이슈 구현해줘", "이 이슈 개발 진행해줘"), or when a bot owns development — works only on issues whose status line is 검토완료, checks that the plan and decisions still hold, then takes the next row of the progress table in order (one row at a time, across repos), implements and verifies it, opens the PR without asking and records the row's status. Asks the user to run steps only a person can do. Sends the issue back to 검토중 with an undecided row when the plan no longer fits, and moves it to 개발완료 after the last row. NOT for planning (plan-issue), handling PR comments (fix-issue), closing (close-issue) or reviewing (review-issue).
---

상태가 검토완료인 이슈 하나를 "진행" 표의 순서대로 개발하고 멈춥니다. 여러 레포에 걸친 이슈도 이 스킬 하나가 차례로 맡습니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다. 상태가 검토완료가 아니면 아무것도 고치지 않고 알린 뒤 멈춥니다.
2. [개발](../../references/stage-resolve.md)을 수행합니다. 이번에 진행할 행을 고르고, 계획이 지금도 맞는지 확인한 뒤 구현·검증해 PR을 올립니다.
3. 계획을 바꿔야 풀리는 문제를 만나면 스스로 계획을 고치지 않고, 미정 행을 더해 상태를 검토중으로 바꾼 뒤 멈춥니다.
4. 시작 조건이나 사용자의 실행을 기다려야 하면 기다리는 것을 알리고 멈춥니다. 모든 행이 끝나면 상태를 개발완료로 바꿉니다. PR 코멘트의 반영과 리뷰는 하지 않습니다.
