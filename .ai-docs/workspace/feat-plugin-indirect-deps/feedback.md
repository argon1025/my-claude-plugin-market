# feat-plugin-indirect-deps 작업 기록

- `context` 일단 두곳이 각 각 별도의 플러그인으로 유지되길 바람 — 꼭 두곳이 직접적인 의존을 하지 않더라도 간접적인 의존을 할 수 있음, 각 스킬간에 이런 의존 문구들이 있으면 간접 의존 문구로 변경하고자 함 (대상은 agent-wiki·plan-workflow·pr-workflow 등 전체 플러그인이며, 고치는 대목은 기존 문구를 유지한 채 단어만 바꾸지 않고 필요성을 검토해 재작성함)
  - source: 사용자 확인 2026-10-06
- `constraint` 이 마켓플레이스의 플러그인 본문은 다른 플러그인의 이름·명령(`/agent-wiki:add` 등)·파일명(`plan.md`·`feedback.md`)·내부 구조(레포 전용·도메인 공유 문서, 기록 폴더 경로)를 지목하지 않고, "세션에 주입된 사전 정보(위키·문서 목록·작업 기록)가 있으면 찾아 읽고 코드로 확인함"처럼 세션 컨텍스트에 있을 때만 쓰는 간접 문구로 적음 — 각 플러그인은 단독 설치로도 문구가 틀리지 않아야 함
  - source: 사용자 확인 2026-10-06
- `why` pr-workflow review의 Layer 2 부재 안내(agent-wiki 미설치·미등록 1회 알림)와 구 룰 파일 `.claude/pr-review-rules.md`의 `/agent-wiki:add` 이관 안내는 다른 플러그인 설치·명령을 지목하는 직접 의존이라 삭제했고, Layer 2 부재는 보고의 `적용 룰 소스` Layer 2 칸에 `없음`으로만 드러냄
- `why` plan-workflow `plan.md`의 `## 선행 읽기`는 세션 주입 문서를 카탈로그 표기 대신 절대 경로로 적음 — 실행은 새 세션에서 시작하므로 주입 형식에 기대지 않고도 열려야 함
- `correction` plan-workflow record-format이 적던 "`source:` 지목이 없는 `feedback.md` 항목은 agent-wiki add가 코드 관찰로 취급함"은 agent-wiki add 본문에 없는 규칙이며, add는 자료마다 근거 줄(파일 경로 등)을 붙이고 같은 대상의 값 충돌은 개정 일자·판본으로 가림
  - evidence: agent-wiki/skills/add/SKILL.md
- `context` 머지 후 위키 `plan-workflow-records`(agent-wiki add가 feedback.md를 입력으로 받는다는 규칙 2개)와 `pr-workflow-skills`(review Layer 2가 agent-wiki 문서 목록을 쓴다는 규칙, 목록 부재 1회 알림, 구 룰 파일 이관 안내)가 본문과 어긋나므로 위키 반영이 후속 작업이며, 사내판 devcenter-pr·devcenter-flow 공통 본문 rsync와 사내 고유 README의 같은 문구 수정, 사내판 agent-wiki add·update 미러링도 후속 작업임
