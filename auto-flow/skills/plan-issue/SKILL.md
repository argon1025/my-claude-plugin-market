---
name: plan-issue
description: Use when asked to plan or re-plan one issue without implementing it ("이슈 검토", "이 이슈 계획 세워줘", "미결 사항 답 반영해줘"), or when a bot owns only the planning stage — turns the request into numbered acceptance criteria and per-repo plans in the issue body, records open questions and stops. Pass a repo to write only that repo's plan. NOT for implementing (resolve-issue) or reviewing a PR (review-issue).
---

이슈 하나의 검토 단계만 수행하고 멈춥니다. 레포를 함께 받으면 그 레포의 레포별 계획만 다룹니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 상태가 검토이거나, 미결 사항이 있거나, 레포별 계획이 필요한 레포가 있으면 [검토](../../references/stage-plan.md)를 수행합니다. 어느 것도 아니면 1번에서 바꾼 것 말고는 어느 절도 고치지 않고 공통 절차 7절대로 알린 뒤 멈춥니다.
3. 질문은 미결 사항에 적고 멈춥니다. 구현과 리뷰는 시작하지 않습니다.
