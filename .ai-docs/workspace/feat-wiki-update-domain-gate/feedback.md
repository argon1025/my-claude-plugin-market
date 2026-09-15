# feat-wiki-update-domain-gate 작업 기록

- `context` 사용자 원문 "현재는 전체 레포들의 머지분을 들고오나 향후엔 도메인별 하위에 많은 레포들이 있을 예정이라 먼저 어떤 도메인의 레포들을 문서화할 것인지를 받고 진행 했으면 함" — llm-wiki update는 도메인 단위로만 대상을 받고 레포 단위 재선택 단계는 두지 않으며, 등록 도메인이 하나뿐이어도 항상 확인한다.
  - source: 사용자 확인 2026-09-15
- `constraint` llm-wiki `update.py domains`의 미반영 커밋 수는 `git fetch` 없이 로컬 `origin/{branch}` 기준이라 세션 시작 훅이 내는 "HEAD보다 N커밋 뒤"와 값이 다르다 — 훅은 로컬 HEAD를 세고 domains와 pending은 원격 추적 ref를 세므로, 푸시하지 않은 브랜치 커밋은 훅에만 잡힌다.
  - evidence: llm-wiki/scripts/update.py `repo_status`, llm-wiki/hooks/session_start.sh
- `why` 도메인 선택 질문 앞단에서 `git fetch`를 돌리지 않는 것은 레포가 수십 개로 늘 때 질문이 뜨기까지의 지연이 선택 정확도보다 크기 때문이며, 대신 출력 끝에 fetch 전 기준임을 한 줄로 밝히고 실제 처리량은 뒤이은 pending이 fetch 후 확정한다.
  - source: 사용자 확인 2026-09-15
