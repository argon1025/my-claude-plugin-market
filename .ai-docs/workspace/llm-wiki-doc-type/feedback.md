# llm-wiki-doc-type 작업 기록

- `context` 문서가 분류가 없음으로 좀 너무 자유로운 느낌이 듬. 이후에 정책, 컨벤션, 도메인 관련된것들이 나올 수 있을 것 같음. 이런걸 미리 프론트메터나 그런걸로 분류해야 섞이지 않고 문서 당 한 주제 씩 자세히 기록되는게 유지될 듯 함
  - source: 사용자 확인 2026-09-25
- `why` llm-wiki 문서 유형은 사용자 제안 3종(정책·컨벤션·도메인)이 아니라 policy·domain·convention·external·procedure 5종과 adr로 정함 — 기존 위키의 외부 제약 문서(toss-openapi-constraints)와 절차 문서(branch-and-deploy)가 3종에 들어갈 자리가 없음
- `why` llm-wiki 유형별 절 제목은 고정하지 않고 권장 골격으로만 둠 — 기존 문서가 내용별 절 제목으로 주제를 나누고 있어 고정 시 가독성이 떨어짐
- `constraint` llm-wiki update 스킬은 `catalog.py --check` 에러가 남은 편집 문서를 원복하므로, type이 필수 키가 된 뒤 type 없는 기존 문서에 사실을 반영하면 사실이 보고 없이 사라짐 — update는 type 없음 에러가 있으면 audit 안내 후 중단해야 함
  - evidence: llm-wiki/skills/update/SKILL.md
- `constraint` llm-wiki audit의 `분할 후보`는 승인 대상이지만 4장 적용 에이전트가 대상 문서 밖 파일을 만들 수 없어 실제 분할은 되지 않고 6장 보고에만 남음 — `external-integration-layer.md` 토스 절 분리처럼 유형이 섞인 문서는 audit 뒤 별도 후속 작업이 필요함
  - evidence: llm-wiki/skills/audit/SKILL.md
- `constraint` llm-wiki update·add의 type 선행 검사는 `knowledge/` 전체를 보지만 audit 기본 범위는 현재 도메인 루트와 현재 레포 폴더뿐이라, 다른 레포 폴더에 type 에러 문서가 남으면 update·add가 계속 중단됨 — 이관 시 레포 폴더마다 `--scope {domain}/{slug}`로 audit을 돌려야 함
  - evidence: llm-wiki/skills/update/SKILL.md, llm-wiki/skills/audit/SKILL.md
