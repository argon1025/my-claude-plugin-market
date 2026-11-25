---
name: review-issue
description: Use when asked to review one repo's PR of an issue run by this plugin ("이 이슈 리뷰해줘", "PR 리뷰"), or when a bot owns only review — checks the code, differences from the wiki, and mistakes in the plan and records, writes findings in the issue (not as PR comments), and moves the repo to waiting-for-merge only when no blocking finding is open. Must run in a context that did not implement the change. NOT for fixing code (resolve-issue).
---

이슈에서 한 레포의 리뷰 단계만 수행하고 멈춥니다. 이 세션이 그 레포를 구현했다면 리뷰하지 않고, 다른 실행자가 리뷰해야 한다고 알린 뒤 멈춥니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다.
2. 그 레포의 단계가 리뷰이면 [리뷰](../../references/stage-review.md)를 수행합니다. 리뷰가 아니면 1번에서 바꾼 것 말고는 어느 절도 고치지 않고 공통 절차 7절대로 알린 뒤 멈춥니다.
3. 코드는 고치지 않습니다. PR을 승인하거나 머지하지 않습니다.
