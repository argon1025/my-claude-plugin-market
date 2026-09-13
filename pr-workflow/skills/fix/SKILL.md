---
name: fix
description: Use when applying review comments on a pull request as the PR author ("리뷰 반영", "코멘트 반영", "리뷰 코멘트 처리", right after a /pr-workflow:review report) — triages every unresolved comment (AI + human) into 수용/기각/이미 해결 with evidence, gets that triage approved, fixes accepted items as commits, then after one more approval pushes and replies to each thread. NOT for reviewing a PR (that is /pr-workflow:review's job). Requires running inside the target repo's checkout.
---

## 계약 로드

- `${CLAUDE_PLUGIN_ROOT}/references/pr-protocol.md` — 사전 조건, 저장소·PR 좌표, 승인 게이트, 금지 행동
- `${CLAUDE_PLUGIN_ROOT}/references/review-comment.md` — 어떤 스레드를 집고 어떤 접두사로 답하는지

## 가드레일

- **force-push 금지**: 어떤 경우에도 하지 않음
- **검증 실패**: push하지 않고 중단해 보고함. 재시도 루프도 우회도 없음
- **신규 발견 금지**: 리뷰는 `/pr-workflow:review`의 일이며, 수정 중 발견한 문제는 코멘트가 아니라 보고로 남김
- **승인 2회 고정**: 판정 세트 승인과 외부 쓰기 묶음 승인. 항목별로 묻지 않음
- **무단 생략 금지**: 기각·보류·미실행 검증을 전부 보고함
- **동일 저장소**: 다른 저장소의 PR은 거절하고 그 체크아웃을 안내함

## 1. PR 확정·소스 브랜치 체크아웃

`pr-protocol.md`로 좌표와 PR 번호를 확정합니다. 현재 브랜치가 PR의 소스 브랜치가 아니면 체크아웃하고, 작업 트리가 dirty면 중단해 보고합니다. push 대상은 소스 브랜치를 보유한 리모트(fork면 `origin`)입니다.

## 2. 미해결 스레드 수집

호스트 도구로 인라인·최상위 코멘트를 AI·사람 구분 없이 가져오고, 아래를 제외합니다.

- **resolved 스레드**
- **`[AI 반영` 답글이 달린 스레드**
- **앵커 없는 `[AI 코드리뷰]` 요약**: 지적이 아니라 보고임

## 3. 판정·승인

각 코멘트를 현재 HEAD와 비판적으로 대조해 수용 / 기각 / 이미 해결로 판정합니다. 근거는 필수이며, 코드 경로나 동작을 확인하지 않은 기각은 금지합니다.

지적 / 수용여부 / 사유 / 수정 계획 표 하나를 보여주고 코드를 만지기 전에 세트 전체의 승인을 받습니다. 기각 판정은 사용자가 승인하며, 변경 요청은 표에 반영해 다시 보여줍니다.

## 4. 수정·검증

- **커밋 단위**: 논리 단위 1개 = 커밋 1개, Conventional Commits
- **검증**: lint·typecheck·test 중 프로젝트에 있는 것을 실행해 전부 통과해야 함. 실패 시 중단해 보고함

## 5. 승인 1회·push·답글

"푸시 + 답글 게시 진행?"을 한 번 묻습니다.

- **승인 시**: push 후 `review-comment.md`의 `[AI 반영]` 양식으로 스레드별 답글을 붙임
- **거절 시**: 아무것도 밖으로 나가지 않으며 로컬 커밋 상태를 보고함

## 6. 핸드오프

- **재검증**: 마지막 한 줄 `재검증: /pr-workflow:review 재실행`
- **종료 조건**: 재리뷰가 Blocker·Bug 0건을 보고하고 이전 발견이 전부 해결이거나 기각이 수용되면 루프가 끝남
- **교착**: 3회차에도 갈리는 항목은 4회차 대신 사용자에게 넘김
