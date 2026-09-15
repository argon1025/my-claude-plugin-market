# feat-plan-handoff-format 작업 기록

- `context` 사용자 원문 "계획 작성 완료 후 다음은 execute 실행 안내하며 계획모드에서 바로 구현으로 넘어가지 않고 종료 되도록 구성", "기존 계획 산출물 참고해서 계획 파일에 필수로 들어가야하는 항목을 정의해두는건 어떨까함", "이후 이 플러그인들 깔끔한거같아서 기존 회사 플러그인도 이 플러그인으로 교체하려고 함", "너의 최우선은 플러그인을 깔끔한 구조로 잘 유지하는것임" — plan-workflow는 사내 devcenter-flow의 대체 대상이며 구조 단순함이 기능 추가보다 우선한다.
  - source: 사용자 확인 2026-09-15
- `correction` planning 스킬 7절의 "정지" 불릿만으로는 승인 후 구현 진입을 막지 못한다 — PR #8에서 계획 스냅샷 커밋 4525329 뒤 57초 만에 같은 세션의 구현 커밋 275c355가 이어졌고, 원인은 ExitPlanMode 승인 결과에 하네스가 "구현을 시작하라"는 지시를 함께 넣기 때문이다.
  - evidence: git log 4525329..275c355
- `why` 승인 후 정지를 PostToolUse(ExitPlanMode) 훅의 additionalContext 주입으로 구현하는 이유는 하네스 지시와 같은 시점에 반대 지시를 넣을 수 있는 유일한 자리이기 때문이며, 대안인 스킬 문구 강화만은 밀린 사례가 있어 기각했고 PreToolUse(Edit·Write) 차단 훅은 세션 상태 판별이 필요해 재발 시 업그레이드 조건으로만 남겼다. 공식 문서 기준 PostToolUse는 도구 성공 시에만 발화하므로 플랜 거절에는 걸리지 않는다.
  - source: 사용자 확인 2026-09-15
- `why` devcenter-flow 요소 중 Jira 키 slug·ponytail 주석·위키 대조 문구·UserPromptSubmit 리마인더 훅을 plan-workflow에 들이지 않는 이유는 각각 회사 종속, v1에서 기각, 플러그인 독립 원칙 위반, 사용자 미선택이며, 선행 읽기 절과 영향 범위 확인 축만 일반화하여 채택했다.
  - source: 사용자 확인 2026-09-15
- `context` plan.md 필수 절 규정은 SKILL.md가 아니라 references/plan-format.md에 두어 record-format.md와 같은 지연 로드 방식을 유지한다 — 상시 주입되는 agent-guide.md와 스킬 본문 분량을 늘리지 않기 위함이다.
  - source: 사용자 확인 2026-09-15
- `why` plan.md의 선택 절 `## 배경`은 `## 의도`와 `## 확정 결정` 사이에 두며, 계획 스냅샷이 같은 불릿에서 "확정 결정 앞"과 "확정 결정과 작업 사이"를 함께 적어 어긋난 것을 조사 결과를 먼저 읽고 결정을 보게 하는 쪽으로 정한 것이다 — `## 외부 계약`·`## 선행 읽기`만 확정 결정과 작업 사이에 남는다.
  - source: 사용자 확인 2026-09-15
- `constraint` 스킬 본문(SKILL.md)의 `{PLUGIN_ROOT}` 토큰은 치환되지 않는다 — 치환은 session_start.sh가 rules/agent-guide.md를 주입할 때만 하므로, 스킬을 읽는 에이전트는 주입된 agent-guide.md의 절대 경로나 스킬 base directory의 상위 두 단계로 직접 해석해야 한다.
  - evidence: plan-workflow/hooks/session_start.sh
