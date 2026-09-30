# marketplace-version-sync 작업 기록

- `context` 해당 버전을 우리 프로젝트에도도입 단 회사 플러그인 레포의 커스텀 설정은 제외 — 사내 PR #107의 marketplace.json 변경 중 마켓플레이스 버전 올림만 개인판에 반영하고, 사내 전용 항목(플러그인별 version·description·author·keywords)은 가져오지 않음
  - source: 사용자 확인 2026-09-30
- `constraint` my-claude-plugin-market은 플러그인 버전을 올리는 PR마다 `.claude-plugin/marketplace.json`의 `metadata.version`도 함께 올리는 관례를 따르며(#28·#30·#31·#32), agent-wiki 0.6.1(#33)은 이를 빠뜨려 4.0.1로 보정함 — 플러그인별 version은 marketplace.json에 두지 않고 각 `plugin.json`이 원본임
  - evidence: .claude-plugin/marketplace.json
