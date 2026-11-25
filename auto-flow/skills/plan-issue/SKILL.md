---
name: plan-issue
description: Use when asked to plan or re-plan one issue without implementing it ("이슈 검토", "이 이슈 계획 세워줘", "미결 사항 답 반영해줘"), or when a bot owns the planning stage of an issue — turns the request into numbered acceptance criteria, splits the work across repos, manages open questions and decides when planning is finished. Writes each repo's plan itself unless that repo has another owner; then it requests the plan from the owner and waits. NOT for writing one repo's plan as its owner (plan-issue-detail), implementing (resolve-issue) or reviewing a PR (review-issue).
---

이슈 하나의 검토 단계를 맡아 수행하고 멈춥니다. 이슈 전체 계획을 쓰고 미결 사항을 관리하며, 검토를 끝낼지를 판정합니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 상태가 검토이거나, 미결 사항이 있거나, 레포별 계획이 필요한 레포가 있으면 [검토](../../references/stage-plan.md)를 수행합니다. 어느 것도 아니면 1번에서 바꾼 것 말고는 어느 절도 고치지 않고 공통 절차 7절대로 알린 뒤 멈춥니다.
3. 담당이 따로 있는 레포의 레포별 계획은 쓰지 않습니다. 검토 문서대로 미결 사항에 "레포별 계획 필요"를 올려 그 담당에게 맡기고, 담당이 `plan-issue-detail`로 계획을 채운 뒤에 끝내는 조건을 확인합니다.
4. 질문은 미결 사항에 적고 멈춥니다. 구현과 리뷰는 시작하지 않습니다.
