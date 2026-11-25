---
name: plan-issue-detail
description: Use when asked to write one repo's detailed plan inside an issue whose issue-level plan already exists ("이 레포 세부 계획 세워줘", "레포별 계획 채워줘", "세부 계획 작성해줘"), or when a bot that owns a repo is handed an open question saying that repo's plan is needed — traces the current behavior in that repo's code, writes its work units with verification it actually ran, removes the request from the open questions and stops. Records an open question and stops when acceptance criteria or another repo's plan must change. NOT for acceptance criteria, splitting work across repos or deciding that planning is finished (plan-issue), and NOT for implementing (resolve-issue).
---

이슈에서 한 레포의 레포별 계획만 쓰고 멈춥니다. 레포를 받지 않았으면 자기가 맡은 레포 가운데 미결 사항에 "레포별 계획 필요"가 올라온 것을 수행합니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 미결 사항에 그 레포의 "레포별 계획 필요"가 있으면 [검토](../../references/stage-plan.md)의 2절을 그 레포에 수행합니다. 없으면 1번에서 바꾼 것 말고는 어느 절도 고치지 않고 공통 절차 7절대로 알린 뒤 멈춥니다.
3. 완료 조건, 레포 나누기, 다른 레포의 계획은 고치지 않습니다. 그것을 고쳐야 풀리는 문제와 사람에게 물을 것은 미결 사항에 적고 멈춥니다.
4. 계획을 다 채우면 그 레포의 "레포별 계획 필요" 줄을 지우고 멈춥니다. 단계는 바꾸지 않으며, 검토를 끝낼지는 `plan-issue`가 판정합니다. 구현은 시작하지 않습니다.
