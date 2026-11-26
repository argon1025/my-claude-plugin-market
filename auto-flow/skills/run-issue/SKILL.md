---
name: run-issue
description: Use when asked to take one issue forward in a single session ("이 이슈 진행해줘", "ABC-123 처리해줘", an issue key or URL with a request to work on it) — reads the issue's status line, plans while it is 검토중 (asking undecided questions in the session one at a time), then develops the progress table row by row while it is 검토완료, until it must wait for a person (an answer, a step the user runs, or a PR merge). To run a single state only, use this plugin's plan-issue, resolve-issue, fix-issue or close-issue. Does not review; ask for review-issue separately.
---

이슈 하나를 받아 사람을 기다리는 지점까지 한 세션에서 이어 갑니다. 계획과 진행은 이슈 본문에, 구현 결과는 PR에 기록합니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다. 이 스킬은 검토중과 검토완료를 맡습니다.
2. 상태가 검토중이면 [검토](../../references/stage-plan.md)를 수행합니다. 미정 행은 본문에 적은 뒤 세션에서 한 번에 하나씩 묻고, 받은 답을 그 행의 기록 칸에 옮겨 적은 뒤 계속합니다. 답이 없으면 멈춥니다.
3. 상태가 검토완료면 [개발](../../references/stage-resolve.md)을 수행합니다. 한 행이 끝나면 이슈를 다시 읽고 다음 행으로 갑니다. 다음 행이 다른 레포면 그 레포의 체크아웃에서 수행하고, 체크아웃이 없으면 그 사실을 알리고 멈춥니다.
4. 미정 행의 답, 사용자의 실행, PR 머지를 기다려야 하거나 상태가 개발완료가 되면 공통 절차 6절대로 알리고 멈춥니다.

- **리뷰**: 이 스킬은 리뷰하지 않습니다. 리뷰가 필요하면 구현하지 않은 세션에서 `review-issue`를 따로 호출합니다.
- **PR 이후**: 코멘트의 반영은 `fix-issue`, 머지 뒤의 정리는 `close-issue`가 합니다.
