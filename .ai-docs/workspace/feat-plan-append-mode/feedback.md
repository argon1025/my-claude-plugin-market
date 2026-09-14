# feat-plan-append-mode 작업 기록

- `context` plan-workflow의 planning 스킬이 같은 브랜치에서 재호출될 때 기존 plan.md를 전면 교체하던 동작을 추가 절 덧붙이기로 바꾸는 작업이며, 사용자 원문은 "기존 계획 내용은 유지하고 add-plan 을 plan.md 하위에 append 하는 방향으로 개선 검토"임
  - source: 사용자 확인 2026-09-14
- `why` 추가 절 실행 여부를 plan.md에 상태 마커나 선행 커밋 해시로 적지 않고 execute가 git log·코드로 매번 판정하게 한 것은, 승인된 스냅샷을 사후에 고치지 않는다는 plan-workflow 원칙을 깨지 않기 위함임
  - source: 사용자 확인 2026-09-14
- `why` planning의 `## 추가 계획`과 execute의 `## Re-plan` 절을 한 이름으로 합치지 않은 것은 신규 요구와 실행 중 현실 괴리가 작성 주체·실행 의미에서 다르기 때문이며, 날짜 뒤 계기 한 줄을 붙이는 형식만 공통으로 둠
  - source: 사용자 확인 2026-09-14
- `constraint` plan-workflow의 rules/agent-guide.md는 SessionStart 훅이 모든 세션에 전문 주입하므로 분량 증가가 상시 비용이며, 상세 규칙은 스킬 본문이나 references로 내림
  - evidence: plan-workflow/hooks/session_start.sh
