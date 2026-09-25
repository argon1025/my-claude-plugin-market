# llm-wiki 문서 유형(type) 도입

## Context

- **문제**: 문서에 분류가 없어 한 문서에 성격이 다른 사실이 섞임 — 실제 사례 `pigeon-trade/external-integration-layer.md`는 코드 구성 컨벤션(폴더·예외·토큰) 5절과 토스 명세 함정 1절이 한 문서에 있고, description도 "외부 연동을 추가하거나 토스 API 호출부를 다룰 때"로 두 트리거를 묶음
- **원인**: 규약 2장 "한 주제"가 주제 축만 보고 사실의 성격 축을 보지 않음, 4장 골격(규칙·절차·용어·adr)은 이미 암묵적 유형이지만 "권장"이라 쓰는 쪽(update·add)이 판정에 쓰지 않음
- **목표**: 문서마다 유형 하나를 frontmatter로 고정하고, update·add가 사실에 유형을 먼저 붙인 뒤 같은 유형 문서에만 배정하게 하여 "문서 1장 = 유형 1개 × 주제 1개" 유지
- **요청 검토 결과**: 방향 수용, 단 사용자 제안 3종(정책·컨벤션·도메인)으로는 기존 문서 8장 중 `toss-openapi-constraints`(외부 제약)·`branch-and-deploy`(절차)가 들어갈 자리가 없어 5종으로 확장, 절 제목 고정은 기존 문서의 내용별 절 제목(`## 토큰과 자격증명` 등)을 해치므로 도입하지 않음

## 유형 정의 (규약 1장 "담는 것" 불릿을 이 표로 대체)

| type | 담는 것 | 답하는 질문 | 현재 문서 배정 |
|---|---|---|---|
| `policy` | 업무 규칙·판정 기준·범위·역할 경계 | 무엇이 허용·금지되고 어떻게 판정하는가 | mvp-scope, mvp-validation-criteria, system-roles, strategy-rule-promotion |
| `domain` | 용어·상태와 전이·코드값 매핑 | 이 낱말·상태·코드는 무엇을 뜻하고 어디로 바뀌는가 | 없음 |
| `convention` | 같은 종류의 이후 작업이 따를 코드 구성 방식, 연동 인터페이스 형태, 기각 대안 | 새로 만들 때 어떤 모양으로 짜는가 | external-integration-layer(토스 절 제외), lint-format-tooling |
| `external` | 외부 시스템 제약·명세 함정·계정·한도 | 외부 시스템이 무엇을 강제하는가 | toss-openapi-constraints |
| `procedure` | 반복 절차·운영·배포 경로 | 어떤 순서로 수행하고 실패 시 어떻게 분기하는가 | branch-and-deploy |

- **adr/**: 폴더로 이미 구분되므로 type 값 `adr` 고정
- **값 표기**: 기계 판정용이라 영문 enum, 목록에는 `name — [type] description`으로 노출

## 변경 사항

### 1. `llm-wiki/references/doc-contract.md`

- **1장**: "담는 것" 불릿을 위 유형 표로 교체, "판정" 불릿 뒤에 "사실마다 유형 하나를 먼저 정하고 둘에 걸치면 두 사실로 나눔" 추가 — update 추출 프롬프트가 1장만 `sed`로 읽으므로 추출 단계에 자동 전달됨
- **2장 한 주제**: "한 문서 = 유형 1개 × 주제 1개, 유형이 다른 사실은 같은 주제라도 다른 문서" 추가
- **4장 frontmatter**: `description`·`type` 2키, 권장 골격을 유형별로 재배치(policy `## 적용 대상`·`## 규칙`·`## 예외`, domain `## 용어`·`## 상태와 전이`·`## 코드값`, procedure `## 트리거`·`## 단계`·`## 분기와 실패`, adr 기존 유지) — 절 제목은 계속 변경 가능
- **7장 대조**: 대상 문서 후보는 같은 type만, 같은 type 문서가 없으면 신규

### 2. `llm-wiki/scripts/catalog.py`

- **키 검사**: `REQUIRED_FIELDS`에 `type` 추가, `TYPES = ("policy","domain","convention","external","procedure","adr")` enum 검사, `adr/` 경로 문서는 `adr` 강제·그 밖은 `adr` 금지 (`check_fields`·`inspect` 확장, 경로는 기존 `LOCATION_RE` 결과 재사용)
- **목록 행**: `build`의 행 형식을 `{name} — [{type}] {description}`로, type 없으면 `[?]`로 남기고 행은 빼지 않음(기존 "문서를 목록에서 빼지 않음" 원칙 유지)

### 3. `llm-wiki/skills/update/SKILL.md`

- **1장 선행 검사**: `catalog.py --check` 결과에 `type 없음`이 있으면 "먼저 `/llm-wiki:audit`" 보고 후 중단 — 유형 없는 문서를 편집하면 6장 되돌림 규칙에 걸려 사실이 조용히 사라지기 때문
- **2장 추출 스키마**: fact 객체에 `"type": "policy|domain|convention|external|procedure"` 추가
- **3장 배정**: 대조 후보를 같은 type으로 한정, 신규 문서 행에 type 기록
- **4장 반영**: 신규 문서는 배정표의 type을 frontmatter에 씀
- **5장 검토**: 문서 type과 다른 질문에 답하는 새 불릿은 `removed` 사유 `유형 불일치`로 — 7장 삭제 표로 복구 근거 보존

### 4. `llm-wiki/skills/add/SKILL.md`

- **2장**: 사실마다 type 부여, **3장**: 같은 type 문서 우선, **5장 초안**: 문서별 type 표시

### 5. `llm-wiki/skills/audit/SKILL.md`

- **신호 2행 추가**: `type 없음` 힌트 문서는 `유형` 조치(후: 판정 type) — 승인 불필요 목록에 포함, 문서 type과 다른 유형의 불릿 묶음은 `분할 후보`(후: 새 문서 type·경로) — 승인 대상
- **이관 경로**: 업그레이드 뒤 첫 audit이 기존 문서 전부에 type을 붙이는 이관을 겸함

### 6. 기타

- **README**: `llm-wiki/README.md` 58행 "frontmatter는 `description`만" 문장과 80행 갱신
- **버전**: `llm-wiki/.claude-plugin/plugin.json` 4.1.1 → 5.0.0 — 필수 키 추가로 기존 위키가 `--check` 에러를 내는 비호환 변경

## 범위 밖

- **위키 본문 이관**: `/Users/rok/.ai-docs/wiki` 문서 8장의 type 부여와 `external-integration-layer.md` 토스 절 분리는 규약상 스킬로만 고치므로 구현 뒤 `/llm-wiki:audit` 실행으로 처리 — 토스 절은 다른 레포도 겪는 외부 제약이라 도메인 루트 `toss-openapi-constraints.md`로 이동 후보

## 검증

- **단위 확인**: 스크래치에 type 정상·누락·오타·adr 불일치 문서 4종을 만들어 아래 명령의 에러 문구 확인

```
python3 llm-wiki/scripts/catalog.py --check --root {스크래치}/knowledge
python3 llm-wiki/scripts/catalog.py --root {스크래치}/knowledge/{domain} --shallow
```

- **실위키 확인**: `catalog.py --check --root /Users/rok/.ai-docs/wiki/knowledge`가 8장 모두 `type 없음`을 내고 목록 모드가 `[?]`로 8행 모두 출력하는지 확인
- **흐름 확인**: `/llm-wiki:update --dry-run`이 1장 선행 검사에서 audit 안내로 멈추는지, audit 후 `--dry-run` 배정표에 type이 실리는지 확인
- **의미 검토**: 편집 뒤 서브에이전트 1개로 doc-contract·update·add·audit 사이 type 용어·enum 표기 일치 검토
