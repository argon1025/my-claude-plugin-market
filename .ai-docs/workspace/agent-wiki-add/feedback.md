# agent-wiki-add 작업 기록

- `context` agent-wiki add 스킬은 사용자가 넘긴 자유 양식 자료에서 사실을 추출해 목록으로 보이고 위키에 반영하며, 사용자 문장은 "내가 넘긴 사실(문서 등 자유양식) 에 대해서 사실을 추출하여 리스트업 하고 그것을 위키에 반영했으면 함 사실 추출 까지가 update와 다른점이고 이후 문서반영은 구조 동일해도 무방할 것 같음"임 — 배정·반영·검토·지도 갱신·커밋은 `agent-wiki/references/apply.md`로 update와 공유함
  - source: 사용자 확인 2026-09-29
- `correction` agent-wiki update는 `registry.json`·`deps.json`을 고치지 않는다는 이전 결정(`.ai-docs/workspace/agent-wiki-update-review/plan.md` 확정 결정의 그래프 불변)은 폐기되었고, update·add 모두 diff·자료로 바뀐 책임·간선·호스트를 갱신할 의무를 가짐 — 사용자 문장 "update, add 전부 registry.json·deps.json 도 최신화를 해야하는 의무를 가져야함 항상 register 를 할 수 없기 때문 물론 책임, 의존성 등 diff 으로 인해 변경되는 사항만 대상임"
  - source: 사용자 확인 2026-09-29
- `context` 레포 지도 값 규칙(stack·summary·responsibilities·hosts·간선 정의)은 `agent-wiki/references/doc-contract.md` 9장 한 곳에 두고 register·update·add가 모두 인용함 — 사용자 문장 "update, add 전부 그래프 갱신, register 갱신 포함임 서로 다를 이유는 없어보임"이며, update·add의 편집 범위는 `responsibilities`·`hosts`·자기 간선이고 `stack`·`summary`·`remote`·`defaultBranch`·`status`는 register 소관임
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki add는 사실 목록 제시·질문 1회 뒤 `wiki-add/{YYYYMMDD-HHMM}` 브랜치 PR로 게시하고 PR 머지가 초안 승인을 대신하며, 모델 호출을 허용하고 세션 규칙 문구에 `/agent-wiki:add` 안내를 덧붙임
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki add의 커밋 근거는 형식을 강제하지 않고 원문을 역추적할 수 있는 값(파일 경로·sha, 페이지 URL, PR 링크·F번호, 자료 제목, `사용자 확인 YYYY-MM-DD`)을 예시로만 둠 — 사용자 문장 "그냥 너무 빡쎄게 제한하지말고 역추적할 수 있는 값 정도로만 가이드 하면될듯"
  - source: 사용자 확인 2026-09-29
- `context` 이번 작업은 update 지도 갱신을 실제 onestore-cmsapp 머지와 기존 S1·S3로 재검증하고 register·add도 실제 레포·실제 작업 기록으로 검증하며, 산출물은 공개 저장소에 커밋하지 않고 스크래치에만 둠
  - source: 사용자 확인 2026-09-29
- `constraint` agent-wiki 지도 값 규칙은 현재 `agent-wiki/skills/register/SKILL.md` 4절 에이전트 프롬프트 안에만 있고, 세션 레포 지도는 `responsibilities`(없으면 `summary`)와 `deps`의 그룹 키·`to`만 읽음
  - evidence: agent-wiki/skills/register/SKILL.md, agent-wiki/scripts/generate_repository_map.py
