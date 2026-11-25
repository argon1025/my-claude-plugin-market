---
name: resolve-issue
description: Use when asked to implement one repo's part of an already planned issue, or to apply review findings on its PR ("이 이슈 구현해줘", "리뷰 지적 반영해줘"), or when a bot owns only implementation — checks the plan against current code, implements unit by unit with verification and commits, opens or updates the PR without asking, records results in the issue and stops. Stops and sends the issue back to planning when the plan no longer fits. NOT for planning (plan-issue) or reviewing (review-issue).
---

이슈에서 한 레포의 해결 단계만 수행하고 멈춥니다. 레포를 받지 않았으면 자기가 맡은 레포 가운데 단계가 해결인 것을 수행합니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 그 레포의 단계가 해결이면 [해결](../../references/stage-resolve.md)을 수행합니다. 해결이 아니면 1번에서 바꾼 것 말고는 어느 절도 고치지 않고 공통 절차 7절대로 알린 뒤 멈춥니다.
3. 계획을 고쳐야 풀리는 문제를 만나면 스스로 계획을 다시 세우지 않고, 해결 문서의 3절대로 미결 사항에 적고 멈춥니다. 리뷰는 시작하지 않습니다. 사람의 확인이나 머지처럼 기다리는 일만 남았으면 같은 검증을 다시 돌리지 않고 멈춥니다.
