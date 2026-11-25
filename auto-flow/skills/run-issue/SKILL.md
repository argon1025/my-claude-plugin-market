---
name: run-issue
description: Use when asked to take one issue forward end to end ("이 이슈 진행해줘", "ABC-123 처리해줘", an issue key or URL with a request to work on it) — reads the issue state, then plans, implements and reviews in order until it must wait for a person (open questions or a PR merge). To run a single stage only, use this plugin's plan-issue, resolve-issue or review-issue.
---

이슈 하나를 받아 사람을 기다리는 지점까지 이어 갑니다. 계획과 진행은 모두 이슈 본문에 기록합니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 공통 절차 2절대로 할 일을 고릅니다. 미결 사항이 있으면 [검토](../../references/stage-plan.md)를 수행합니다. 없으면 레포별 계획의 레포마다 그 단계의 문서를 수행합니다. 해결은 [해결](../../references/stage-resolve.md), 리뷰는 [리뷰](../../references/stage-review.md)입니다.
3. 한 단계가 끝나면 이슈를 다시 읽고 2번으로 돌아갑니다. 미결 사항이 남았거나, 남은 레포가 모두 머지 대기나 완료이거나, 순서 조건이나 사람의 확인을 기다리는 일만 남았으면 공통 절차 7절대로 알리고 멈춥니다.

- **질문**: 미결 사항에 적은 뒤 세션에서 한 번에 하나씩 묻고, 답을 받으면 반영해 계속합니다.
- **리뷰**: 이 세션이 구현한 레포의 리뷰는 직접 하지 않고 서브에이전트에 맡깁니다. 서브에이전트에는 이슈 위치, PR, 공통 절차·이슈 템플릿·리뷰 단계 문서의 절대 경로만 넘기고 구현 과정의 설명은 넘기지 않습니다. 서브에이전트를 쓸 수 없으면 리뷰하지 않고, 리뷰가 남았다고 알린 뒤 멈춥니다.
