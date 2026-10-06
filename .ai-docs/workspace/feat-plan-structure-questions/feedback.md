# feat-plan-structure-questions 작업 기록

- `context` plan-workflow planning 스킬 개선 작업이며 사용자 원문은 "트레이드 오프를 잘 하면 깔끔한 구조로 갈 수 있음에도 기존 묻지 않고 기존 코드를 살려서 작업", "질문을 할 대 어디를 어떻게 변경할것이며에 대한 설명 없이 그냥 선택지만 노출함", "앞선 질문의 답에 따라 분기가 갈림에도 질문을 몰아서 하는 경우가 있음 (뒷 질문이 무의미 해지는 케이스)", "그래서 계속 중간중간 replan 을 하는 경우가 있었음 완성해보니 이상해서", "다 반영할 필요는 없음 담당자로써 비판적으로검토하여 수용여부를 검토 (최우선 목표는 간결한 구조와 프롬프트)"이고, 범위는 개인판 plan-workflow와 사내판 devcenter-flow 미러링까지임
  - source: 사용자 확인 2026-10-06
- `why` plan-workflow planning SKILL.md의 기존 코드 유지 편향은 3절 `구조` 축(무엇을 물을지)과 4절 `기존 코드` 판정(무엇이 최소인지)으로 나눠 고치며, 3절 하나로 합치는 안은 4절 사다리가 "새 코드 단위마다"로 남아 ② "코드베이스에 이미 있음"을 통한 기존 코드 재사용이 그대로 통과하므로 기각함
  - source: 사용자 확인 2026-10-06
- `why` plan-workflow planning에서 기존 코드 재편·삭제는 에이전트가 자율 수행하지 않고 지울 범위와 함께 후보로만 올리며, 하네스 기본 지침의 범위 밖 리팩터링 억제·외부 계약 파손·리뷰 diff 증가를 피하고 결정권을 사용자에게 두기 위함임
  - source: 사용자 확인 2026-10-06
- `why` plan-workflow planning 5절 `독립 라운드`의 미룸 기준은 "문구가 바뀌는 질문"이 아니라 "필요 여부나 선택지가 바뀌는 질문"이어야 하며, 문구는 같고 앞 답에 따라 필요성만 사라지는 질문(중계 페이지 제거 여부보다 먼저 물은 [확인] 버튼 반영 시점 질문)이 앞 기준으로는 걸러지지 않았음
  - evidence: onestore-cmsapp-front/.devcenter/workspace/progress/CMSAPP-2396/plan.md
- `why` plan-workflow plan.md 형식에 결과 구조 절을 신설하지 않는 것은 질문 단계의 AskUserQuestion preview로 승인 전에 구조를 확인하게 하여 plan-format 절 증가를 피하기 위함임
  - source: 사용자 확인 2026-10-06
- `constraint` 사내판 마켓플레이스의 marketplace.json은 플러그인별 version 항목이 있어 devcenter-flow 버전을 plugin.json과 marketplace 항목 두 곳에서 올리고 최상위 version도 올려야 하며, 개인판 marketplace.json에는 플러그인별 version이 없어 plugin.json과 metadata.version만 올림
  - evidence: onestore-devcenter-claude-plugin-marketplace/.claude-plugin/marketplace.json
- `context` plan-workflow 구조 질문 개선의 검증은 문구·순서·버전의 정적 확인까지이며, 실제 효과는 후속으로 이후 계획 파일의 Re-plan·추가 계획 계기 중 구조 재편·불필요 코드 제거 비율(개선 전 51절 중 17절)이 줄었는지로 확인함
