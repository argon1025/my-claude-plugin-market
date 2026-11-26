---
name: fix-issue
description: Use when asked to handle comments on the PRs of an issue run by this plugin ("PR 코멘트 반영해줘", "리뷰 지적 반영해줘", "코멘트 확인해서 수정해줘"), or when a bot periodically checks open PRs — reads the open PRs listed in the issue's progress table, picks comments that ask for a change, reconstructs why the PR was built that way from the issue and PR body, judges each comment against the code, then fixes or declines with a reason as a reply on the PR. Does not edit the issue body unless a comment requires changing the plan, in which case it adds an undecided row and sends the issue back to 검토중. NOT for first implementation (resolve-issue) or reviewing (review-issue).
---

이슈 하나의 열린 PR에 달린 코멘트를 확인해 반영하고 멈춥니다. 레포를 받았으면 그 레포의 PR만 봅니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다. 상태가 검토완료나 개발완료가 아니면 아무것도 고치지 않고 알린 뒤 멈춥니다.
2. [수정](../../references/stage-fix.md)을 수행합니다. 처리할 코멘트가 없으면 아무것도 바꾸지 않고 멈춥니다.
3. 의견을 그대로 따르지 않습니다. 이슈와 PR 본문에서 이전 맥락을 파악하고, 코드로 확인해 받아들일지 정한 뒤 그 코멘트에 답합니다.
4. 이슈 본문은 고치지 않습니다. 코멘트를 따르려면 계획이 바뀌어야 할 때만 미정 행을 더해 상태를 검토중으로 바꿉니다. PR을 승인하거나 머지하지 않습니다.
