---
name: review-issue
description: Use when the user explicitly asks to review one repo's PR of an issue run by this plugin ("이 이슈 리뷰해줘", "이 PR 리뷰해줘") — checks the code against the issue's acceptance criteria and plan, verifies that the PR body's claims are true, and leaves each finding as a PR comment plus one summary comment. Never invoked by the other skills, and does not change the issue body or status. Must run in a context that did not implement the change. NOT for fixing code or answering comments (fix-issue).
---

이슈에서 한 레포의 PR을 리뷰하고 멈춥니다. 요청받았을 때만 수행합니다. 이 세션이 그 레포를 구현했다면 리뷰하지 않고, 다른 실행자가 리뷰해야 한다고 알린 뒤 멈춥니다.

1. [공통 절차](../../references/common.md)를 읽고 1절의 1~3번(이슈 지정, 도구 확인, 읽기)을 수행합니다. 이슈의 상태는 가리지 않습니다.
2. 그 레포의 열린 PR에 [리뷰](../../references/stage-review.md)를 수행합니다. PR이 없으면 그 사실을 알리고 멈춥니다.
3. 지적은 PR 코멘트로 남깁니다. 이슈 본문과 코드는 고치지 않고, PR을 승인하거나 머지하지 않습니다.
