# agent-wiki-migration 작업 기록

- `context` 기존 llm-wiki 를 agent-wiki로 이제 이전하려고 함 (llm-wiki는 이제 사용안할 예정, 사용자는 나뿐) — 기존 레포지토리 URL을 agent-wiki config 에 맞게 설정, 기존 llm-wiki의 레포지토리 내 문서들 삭제하고 registry, deps 만 새로운 양식에 맞게 작성, 처음 커밋부터 update 할 수 있도록 커서 설정, 기존 llm-wiki를 플러그인 목록에서 삭제
  - source: 사용자 확인 2026-09-30
- `constraint` agent-wiki update는 커서를 제외한 `{cursor}..origin/{defaultBranch}` first-parent 커밋만 읽으므로 커서를 최초 커밋으로 둬도 최초 커밋 자체는 반영되지 않으며, 위키 `argon1025-llm-wiki`의 pigeon-trade(최초 커밋 `4c2a4d4`, NestJS 스타터 골격)·pigeon-trade-dashboard(최초 커밋 `7370732`, 빈 커밋) 커서는 이 한계를 감수하고 최초 커밋으로 설정함
  - evidence: agent-wiki/scripts/collect_update_merges.py
