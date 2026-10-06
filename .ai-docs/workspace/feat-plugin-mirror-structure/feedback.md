# feat-plugin-mirror-structure 작업 기록

- `context` 나머지 플러그인도 함께 유지될 수 있도록 변경되는 항목 (예: 사내 빗버킷 mcp, 사내에서만 다르게 처리되어야하는 항목들)은 agent-wiki 처럼 별도의 문서로 관리되고 조합해서 사용하는 구조로 구조를 개편하고 사내판도 동일하게 버전 정합을 맞추려고 함 — 대상은 개인판 pr-workflow·plan-workflow·better-communication과 사내판 devcenter-pr·devcenter-flow·devcenter-comms이며, 범위는 구조 개편·버전 정합과 그 과정에서 드러난 낡은 문구 정리까지임
  - source: 사용자 확인 2026-10-06
- `context` 사내판 플러그인 이름(devcenter-pr·devcenter-flow·devcenter-comms)은 유지하고 공통 본문에서 플러그인 이름을 빼며, 한쪽에만 있던 내용 중 위키 연동(pr review Layer 2, planning 위키 대조, execute 위키 문서 선행 읽기, record-format 위키 편입)과 이슈 키 slug 규칙만 공통 본문으로 올리고, devcenter-comms의 NOTICE와 typescript-react 체크리스트의 lint 제외 절은 사내 고유로 남김
  - source: 사용자 확인 2026-10-06
- `constraint` 사내 cms·devcenter 25개 레포 develop의 공유 `.claude/settings.json`이 `devcenter-flow@onestore-devcenter`·`devcenter-comms@onestore-devcenter`·`devcenter-pr@onestore-devcenter`·`agent-wiki@onestore-devcenter` 키로 플러그인을 켜므로, 사내판 플러그인 이름을 바꾸면 25개 레포 설정 재배포와 marketplace `renames` 처리가 필요함
  - evidence: onestore-devcenter-claude-plugin-marketplace/.devcenter/workspace/progress/project-plugin-settings/feedback.md
- `constraint` Claude Code 플러그인 캐시는 `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/` 폴더 단위이고 이 머신에도 `onestore-devcenter/devcenter-flow/1.3.0` 같은 과거 버전 폴더가 남아 있으므로, 사내판 버전을 과거에 쓴 번호로 낮추면 옛 본문이 로드될 수 있음 — 개인판·사내판 공통 버전은 사내 이력(devcenter-pr 3.0.1, devcenter-flow 3.0.1과 marketplace 항목 3.1.0, devcenter-comms 4.0.0)보다 높게 잡음
- `why` 공통 버전을 pr 3.1.0·flow 3.2.0·comms 4.1.0으로 정해 개인판이 1.x에서 건너뛰게 한 이유는 위 캐시 충돌을 피하면서 사내판 쪽 버전 단조 증가를 지키기 위함이며, 개인판 버전 기준으로 사내판을 낮추는 대안은 기각함
  - source: 사용자 확인 2026-10-06
- `why` plan-workflow 훅은 `plugin.json`의 name과 `config.json`의 `workspace.root`를 읽어 규약의 `{PLUGIN_NAME}`·`{WORKSPACE_ROOT}`를 치환하지만, better-communication의 UserPromptSubmit 훅과 plan-workflow의 PostToolUse(ExitPlanMode) 훅은 리마인드 문구에서 플러그인 이름을 빼는 쪽을 택함 — 매 프롬프트마다 python을 기동해 JSON을 파싱하는 비용을 더하지 않고, 정확한 명령은 세션 시작 주입문이 이미 담고 있기 때문임
- `constraint` agent-wiki 세션 주입은 레포 전용 문서·도메인 공유 문서 목록만 싣고 `!` 미검증 표시나 '스페이스' 구분이 없으므로, 사내판 devcenter-pr의 Layer 2 문구(`!` 대조, `그룹 스페이스`·`레포 스페이스`)는 제거된 devcenter-wiki 시절 어휘이고 공통 본문으로 올릴 때 agent-wiki 어휘로 바꿔야 함
  - evidence: agent-wiki/hooks/session_start.py
  - evidence: onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-pr/skills/review/SKILL.md
- `context` 개인판 공통 파일 `agent-wiki/skills/add/SKILL.md` 24행 예시에 사내 경로 `.devcenter/workspace/progress/*/feedback.md`가 남아 있으나, 이번 범위에서는 agent-wiki를 바꾸지 않고 후속 작업으로 남김
  - evidence: agent-wiki/skills/add/SKILL.md
