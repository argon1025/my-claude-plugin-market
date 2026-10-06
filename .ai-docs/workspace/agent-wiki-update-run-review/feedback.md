# agent-wiki-update-run-review 작업 기록

- `context` 2026-10-06 사내 update 실행 A·B 리뷰(사내판 루트 `agent-wiki-update-review.md`) 개선 제안 15건은 비판 검토로 수용 여부를 정하며, 기준은 사용자 문장 "비판적으로 검토 후 수용여부 결정 (최우선은 간결한 구조와 프롬프트)", "실제실측하고 개선이 가능한 부분만, 프로세스 진행 중 자연스럽게 회복되는문제는 무시해도 무방할듯"임 — 수용은 update 커서 커밋 1개화와 검토 프롬프트 입력의 `assign.json` 참조 2건이고 나머지 13건은 기각함
  - source: 사용자 확인 2026-10-06
- `context` 사내판 미러링 때 사내판 `plugins/agent-wiki/config.json`의 `wiki.baseRoot`를 개인판과 다른 경로로 바꿈 — 사용자 문장 "사내판 반영 하면서 llm-wiki config 경로 baseRoot 를 개인판과 충돌나지 않도록 수정 추가 진행"
  - source: 사용자 확인 2026-10-06
- `constraint` 개인판과 사내판 agent-wiki를 한 머신에 함께 설치하면 두 세션 시작 훅이 같은 `wiki.baseRoot`(`~/.agent-wiki`)를 각자의 원격(GitHub `main`·Bitbucket `master`)으로 `remote set-url`·강제 checkout해 경합하므로, 나중에 끝난 쪽 위키를 다른 쪽 주입이 읽음 — `workspace.root`는 `{slug}` 폴더 단위 clone이고 두 위키 등록 slug가 겹치지 않아 공유해도 됨
  - evidence: agent-wiki/hooks/session_start.py, agent-wiki/scripts/sync_wiki.py
- `why` agent-wiki update 7절 커서 기록은 레포마다 Write한 뒤 `git add state` 커밋 1개로 남기고 `write_cursors.py` 스크립트는 두지 않음 — 실행 B의 잘못된 커서 파일명 커밋은 "레포마다 커밋" 지시를 메인이 셸 반복문으로 옮기다 zsh가 `set -- $p`를 단어 분리하지 않아 생겼으므로 반복 지시 자체를 없애면 되고, 스크립트는 "커서 파일도 에이전트가 씀"·스크립트 최소화 결정과 상충함
  - evidence: agent-wiki/skills/update/SKILL.md 7절
- `why` agent-wiki update 4장 대체 규칙을 "함께 참일 수 없는 앞 사실(deleted·부재 주장 포함, 레포 무관)"로 넓히는 제안은 기각함 — 현행 규칙의 `order`가 레포를 넘는 전역 순서라 위키 PR #24에서 다른 레포 뒤 머지로 거짓이 된 F11(부재 주장)·F53이 각각 F55·F56으로 `대체` 처리됐고, PR #23의 deleted F6과 현재 상태 F15는 `동일`·`추가`로 결과가 맞음
  - source: onestore-llm-wiki PR #23·#24 사실 목록
