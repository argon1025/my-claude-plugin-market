---
name: plan-issue
description: Use when asked to plan or re-plan one issue without implementing it ("이슈 검토", "이 이슈 계획 세워줘", "미정 행 답 반영해줘"), or when a bot owns the planning state of an issue — works only on issues whose status line is 검토중, turns the request into numbered acceptance criteria, lays out who does what in which order across repos, writes every repo's plan, manages undecided rows and moves the issue to 검토완료 when none remain. Leaves any other status untouched. NOT for implementing (resolve-issue), handling PR comments (fix-issue), closing (close-issue) or reviewing a PR (review-issue).
---

상태가 검토중인 이슈 하나의 계획을 쓰고 멈춥니다. 이슈 전체 계획과 모든 레포의 레포별 계획을 이 스킬이 씁니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다. 상태가 검토중이 아니면 아무것도 고치지 않고 알린 뒤 멈춥니다.
2. [검토](../../references/stage-plan.md)를 수행합니다. 미정 행의 답을 반영하고, 이슈 전체 계획을 쓰고, 미정 행이 없으면 레포별 계획까지 씁니다.
3. 미정 행이 남으면 본문에 적고 멈춥니다. 답할 사람을 지정하거나 알리는 댓글을 남기지 않습니다.
4. 끝내는 조건을 채우면 상태를 검토완료로 바꾸고 멈춥니다. 구현은 시작하지 않습니다.
