---
name: close-issue
description: Use when asked to wrap up an issue whose development is finished ("이슈 정리해줘", "머지됐는지 확인하고 마무리해줘", "완료 처리해줘"), or when a bot periodically closes out finished issues — works only on issues whose status line is 개발완료, checks whether each PR in the progress table is merged and whether the user's steps and confirmations are recorded, reflects them in the body and moves the issue to 완료 when everything is done. Ignores reviews and comments. Sends the issue back to 검토중 when a PR was closed without merging. NOT for implementing (resolve-issue) or handling PR comments (fix-issue).
---

상태가 개발완료인 이슈 하나에서 머지와 사람의 확인을 본문에 반영하고, 모두 끝났으면 완료로 바꾼 뒤 멈춥니다.

1. [공통 절차](../../references/common.md)를 읽고 1절(시작)을 수행합니다. 상태가 개발완료가 아니면 아무것도 고치지 않고 알린 뒤 멈춥니다.
2. [정리](../../references/stage-close.md)를 수행합니다.
3. 남은 것이 있으면 상태를 그대로 두고 남은 것을 알린 뒤 멈춥니다. 코드는 고치지 않고, PR을 승인하거나 머지하지 않습니다.
