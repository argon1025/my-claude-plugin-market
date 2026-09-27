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
