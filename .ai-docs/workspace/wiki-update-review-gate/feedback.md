# wiki-update-review-gate 작업 기록

- `context` 기계식 검증은 진짜 확실하게 걸러 낼 수 있는 사항에만 적용하고 나머지 의미없는 게이트는 제거, 수정 후 서브에이전트로 의미론적 위반까지 잡는 구조로 감
  - source: 사용자 확인 2026-09-25
- `context` llm-wiki 규약 1장 담지 않는 것 기준은 CI·린터가 없는 프로젝트에도 통하는 전역 기준이어야 하며, update 추출 입력은 테스트 포함 git diff 전체를 누락 없이 넣고 입력 종류별 제외 조항을 두지 않음
  - source: 사용자 확인 2026-09-25
- `why` llm-wiki 리뷰 문서의 개선안 중 추출 출력 기각 칸·검색 문구 기재·catalog.py 불릿 길이 검사·신규 문서 최소 3건·추출 Opus 전환은 기각함 — 단일 판정 질문과 반영 뒤 검토 에이전트가 같은 위반을 포섭하고, 이번 위반은 Opus 추출에서도 발생해 모델이 원인이 아님
  - source: 사용자 확인 2026-09-25
- `correction` 리뷰 문서는 토스 명세 세부(응답 envelope·nullable)를 레포 문서로 옮기라고 했으나, 외부 서비스 사실이고 도메인 루트 `toss-openapi-constraints.md`와 한 주제이므로 도메인 루트 배치가 맞음
  - source: 사용자 확인 2026-09-25
- `constraint` llm-wiki update 검토 에이전트는 이번 변경 줄과 description만 고치고 기존 줄은 무인 삭제하지 않음 — 기존 줄 정리는 사용자 승인을 거치는 audit 몫
- `constraint` update 검토 에이전트의 1장 판정은 `git grep {패턴} {sha}`·`git show {sha}:{경로}`처럼 머지 sha를 명시해야 함 — rev 없는 `git grep`은 로컬 작업 트리를 읽어 머지 시점이 아닌 현재 코드로 판정하게 되고, 한 문서에 여러 레포 사실이 섞이면 근거도 레포별 `path@sha` 목록으로 넘김
  - source: plan 실행 중 확인 2026-09-25
