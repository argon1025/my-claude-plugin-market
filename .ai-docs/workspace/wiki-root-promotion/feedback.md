# wiki-root-promotion 작업 기록

- `context` update를 몇 번 돌려 보니 stock-identifiers.md 같은 문서는 공통 레벨 문서로 승격되어야 할 것 같음(예: 종목 식별은 서비스 고유로 정의된다는 사실), 지금 공통 문서는 계속 업데이트되지 않음 — 규약 3장 위치 판정과 audit 승격 신호를 고치는 방향으로 합의함
  - source: 사용자 확인 2026-09-25
- `correction` llm-wiki 규약 3장의 옛 위치 판정("모르고 개발하면 다른 레포에서 문제가 되는가")은 도메인에 등록 레포가 하나뿐이면 항상 거짓이라, personal-stock-trading에서 update가 만든 신규 문서 11장이 모두 레포 폴더로 감 — 레포 밖 소비자(Jev·메인 에이전트·대시보드)는 등록 레포가 아니어서 판정에 잡히지 않음
  - evidence: llm-wiki/references/doc-contract.md
- `why` 위치 판정은 등록 레포 수와 무관하게 사실이 보이는 범위(레포 경계 밖에서 통하는가)로 가름 — 레포를 하나 더 등록해야 루트 문서가 생기는 구조는 도메인 규모와 무관한 사실(업무 용어·식별 체계)을 레포 폴더에 가둠
- `constraint` llm-wiki audit 적용 에이전트는 대상 문서 밖 파일을 만들지 못하므로, 레포 폴더에서 도메인 루트로 옮기는 `승격`은 대상 루트 문서 에이전트가 추가(신규면 생성)하고 원 문서 에이전트가 원 불릿을 지우는 두 쪽 행으로 나눠 적용해야 함
  - evidence: llm-wiki/skills/audit/SKILL.md
- `why` llm-wiki 규약 3장은 레포 밖 소비자가 겪는 동작(받는 입력·응답·없는 기능)을 그 레포의 한계여도 도메인 루트에 두고 구현 원인만 레포 폴더에 둠 — personal-stock-trading 드라이런에서 "등록 입력이 곧 토스 심볼", "동기화 플래그 수정 API 없음"이 레포 한계와 소비자 약속 양쪽에 걸려 판정이 갈림
- `constraint` llm-wiki audit의 되돌림은 문서 단위 checkout이라, 루트 문서 하나가 여러 원본의 승격을 받을 때 짝 단위로 되돌리면 이미 불릿을 뺀 다른 원본의 사실이 사라짐 — 승격 행으로 이어진 문서 전체를 한 묶음으로 되돌려야 함
  - evidence: llm-wiki/skills/audit/SKILL.md
- `constraint` llm-wiki audit 승격은 레포 `adr/` 문서를 제외함 — 원 문서 type(adr)을 이어받은 신규 문서가 루트 평면에 생기면 catalog 검사("type adr은 adr/ 폴더 문서만")에 걸림
  - evidence: llm-wiki/scripts/catalog.py
- `why` llm-wiki audit은 승격 전용 조치를 따로 두지 않고 흡수·분할 후보·승격을 문서 사이 불릿 이동 하나(`옮김`)로 합침 — 셋 모두 "원본에서 빼고 대상(기존 또는 신규)에 넣음"이라 조치별 예외 문장(흡수 조각 충돌, 원 문서 type 상속)이 쌓였음
  - source: 사용자 확인 2026-09-25
- `correction` llm-wiki audit의 `분할 후보`가 보고에만 남던 한계는 `옮김`이 신규 문서를 만들 수 있게 되어 해소됨 — 유형이 섞인 문서도 audit 한 번으로 실제 분할됨
  - evidence: llm-wiki/skills/audit/SKILL.md
- `context` llm-wiki 스킬·규약 수정은 기존 문장을 두고 영향 부분만 덧대지 말고, 필요성을 따져 삭제·재구성까지 검토함
  - source: 사용자 확인 2026-09-25
