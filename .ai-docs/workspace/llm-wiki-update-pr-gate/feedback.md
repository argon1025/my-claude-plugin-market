# llm-wiki-update-pr-gate 작업 기록

- `context` PR 생성 및 승인 게이트 도입 (사용자, 이후 PR 기록을 보고 어떤 근거로 수행했는지 할 수 있도록) 현재는 바로 push해서 별도 승인게이트가 없음
  - source: 사용자 확인 2026-09-28
- `context` PR 템플릿은 개발자가 업데이트 후 내용이 맞는지 확인용, 이후 히스토리용이며 에이전트가 작성하기 용이한 구조여야 함 — 시안 A(사실 원장)를 채택하되 추출 사실은 사실·판정·사유·출처 순으로 두고 문서 열은 빼며, 문서는 각 문서마다 표 말고 섹션으로 두고 불릿으로 어떻게 수정·삭제·추가했는지 간결히 정리
  - source: 사용자 확인 2026-09-28
- `constraint` llm-wiki update.py의 미러는 `{--wiki}/.local/mirrors/{slug}.git`에 있어 위키를 git worktree로 옮겨 실행하면 미러를 전부 다시 clone하므로, update의 PR 브랜치 작업은 WIKI_ROOT 체크아웃 자체에서 브랜치를 전환해 수행함
  - evidence: llm-wiki/scripts/update.py mirror_path
- `why` llm-wiki update는 커서(`state/{slug}.json`) 커밋도 PR에 태워 PR close가 전체 거절이 되게 하고, 대신 열린 `wiki-update/` PR이 있으면 같은 머지를 두 번 추출하지 않도록 실행을 중단함
- `why` llm-wiki update PR 본문은 렌더 스크립트 없이 메인 에이전트가 extract·assign·applied·review JSON을 순회해 `templates/update-pr.md` 규칙대로 작성하며, 이를 위해 assign.json에 기각 사실(`rejected`), 반영 출력에 `summary`, 검토 출력에 `ids`를 둠
- `constraint` llm-wiki update PR은 squash 머지하면 문서별 커밋 본문(규약 8장 발견 근거·기존/새 값)이 사라지므로 rebase 또는 merge commit으로만 머지함
- `why` llm-wiki update SKILL.md는 push·PR 생성을 6장이 아니라 7장에 둠 — PR 본문 `pr.md`를 먼저 써야 `gh pr create --body-file`이 가능하므로 6장은 커밋까지, 7장이 본문 작성·push·PR·`main` 복귀를 맡음
- `why` llm-wiki update의 `wiki-update/*` 브랜치는 `pending` 종료 코드 0이고 `--dry-run`이 아닐 때만 만듦 — 미처리 없음·dry-run 실행이 빈 브랜치를 남기지 않게 하기 위함
- `constraint` llm-wiki update PR의 커밋 링크는 `work.json`에 remote가 없어 `registry.json` 노드의 `remote`(scheme 없는 정규화 꼴)로 `https://{remote}/commit/{sha}`를 만듦
  - evidence: llm-wiki/scripts/update.py mirror_path
- `constraint` llm-wiki `/llm-wiki:update`는 PR로만 반영하므로 위키에 GitHub 원격과 `gh` 인증이 필요하며, 없으면 열린 PR 검사 단계에서 보고 후 중단함 — 원격 없는 로컬 전용 위키에서는 update를 쓸 수 없음
- `why` llm-wiki update는 작업 브랜치 생성 뒤 어느 단계에서 끝나든 미커밋 편집을 `stash -u`로 치우고 `main`으로 복귀함 — 브랜치에 남은 편집을 세션 주입이나 add·register·audit가 `main` 기준으로 읽고 커밋하지 않게 하되, 폐기 대신 stash로 원인 조사 여지를 남김
- `why` llm-wiki update 4장 반영 출력은 `skipped`를 따로 두지 않고 `verdicts[{id, verdict, summary, old}]` 한 목록에 건너뜀까지 담음 — 건너뜀 사유는 7장 판정상 항상 "의도 인용 없음"이고 slug·sha는 `id`로 3장 사실 행에서 얻으므로 PR 원장이 `id` 하나로 모든 판정을 잇게 하기 위함
- `context` 간선 기각(상대 미정·선언 위치·contracts 상한)은 사실 `id`가 없어 `assign.json` `rejected`에 `id` 없이 식별자 원문으로 남기고 PR 본문 `그래프` 절에 실음
