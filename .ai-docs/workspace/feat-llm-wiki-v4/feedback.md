# feat-llm-wiki-v4 작업 기록

- `context` 반영 범위는 4.0.0 합의 모델(등급·출처·verified·낡음·inbox 제거, update 무인 전역 시간순)까지 전부이며, 노드 `project`는 GitHub owner URL로 두고, view.py·templates/graph.html을 포함하며, `~/.ai-docs/wiki` 데이터 이관은 이번 작업에서 하지 않고 README 안내만 둠
  - source: 사용자 확인 2026-09-25
- `context` llm-wiki README·커밋 메시지·작업 기록에는 다른 조직 저장소와의 비교나 그 식별자를 적지 않고 이번에 바뀐 내용만 서술함
  - source: 사용자 확인 2026-09-25
- `why` llm-wiki는 PR 게이트 없이 스킬 끝에서 직접 `git pull --rebase && git push`를 하므로, 건너뛴 사실은 inbox 파일 대신 스킬 최종 보고의 건너뜀 표에 남기고 교체 결정은 커밋 본문 `기존/새` 줄에 남김
- `constraint` 개인 위키 `~/.ai-docs/wiki`의 registry.json은 3.x 스키마(`remotes` 배열·`domain` 필드)라 4.0.0 graph.py check에서 에러가 나며, 문서 wiki-fact-tier-authority·wiki-fact-reverification는 등급·verified 체계를 전제로 해 4.0.0 모델과 모순되므로 설치 후 register --resurvey와 audit 대상임
  - evidence: ~/.ai-docs/wiki/registry.json, ~/.ai-docs/wiki/knowledge/argon1025-side/my-claude-plugin-market/
- `constraint` llm-wiki 4.0.0의 graph.py·view.py는 위키 루트를 `--wiki PATH`로 받고 render는 `--domain NAME --slug SLUG`로 대상 레포를 지정하며, catalog.py만 `--root {WIKI}/knowledge`를 받음
  - evidence: llm-wiki/scripts/graph.py, llm-wiki/scripts/view.py
- `why` llm-wiki 4.0.0의 graph.py는 노드 `project`를 `https://{host}/{owner}` 한 단 경로로 제한하고 clone 패턴을 `{host}/{owner}/{slug}`로 파생하며, 전 노드의 owner가 하나일 때만 패턴에 owner 값을 그대로 싣고 여럿이면 `{owner}` 자리표시를 둠 — owner가 섞인 위키에서도 remote가 규칙과 다른 노드만 지도 행에 나오게 하려는 선택
  - evidence: llm-wiki/scripts/graph.py (remote_pattern, owner_label)
- `context` llm-wiki 4.0.0은 inbox가 없어 update·audit가 건너뛴 사실이 위키 파일에 남지 않고 실행 최종 보고의 건너뜀 표에만 실리며, 무인 실행의 건너뜀은 그 보고를 받아 `/llm-wiki:add`로 넘겨야 하는 의도적 단순화의 한계임
  - evidence: llm-wiki/references/doc-contract.md (8장 건너뜀 보고), llm-wiki/README.md (한계)
