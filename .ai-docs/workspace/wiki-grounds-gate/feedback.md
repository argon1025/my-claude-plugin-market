# wiki-grounds-gate 작업 기록

- `context` 기본적으로 문서를 신뢰하되 사용자가 맥락을 설명(개정됨, 다시 바뀜, 논의됨) 되어 납득된 경우 그것 문서보다 사용자 의견을 신뢰하고 진행하는것임 이것이 이제 plan, feedback 문서에 기록되고 향후 auto 업데이트에서도 반영 되는거고 비 정기적으로 실행되는 add 에서도 동일하게 적용 되는거고.. 이런 전체적인 라이프 사이클로 가져가면 어떨까함
  - source: 사용자 확인 2026-09-14
- `context` 세부 위키 개정이력은 git history 로 사유 기록 해두면 파일 내부에 굳이 기록 안해도 될듯함
  - source: 사용자 확인 2026-09-14
- `why` llm-wiki에서 사용자가 건넨 사실의 정지점 기준을 "충돌인가"가 아니라 "근거가 있는가"로 잡음 — 오정보·향후 변경될 정책·개정 세 유형 중 오정보만 자기 신고가 불가능하고, 코드 대조를 트리거로 삼으면 코드에 근거가 없는 정책 사실을 거를 수 없어 기각함
- `why` 개정된 값이 코드와 어긋나도 llm-wiki 문서에 코드 미반영 표식을 두지 않음 — 코드가 따라오면 update의 `동일` 판정이 verified를 갱신해 수명주기가 닫히므로 표식이 중복이며, 사용자가 레포별로 후속 작업을 진행함
  - evidence: llm-wiki/skills/update/SKILL.md
- `constraint` llm-wiki의 출처 줄은 catalog.py·update.py 어디에서도 파싱되지 않는 순수 규약 영역이라 출처 식별자 규격을 바꿔도 기계 검사에 걸리지 않음
  - evidence: llm-wiki/scripts/catalog.py, llm-wiki/scripts/update.py
- `constraint` llm-wiki에서 기존 값을 덮을 수 있는 출처는 `확인` 등급뿐이고 `관찰`(update)은 보강만 가능하므로, 잘못 들어간 `확인` 값은 무인 갱신으로 교정되지 않고 실행마다 inbox.md에 같은 충돌 행을 다시 쌓음
  - evidence: llm-wiki/references/doc-contract.md, llm-wiki/skills/update/SKILL.md
- `constraint` llm-wiki의 세션 훅은 inbox.md에서 `- [`로 시작하는 줄만 세어 확인 필요 건수를 표시하므로 inbox 행은 그 형식을 벗어나면 집계되지 않음
  - evidence: llm-wiki/hooks/session_start.sh
- `context` llm-wiki 규약은 plan-workflow의 feedback.md를 가리키지 않음 — 세션 기록은 plan-workflow 소관이고 llm-wiki가 단독 설치되어도 규약이 참이어야 함
  - source: 사용자 확인 2026-09-14
- `context` audit의 `검증` 조치가 무승인으로 verified를 갱신해 doc-contract 4장 "대조 없이 verified 갱신 금지"와 충돌하는 문제는 이번 범위에서 제외하고 후속 과제로 남김
