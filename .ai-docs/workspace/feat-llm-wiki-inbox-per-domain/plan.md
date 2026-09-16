# llm-wiki 레포 그래프 데이터화와 파생 주입 v3.0.0

## 의도

- **왜**: 레포 간 계약과 소관이 `index.md` 본문(사람이 쓰는 표)과 `deps.json`(간선)에 나뉘어 책임이 겹치고, `update`의 추출 프롬프트가 호출 관계를 사실이 아니라고 배제해 간선의 무인 생성 경로가 끊겨 있으며, 훅은 현재 도메인 `index.md` 본문 전체를 매 세션·compact마다 주입해 팀 규모(레포 30개 이상)에서 세션당 약 9,000토큰을 쓰면서도 간선 상대 레포를 열 좌표(로컬 경로·remote)는 주지 않음 — 그래서 Front 작업 전 Backend 선대응 확인, 리뷰 시 타 도메인 파급 판단, 요구사항의 수정 대상 도메인·프로젝트 파악이 성립하지 않음
- **누가**: 여러 도메인(개발자센터·상품전시)의 프로젝트(Front·Backend·Batch)에서 개발·코드 리뷰·질의를 하는 에이전트 세션마다, 그리고 레포를 등록하는 register와 머지를 반영하는 update가 노드·간선을 어디에 어떻게 적을지 정하는 시점
- **완료**: ① 레포 노드 지식(스택·소관·업무 영역별 역할·호스트·상태)이 `registry.json`에, 간선이 `deps.json`에만 있고 `index.md`는 없음 ② 훅이 그 데이터에서 도메인 목록(영역 이름 포함)·접근 좌표·역인덱스·현재 레포 기준 두 묶음 간선·인접 레포 좌표를 마크다운으로 파생 주입하며 `python3 graph.py map --domain {d}`로 타 도메인 지도를 한 번에 얻음 ③ register가 서브에이전트 1회 조사 → 확인 1라운드로 노드와 나가는 간선을 채우고, update가 기존 영역·호스트·간선을 `관찰`로 보강함 ④ `catalog.py --check`가 노드·간선·영역 키를 검사함 ⑤ 픽스처 위키에서 훅 출력이 형식대로 나오고 검사가 통과함. 기존 위키 이관과 하위 호환은 범위 밖

## 배경

- **플러그인 파일**: `llm-wiki/hooks/session_start.sh`(bash + 인라인 python, `scripts/catalog.py`를 import), `scripts/catalog.py`(문서 목록·`--check`·`deps.json` 검사·`resolve_repo`), `scripts/update.py`(`domains`·`pending`·`advance`), `rules/agent-guide.md`(10불릿, 훅이 `{WIKI_ROOT}`·`{CATALOG_PY}` 치환), `references/doc-contract.md`(1~10장, 9장 index.md·10장 deps.json), `skills/{init,register,update,add,audit}/SKILL.md`, `README.md`, `.claude-plugin/plugin.json`과 루트 `.claude-plugin/marketplace.json`의 `version`이 함께 2.10.0
- **현 훅 조립 순서**: 규약 → 헤더(동기화·도메인·형제 건수·inbox 건수·커서) → 도메인 목록(`index.md` 첫 단락) → 현재 도메인에 닿는 간선 평면 나열 → 도메인 `index.md` 본문 전체 → 도메인 루트 목록(shallow) → 현재 레포 목록, 소프트 8,000토큰 초과 시 권고 한 줄. `.local/paths.json`에 `{slug: toplevel}`을 기록하는 부수 효과가 있음
- **catalog.py 안 index·deps 결합 지점**: `INDEX_NAME` 상수, `docs(shallow)`의 index 제외, `lead_line`, `load_edges`·`EDGE_RE`·`EDGE_KEYS`·`check_deps`, `check_index_refs`·`REF_RE`·`REVERSE_INDEX_HEADING`, `missing_indexes`, `check()`의 `index_errors`·`deps_errors`, `selected_names`의 `deps.json` 특례, `normalize_remote`·`resolve_repo`
- **update 단절 지점**: `skills/update/SKILL.md` 2장 추출 프롬프트 출력 스키마가 `fact·topic·code·quote·shas`뿐이고 "호출 관계는 사실이 아님"을 명시하는데, 3장 `deps.json 배정`은 "diff에서 레포 간 의존이 확정되면"을 전제함 — 메인은 diff를 읽지 않으므로 무인 간선은 생기지 않음
- **레거시 참조**: 사내 `system-repository-map.md`(약 9,200토큰 단일 문서)는 접근 좌표(Bitbucket 프로젝트 키·MCP 호출 템플릿·clone URL 패턴), 업무 영역 → 레포(역할) 역인덱스, 레포 표(스택·접점·소관), 의존 방향 블록, 반영 순서 계약 사실을 한 파일에 담았음. 이번 설계는 그 내용을 노드·간선·도메인 데이터로 옮기고 반영 순서 계약은 도메인 루트 일반 문서로 둠(규격 변경 없음)
- **실제 위키**: `~/.ai-docs/wiki`에 도메인 1개(`argon1025-side`)·레포 2개·`index.md` 1장·레포 문서 3장·`deps.json` 없음

## 확정 결정 (사용자 확인 2026-09-16)

- **주입 축소**: "주입 축소 : 동의" — `index.md` 본문 전체 주입을 없애고 데이터에서 파생한 역인덱스·간선·좌표만 주입
- **접점 제거**: "노드 방식으로 의존성을 관리 함으로 접점은없어도 되지 않을지" — 셀러·운영자·파트너 접점 열을 두지 않음
- **SSOT**: "각 레포별 노드는 register 에서 관리하던지 SSOT 준수" — 노드는 `registry.json`의 `repos.{slug}`에 통합하고 register가 생명주기를 소유, `deps.json`은 간선 전용
- **index.md 폐지, 접근 좌표는 도메인 데이터**: `registry.json`의 `domains.{d}.access` 문자열 배열로 두고 훅이 현재 도메인 것을 주입
- **영역 어휘는 도메인 접두**: "앞에 도메인을 붙여야함 (예: 상품전시 PID / 개발자센터 PID) 처럼 같은 어휘라도 도메인별로 처리가 달라질 수 있음" — 영역 키는 항상 `{domain}/{영역}` 꼴이며 노드가 다른 도메인의 영역에 참여할 때는 그 도메인 접두 키를 씀
- **register 조사**: "서브에이전트 1회, 입력 5종 고정" — 먼저 조사하고 확인차 묻는 순서, 이후 변경은 update가 보강
- **도메인 용어 독립**: "도메인 별로 의존관계는 있을 수 있으나 해당 도메인간에는 용어등 다 다를 수 있고 각자 유지되어야함" — 영역 키·`description`·`access`는 도메인마다 따로 두고 도메인 사이는 간선으로만 잇음, 도메인 공통 어휘 층은 두지 않음
- **간선 종류 구분**: "의존성 deps 도 코드상 의존 (예: external 라이브러리는 외부연동만 정의 해당 서비스를 백엔드 프론트든 다 import 하여 사용) 이 있고 도메인간에 의존이 있음 (예: 개발자센터에서 MQ로 상품이 배포 이것은 전시에서 받음) 이런 부분도 표현되어야" — `deps.json` 간선에 `kind`(`library`·`http`·`message`·`data`) 필수 키를 두고 방향 의미는 종류와 무관하게 "`from`이 `to`의 계약에 의존"으로 통일, 도메인 간 관계는 간선 집계로 도메인 목록에 표시
- **이관 불필요**: "기존 wiki 마이그레이션은 불필요 (하위호완 고려 불필요)" — 이관 스크립트·구버전 필드 호환 없음, 기존 위키는 레포별 register 재실행으로 채움
- **좋은 구조 우선**: 파일 수 최소화보다 책임 분리를 우선해 그래프 파생·검사를 `graph.py`로 분리함

## 외부 계약

### registry.json (규약 9장이 정본이 됨)

```json
{
  "domains": {
    "onestore-devcenter": {
      "description": "개발자센터 셀러 콘솔·앱 등록 레포 모음",
      "access": [
        "Bitbucket 프로젝트 DEVCENTER — https://bitbucket.example.com/projects/DEVCENTER",
        "clone https://bitbucket.example.com/scm/devcenter/{slug}.git",
        "MCP bitbucket_get_file_content(project_key=\"DEVCENTER\", repo_slug=\"{slug}\", path=\"…\")"
      ]
    }
  },
  "repos": {
    "devcenter-api": {
      "domain": "onestore-devcenter",
      "remotes": ["bitbucket.example.com/scm/devcenter/onestore-devcenter-api"],
      "branch": "develop",
      "status": "active",
      "stack": "Java 21 · Boot 3.5",
      "summary": "백엔드 API. 로그인 룰 체인·2FA·세션·핸드오프와 공지·메뉴·QnA·파일·공통코드",
      "areas": {
        "onestore-devcenter/로그인·세션": "룰 체인·세션·핸드오프",
        "onestore-devcenter/약관": "재동의 룰",
        "onestore-display/상품 정보": "상품 조회 API 제공"
      },
      "hosts": ["api.devcenter.example.com", "com.onestorecorp.devcenter:devcenter-client", "devcenter.notify"],
      "source": "확인 — register 조사, 2026-09-16"
    },
    "storeplatform-devcenter-batch": {
      "domain": "onestore-devcenter",
      "remotes": ["bitbucket.example.com/scm/devcenter/storeplatform-devcenter-batch"],
      "branch": "master",
      "status": "excluded",
      "reason": "레거시 VOC 메일 배치, 휴면",
      "stack": "", "summary": "", "areas": {}, "hosts": [],
      "source": "확인 — register 조사, 2026-09-16"
    }
  }
}
```

- **domains.{d}**: `description`(필수, 한 줄)·`access`(선택, 문자열 배열, 비밀값 금지) — 그 밖의 키 금지
- **repos.{slug} 키**: `domain`·`remotes`·`branch`·`status`·`stack`·`summary`·`areas`·`hosts`·`source` 9키 필수, `reason`은 `status`가 `excluded`일 때만 필수·그 밖에는 금지, 그 밖의 키 금지
- **status**: `active`·`excluded` 2값 — `excluded`는 훅 주입·update 대상에서 빠지고 `map` 출력의 제외 표에만 나옴
- **summary**: 80자 이내 소관 한 줄, 업무 낱말 우선, 접점(셀러·운영자 등)은 필요할 때 문장 안 낱말로만
- **areas**: `{영역 키: 역할}` — 키는 `^{domain}/[^/]+$`(domain은 `domains`에 등록된 이름), 역할은 40자 이내. 노드 자신의 도메인 접두가 기본이고 타 도메인 접두는 그 도메인 업무에 참여할 때만
- **hosts**: 이 레포가 서빙·발행하는 식별자 — 호스트명, Maven·npm artifact(`group:artifact`), 큐·토픽 이름. 무인 간선 매핑의 유일한 표이며 중복은 레포 사이에서 금지
- **excluded 대칭**: `status`가 `excluded`면 `stack`·`summary`는 빈 문자열, `areas`는 빈 객체, `hosts`는 빈 배열이어야 하고 `active`면 `stack`·`summary`가 비면 안 됨 — `check`가 양쪽을 검사
- **source**: 4장 출처 줄과 같은 꼴 `확인 — register 조사, {날짜}` 또는 `확인 — {자료·결정}, {날짜}`. update가 `areas`·`hosts`를 보강해도 갱신하지 않음(커밋 메시지가 근거)
- **편집 주체**: register가 노드 전체(생성·재조사·도메인 이동·status), add가 `확인` 출처로 `summary` 교체·`areas`·`hosts`·`access` 보강, update가 `관찰`로 `areas`(기존 키에 레포를 붙이는 것만)·`hosts` 추가 — 새 영역 키 생성은 register·add만

### deps.json (규약 10장, 기존 규격 + kind 추가)

```json
{
  "edges": [
    {
      "from": "onestore-display/display-front",
      "to": "onestore-devcenter/devcenter-agent",
      "kind": "message",
      "note": "product.deployed",
      "source": "관찰 — register 조사, 2026-09-16"
    },
    {
      "from": "onestore-devcenter/devcenter-api",
      "to": "onestore-devcenter/cmsapp-external",
      "kind": "library",
      "note": "com.onestorecorp.cmsapp:cmsapp-external",
      "source": "관찰 — devcenter-api @a1b2c3d 머지, 2026-09-16"
    }
  ]
}
```

- **kind**: 필수, 4값 — `library`(from이 to를 빌드 의존으로 import: 코드값·외부연동 라이브러리), `http`(from이 to의 API를 동기 호출), `message`(from이 to가 발행한 큐·토픽 메시지를 소비), `data`(from이 to 소유 DB·스토리지를 직접 읽음). 방향 의미는 종류와 무관하게 "`from`이 `to`의 계약에 의존, `to` 변경 시 `from`이 파급 대상"으로 하나 — 메시지는 발행자가 `to`
- **유일성 조정**: `(from, to, kind)` 셋이 하나 — 같은 두 레포가 http와 message로 함께 이어질 수 있음
- **정렬**: `from`·`to`·`kind` 사전순
- **note 규약**: 계약 식별자를 ` · `로 나열 — HTTP는 메서드+경로 접두(`GET /v1/notices*`), 라이브러리는 `group:artifact`, 메시지는 큐·토픽 이름. 식별자 추가(append)는 출처 등급과 무관하게 `관찰`도 할 수 있고, 식별자 삭제·교체와 자유 텍스트 변경은 `확인`만 — 기존 "`확인` 간선의 `note`는 `관찰`이 바꾸지 못함" 문장을 이 규칙으로 대체
- **register 간선 출처**: register 조사에서 나온 간선은 코드 관찰이므로 `관찰 — register 조사, {날짜}` — 노드 `source`(사용자가 확인한 소관·영역)와 등급이 다름
- **낡음**: `source` 끝 날짜가 180일을 넘으면 주입·`map` 출력에 `!`를 붙임(문서와 같은 `STALE_DAYS`)

### 훅 주입 형식 (규약 다음, 문서 목록 앞)

```
# 위키 — 도메인 onestore-devcenter · 레포 devcenter-front
# 커서 a1b2c3d · HEAD와 같음

# 도메인 2개 · 현재 onestore-devcenter
- onestore-devcenter — 개발자센터 셀러 콘솔·앱 등록 레포 모음 · 영역: 로그인·세션, 약관, 공지 외 9
- onestore-display — 상품 전시·매대 레포 모음 · 영역: 상품 전시, 프로모션 외 7 · onestore-devcenter에 의존 http 2 · message 1

# 접근 좌표 · onestore-devcenter
- Bitbucket 프로젝트 DEVCENTER — https://…

# 역인덱스 · onestore-devcenter 12영역 (영역 — 레포(역할), 타 도메인 레포는 {domain}/{slug})
- 로그인·세션 — devcenter-api(룰 체인·세션·핸드오프) · devcenter-front(화면) · onestore-display/display-front(SSO 진입)
- 약관 — devcenter-api(재동의 룰) · devcenter-front(열람 화면)

# 이 레포가 의존 — 선행 조건 2건 (to 레포 계약이 새로 필요하면 선대응 확인)
- http → onestore-devcenter/devcenter-api — GET /v1/notices* · POST /v1/files
- library → onestore-devcenter/devcenter-client — com.onestorecorp.devcenter:devcenter-client
# 이 레포에 의존 — 파급 대상 2건 (변경 시 from 레포 소비 여부 확인)
- http onestore-display/display-front → — /embed/*
- message onestore-display/display-batch → — product.deployed
# 도메인의 다른 간선 3건
- library onestore-devcenter/devcenter-batch → onestore-devcenter/devcenter-client — com.onestorecorp.devcenter:devcenter-client !

# 인접 레포 좌표 2건 (slug — 스택 · 소관 · 로컬 경로 · remote · 문서 건수)
- devcenter-api — Java 21 · Boot 3.5 · 백엔드 API. … · 로컬 /Users/me/src/devcenter-api · bitbucket.example.com/scm/devcenter/onestore-devcenter-api · 문서 4건
- onestore-display/display-front — Next.js 15 · 상품 전시 프론트 · 로컬 없음 · bitbucket.example.com/scm/display/display-front · 문서 0건
```

- 도메인 목록 영역 이름은 그 도메인 접두 영역 키를 사전순 5개까지, 나머지는 `외 N`; 뒤에 현재 도메인과 잇는 간선을 방향·종류별로 집계(`{d}에 의존 http 2 · message 1`, `{d}가 의존 …`), 없으면 생략
- 간선 행은 `{kind} {from} → {to} — {note}` 꼴이고 두 묶음에서는 현재 레포 쪽 끝점을 비움
- 역인덱스 행은 `{현재 도메인}/` 접두 영역 키 전부, 각 행의 레포는 노드 사전순, `status: excluded` 노드 제외
- 인접 레포는 두 묶음 간선의 상대편 레포 합집합, 로컬 경로는 `.local/paths.json`, 문서 건수는 `knowledge/{domain}/{slug}` 파일 수
- 미등록 레포 세션(도메인 없음)은 규약·헤더·도메인 목록만, 레포 밖 세션도 같음

### graph.py CLI

```
python3 graph.py map --domain {d} [--wiki PATH]   # 그 도메인의 접근 좌표·역인덱스·도메인에 닿는 간선 전부·레포 표(slug·스택·소관)·제외 표를 마크다운으로
python3 graph.py check [--wiki PATH]              # registry.json·deps.json 검사, 에러 있으면 종료 코드 1
```

## 선행 읽기

- `llm-wiki/references/doc-contract.md` — 9·10장을 통째로 바꾸고 1·6·8장을 손대므로 현재 장 구조를 먼저 봄
- `llm-wiki/skills/update/SKILL.md` 2~5장 — 추출·배정·반영·커밋의 fan-out 구조 위에 `deps`·`node_hints`를 얹으므로 프롬프트 원문을 먼저 봄
- `.ai-docs/workspace/feat-wiki-deps-graph/plan.md` — 직전 판(v2.9.0)이 `deps.json`을 분리한 근거와 형식이 이번 계약의 출발점

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/scripts/graph.py` | 신설: registry·deps 로드, 영역 파생, 간선 묶음, 인접 좌표, 렌더러, `check`, `map`·`check` CLI, `normalize_remote`·`resolve_repo` 이전 | ⑦ — 파생·검사가 약 250줄이고 `catalog.py`는 문서 목록 책임이라 한 파일에 두면 docstring이 선언한 계약("문서의 frontmatter를 읽어 목록을 만든다")이 깨짐 |
| `llm-wiki/scripts/catalog.py` | index·deps·registry 관련 상수·함수 삭제, `check()`가 `graph.check_errors()` 결과를 `registry.json:`·`deps.json:` 이름으로 합침, `selected_names`가 두 파일 이름을 받음 | ② 기존 코드 축소 |
| `llm-wiki/scripts/update.py` | `status: excluded` 레포를 `pending`·`domains`에서 건너뜀(`skipped` 사유 "제외 레포") | ⑥ 한 줄 분기 |
| `llm-wiki/hooks/session_start.sh` | 인라인 python을 `graph.py` 파생 호출로 재작성: index 본문·형제 건수·평면 간선 삭제, 도메인 목록(영역 포함)·접근 좌표·역인덱스·두 묶음 간선·인접 좌표 추가, 소프트 예산 유지 | ② 기존 훅 재작성 |
| `llm-wiki/rules/agent-guide.md` | 10불릿 재구성: 역인덱스·선행 조건·파급 대상 3불릿 신설, 도메인 지도·의존 간선 불릿 삭제, 커서 불변을 직접 수정 금지에 병합, `{GRAPH_PY}` 치환자 | ② |
| `llm-wiki/references/doc-contract.md` | 9장 index.md 삭제 → 9장 registry.json 노드, 10장 deps.json에 note 규약·낡음 추가, 1장에 "레포 간 호출 관계는 문서가 아니라 간선" 문장, 6장 면제 문구를 그래프로, 8장 커밋 접두 `docs(graph)` | ② |
| `llm-wiki/skills/register/SKILL.md` | 2장 조사(서브에이전트 1회·입력 5종·JSON 초안), 3장 질문에 status·description·access·확인 표 추가, 4장 index.md 골격 삭제 → 노드 기록·확인 간선, `--resurvey` 인자, 상태 표에 영역·간선 수 | ② |
| `llm-wiki/skills/update/SKILL.md` | 2장 추출 출력에 `deps`·`areas`·`hosts` 추가(도메인 기존 영역 키를 프롬프트에 전달), 3장 index.md 배정 삭제 → 그래프 배정(호스트 매핑·기존 영역 보강·새 영역은 inbox), 4장 index.md 에이전트 삭제, 5장 `docs(graph)` 커밋 | ② |
| `llm-wiki/skills/add/SKILL.md` | 5장 index.md 보강 → 노드·access 보강(`확인`), 간선 규칙 유지, 커밋 접두 | ② |
| `llm-wiki/skills/audit/SKILL.md` | 1장 측정에 `graph.py check`·낡은 간선·빈 영역 노드, 2장 index.md 행 2종 삭제 → 영역 유사 키 `통합` 행, 4장 index.md 절 이동 문구 삭제 | ② |
| `llm-wiki/skills/init/SKILL.md` | 4장 다음 안내 문구에서 index.md 제거 | ⑥ |
| `llm-wiki/README.md` | 동작 방식·위키 구조·registry 예시·무인 갱신 범위 재작성, 보류 목록에서 "성격별 폴더 분류" 유지 | ② |
| `llm-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `version` 3.0.0, description의 "3층" 문구를 "그래프 파생 주입"으로 | ⑥ |

### graph.py

- **로드**: `load_registry(wiki_root)`·`load_edges(wiki_root)`는 깨진 파일을 빈 값으로 돌려주고(훅 경로) 모양 검사는 `check_errors`가 함 — `catalog.load_json` 재사용
- **파생 함수**: `domain_areas(registry, d)` → 접두 `d/` 영역 키의 정렬 목록, `reverse_index(registry, d)` → `[(영역, [(slug 표시, 역할)])]`(타 도메인 노드는 `{domain}/{slug}` 표시), `edge_groups(edges, domain, slug)` → `(outgoing, incoming, others)`, `domain_links(edges, d)` → 다른 도메인마다 방향·`kind`별 건수(도메인 목록 집계용), `adjacent(registry, edges, slug, paths, knowledge)` → 좌표 행, `edge_stale(edge, today)` → `source` 끝 `YYYY-MM-DD` 파싱해 180일 초과 여부
- **렌더**: `render_session(...)`이 훅 주입 블록(외부 계약의 형식)을, `render_map(d)`가 `map` 출력을 만듦 — 둘이 같은 파생 함수를 쓰므로 세션과 명령 출력이 어긋나지 않음
- **check_errors(wiki_root)**: `(파일, 메시지)` 목록 — domains 키 검사·description 필수·access 배열, repos 9키·`reason` 조건·status 2값·summary 80자·areas 키 형식과 도메인 등록·역할 40자·hosts 레포 간 중복·source 형식, 간선 기존 검사(키·형식·자기 간선·끝점 등록)에 `kind` 필수·4값 검사와 `(from, to, kind)` 중복 검사, `excluded` 끝점 경고 없음(간선은 유지), 영역 키 유사 중복(같은 도메인에서 공백·`·`·`/` 뒤 구두점을 지운 소문자가 같으면 에러)
- **CLI 종료 코드**: `map`은 항상 0(도메인 미등록이면 한 줄 안내), `check`는 에러 있으면 1
- **resolve_repo·normalize_remote**: `catalog.py`에서 그대로 옮기고 시그니처 유지 — 훅·`update.py`가 import 경로만 바꿈

### catalog.py

- **삭제**: `INDEX_NAME`·`DEPS_NAME`·`EDGE_*`·`REF_RE`·`REVERSE_INDEX_HEADING`·`lead_line`·`load_edges`·`check_deps`·`check_index_refs`·`missing_indexes`·`normalize_remote`·`resolve_repo`, `docs(shallow)`의 index 제외 조건, `check_location`의 "index.md는 도메인 루트에만" 분기
- **유지**: `parse_frontmatter`·`body_lines`·`estimate_tokens`·`docs`·`build`·`load_json` — 훅과 `graph.py`가 import해 씀
- **check()**: `graph.check_errors(root.parent)`를 `only`가 None이거나 `only`에 `registry.json`·`deps.json`이 있을 때 합침, 나머지 문서 검사 그대로
- **selected_names**: `root.parent/registry.json`·`deps.json`을 이름으로 받는 특례 2건
- **docstring**: 문서 목록과 문서 검사만 책임진다고 갱신

### session_start.sh

- **유지**: python3 확인, source 판정, pull 동기화, `.local/paths.json` 기록, 헤더(동기화·inbox·커서), 도메인 루트 shallow 목록·현재 레포 목록, 소프트 예산 권고, 어떤 실패에도 종료 코드 0
- **교체**: `import catalog, graph` 후 `graph.render_session(registry, edges, domain, slug, paths, knowledge, today)`가 도메인 목록·접근 좌표·역인덱스·간선 두 묶음·인접 좌표 블록을 돌려주고 훅은 헤더와 목록 사이에 끼움
- **헤더 첫 줄**: `# 위키 — 도메인 {d} · 레포 {slug}`만(형제 건수 삭제, 인접 좌표의 문서 건수가 대체)
- **치환자**: 규약의 `{WIKI_ROOT}`·`{CATALOG_PY}`·`{GRAPH_PY}`

### rules/agent-guide.md (10불릿)

1. **문서 우선** 유지 2. **여는 기준** 유지 3. **역인덱스**: 요청의 업무 낱말이 주입된 역인덱스 행에 있으면 그 레포 집합이 수정·검토 대상이고, 없으면 도메인 목록의 영역 이름이 걸리는 도메인을 `python3 {GRAPH_PY} map --domain {d} --wiki {WIKI_ROOT}`로 봄 — 레포 밖 세션도 같음 4. **선행 조건**: 현재 레포에서 HTTP 호출·라이브러리 import·메시지 소비·타 레포 데이터 조회 코드를 추가·변경하면 "이 레포가 의존" 간선의 `to` 레포 코드를 인접 좌표(로컬 경로, 없으면 `git clone --depth 1 https://{remote}.git`을 스크래치에)로 열어 계약 대응 여부를 대조하고 없으면 선대응 필요로 보고 5. **파급 대상**: 현재 레포의 공개 계약(컨트롤러·공용 라이브러리 심볼·발행 메시지·공유 스키마)이 바뀌면 "이 레포에 의존" 간선마다 `kind`·`note` 식별자와 대조하고 걸리면 `from` 레포 코드로 소비 여부를 확인해 리뷰·보고에 파급을 명시, 타 도메인 `from`은 도메인 이름을 함께 적음, `!` 간선은 대조 전 최신 여부 재확인 6. **범위 순서** 유지 7. **낡음 표시** 유지 8. **모순 보고** 유지 9. **직접 수정 금지**: 스킬 5종 안내에 "노드·간선은 register·add·update만, 커서는 update만" 병합 10. **기록 제안** 유지

### doc-contract.md

- **1장**: 제외 판정선의 `호출 관계`를 `한 레포 안 호출 관계`로 좁히고, 담지 않는 것에 "레포 간 호출·소비 관계 — 문서가 아니라 10장 간선으로" 추가(추출 프롬프트가 인용하는 절이므로 여기 두어야 서브에이전트가 `deps`로 분류하며, 두 문장이 한 절에서 충돌하지 않음)
- **6장**: 면제 문구 "`index.md`의 역인덱스와 `deps.json`의 간선" → "9·10장 그래프"
- **8장**: 커밋 접두 표 — 문서 `docs({domain})`, 그래프(노드 보강·간선) `docs(graph)`, 등록 `chore(register)`
- **9장 registry.json**: 외부 계약의 스키마·키 규칙·편집 주체를 그대로 옮기고, 영역 키 작성 기준(업무 낱말 명사구, 도메인 접두 필수, 같은 도메인에서 구두점만 다른 키 금지, 타 도메인 접두는 참여할 때만) 추가
- **10장 deps.json**: 기존 항목 유지 + `kind` 4값과 방향 의미(메시지는 발행자가 `to`)·`(from, to, kind)` 유일성·note 규약·낡음·"작성 주체"에 register(조사 관찰 간선) 추가, "audit이 index.md 의존 절 이동" 문구 삭제

### skills/register/SKILL.md

- **frontmatter**: `description`에서 "scaffolds or updates knowledge/{domain}/index.md"를 "surveys the repo once and records the node (stack·summary·areas·hosts·status) in registry.json with its outgoing edges in deps.json"으로 재작성
- **1장 전제**: 기존 등록이면 `--resurvey`가 없을 때 도메인 이동·remote 추가만 묻고 조사 생략. 체크아웃 밖 휴면 레포는 `--excluded {slug} --remote {URL} --reason {사유} [--branch {b}]`로 등록 — 조사·질문 없이 `status: excluded` 노드를 기록하고 `branch` 기본값은 `main`
- **2장 조사 — 서브에이전트 1회(`model: sonnet`)**: 입력 5종 고정 — ① `README*` ② 빌드 파일(`package.json`·`pom.xml`·`build.gradle*`·`pyproject.toml`·`go.mod`)의 이름·의존 목록 ③ 최상위 디렉터리와 소스 패키지 3단계 목록 ④ 컨트롤러·라우터·핸들러 파일명과 라우트 선언 grep(`@RequestMapping|@GetMapping|@PostMapping|router\.|app\.(get|post|put|delete)|@Controller`) ⑤ 설정 파일(`application*.yml|properties`, `.env.example`)의 URL·호스트·큐 이름과 HTTP 클라이언트 base URL·Feign name. 출력 `{스크래치}/survey.json` = `{stack, summary, areas: [{area, role, evidence}], hosts: [], outgoing: [{target, kind: library|http|message|data, identifiers: [], evidence}]}` — 빌드 의존은 `library`, HTTP 클라이언트·Feign은 `http`, 큐·토픽 리스너는 `message`(target은 발행 측 식별자), 타 레포 스키마 직접 조회는 `data`, 응답은 건수만. 프롬프트에 대상 도메인의 기존 영역 키 목록을 넣어 같은 이름을 우선 쓰게 함
- **3장 질문 — 정지점 하나**: 기존(도메인·기본 브랜치·기존 등록 처리)에 신규 도메인 `description`·`access`(빈 값 허용), `status`(기본 active, excluded면 사유), 조사 초안 표(스택·소관·영역별 역할·호스트·나가는 간선 대상)를 AskUserQuestion 한 라운드로 확인 — 초안 수정은 자유 입력, `알아서`는 초안 채택
- **4장 registry.json·deps.json**: `repos.{slug}` 9키(+`reason`) 기록, `domains.{d}` 신설 시 `description`·`access`; `outgoing`의 `target`을 다른 노드의 `hosts`·slug·remotes와 대조해 걸린 것만 `deps.json`에 `관찰 — register 조사, {날짜}` 간선(`kind` = outgoing.kind, note = identifiers)으로 추가, 걸리지 않은 대상은 보고의 "미등록 상대"로만 남김; 도메인 이동은 `deps.json` 끝점 치환 + `knowledge/{old}/{slug}` `git mv`(승인 하나) — 영역 키는 도메인 접두가 참여 도메인을 뜻하므로 바꾸지 않으며, 새 도메인 영역 참여는 이동 직후 `--resurvey`로 재조사하라고 보고에 안내
- **5장 검사·커밋**: `python3 …/catalog.py --check --root {WIKI_ROOT}/knowledge {WIKI_ROOT}/registry.json {WIKI_ROOT}/deps.json` 에러 0, 커밋 `chore(register): {slug} → {domain}` 하나에 registry·deps 모두 담음
- **6장 상태 표**: `| 레포 | 도메인 | 상태 | 영역 | 간선(out/in) | 브랜치 | 커서 | 로컬 경로 |`

### skills/update/SKILL.md

- **frontmatter**: `description`의 "assigns facts to the domain root, the repo folder and index.md"를 "assigns facts to the domain root and the repo folder and observed dependencies·areas·hosts to registry.json/deps.json"으로 재작성
- **1장**: `work.json`의 `skipped` 사유에 "제외 레포" 추가 설명
- **2장 추출 프롬프트**: 규약 인용을 `sed -n '/^## 1\./,/^## 2\./p'` 유지, 출력 파일에 `facts`(기존 배열)·`deps: [{target, kind: library|http|message|data, identifiers, shas}]`·`areas: [{area(전달된 기존 키 중 하나), role, shas}]`·`hosts: [{host, shas}]` 4키 객체로 변경, 프롬프트에 그 레포 도메인의 기존 영역 키 목록 전달, "호출 관계는 사실이 아니라 deps입니다" 문장
- **3장 배정**: `deps.target`을 `registry.repos[*].hosts`·slug·remotes에 대조 → 걸리면 `(from=현재 레포, to=대상, kind)` `관찰` 간선 추가 또는 같은 셋의 기존 간선 `note`에 identifiers 추가·`source` 갱신(`관찰` 간선만 `source` 갱신), 걸리지 않으면 `기각 — 미등록 상대`(보고에 대상 원문); `areas`는 노드 `areas`에 없는 키면 보강, 전달 키 밖 이름은 `inbox/{domain}.md`에 `- [{날짜}] [{domain}] 새 영역 후보 — 기존 없음 / 새 {제안 키}: {역할} ({slug} @{sha7} {code})` 행(7장 형식의 `기존 없음` 변형, `- [`로 시작해 훅 건수에 잡힘); `hosts`는 다른 노드와 겹치지 않을 때만 추가. index.md 배정 삭제
- **4장 반영**: index.md 에이전트 삭제, registry·deps는 메인이 직접 편집(문서 에이전트에 보내지 않음)
- **5장 커밋**: 문서 커밋 뒤 그래프가 바뀌면 `docs(graph): {slug} @{sha7} 간선 N건 · 영역 M건 · 호스트 K건` 한 커밋(registry·deps 함께)
- **6장 보고**: "그래프" 항목(간선·영역·호스트 추가 건수, 미등록 상대 목록)

### skills/add/SKILL.md

- **5장**: "index.md 보강" 불릿 → "노드·좌표 보강: 자료·대화에서 소관·영역·호스트·접근 좌표가 확정되면 `확인` 출처로 `registry.json`을 편집(summary 교체는 3장 교체 판정), 새 영역 키 생성 가능, `inbox`의 `새 영역 후보` 행은 여기서 소비"; 간선 불릿의 커밋을 `docs(graph): {요약}`으로, 승인 표에 노드 변경 행 포함

### skills/audit/SKILL.md

- **1장 측정**: `- **index.md**: …` 불릿 삭제, `python3 …/graph.py check --wiki {WIKI_ROOT}` 에러, `!` 간선 목록, `areas`가 빈 active 노드 목록을 `catalog.md`에 함께 저장
- **2장 진단 표**: index.md 행 2종 삭제, "같은 도메인에서 구두점·공백만 다른 영역 키 쌍" → `통합`(후: 남길 키, 비고: 옮길 노드) 행 추가 — 메인이 `check` 출력에서 직접 만들고 서브에이전트에는 보내지 않음
- **3장**: `!` 간선·빈 영역 노드는 `inbox/{domain}.md`에 `확인 필요` 행으로
- **4장**: 영역 키 통합은 메인이 `registry.json`을 직접 편집, 커밋 `docs(graph): audit 영역 통합 N건`

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `scripts/graph.py` 신설, `catalog.py` 정리·위임, `update.py` 제외 레포 건너뜀 | 스크래치에 픽스처 위키(`registry.json` 도메인 2·노드 4(제외 1)·`deps.json` 간선 4(kind 4종 각 1, 그중 도메인 간 message 1·낡음 1)·`knowledge/{d}/{slug}/a.md` 1장) 생성 후 `python3 graph.py check --wiki FIX` 종료 코드 0, `check`에 areas 키 접두 오류·hosts 중복·reason 누락·kind 미허용 값을 넣은 사본에서 에러 4건·종료 코드 1, `map --domain d2` 출력의 도메인 목록 행에 `d1에 의존 message 1` 집계 존재, `python3 graph.py map --domain d1 --wiki FIX` 출력에 역인덱스·간선·제외 표 절이 있음, `python3 catalog.py --check --root FIX/knowledge` 가 `registry.json:` 접두 에러를 함께 냄, `! grep -q 'INDEX_NAME\|check_deps\|resolve_repo' scripts/catalog.py` 통과 |
| 2 | `hooks/session_start.sh` 재작성 | 픽스처 레포(`git init` + `remote add origin` 픽스처 remote)에서 `CLAUDE_PROJECT_DIR=… LLM_WIKI_ROOT=FIX CLAUDE_PLUGIN_ROOT=… echo '{"source":"clear"}' \| bash session_start.sh \| python3 -c 'import json,sys;print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'` 출력이 외부 계약 형식의 절(도메인 목록에 `영역:`과 `에 의존` 집계, 접근 좌표, 역인덱스, 이 레포가 의존, 이 레포에 의존, 인접 레포 좌표, 문서 목록)을 순서대로 담고 간선 행이 `{kind} ` 접두로 시작하며 `! grep -q 'index.md\|형제:'`로 두 문자열 부재 확인, 미등록 remote로 바꾸면 규약·헤더·도메인 목록만 나옴, 훅 종료 코드 0 |
| 3 | `rules/agent-guide.md`, `references/doc-contract.md` | `grep -c '^- \*\*' rules/agent-guide.md` 출력 `10`, `! grep -q 'index.md' rules/agent-guide.md references/doc-contract.md` 통과, `python3 -c "print(len(open('rules/agent-guide.md').read())/1.8)"` 출력 900 이하, `grep -q '^## 9\. registry.json' references/doc-contract.md && grep -q '^## 10\. deps.json' references/doc-contract.md && grep -q 'docs(graph)' references/doc-contract.md` 통과 |
| 4 | `skills/register/SKILL.md`, `skills/init/SKILL.md` | `! grep -q 'index.md' skills/register/SKILL.md skills/init/SKILL.md` 통과(frontmatter 포함), `grep -q 'survey.json' skills/register/SKILL.md && grep -q -- '--resurvey' skills/register/SKILL.md && grep -q -- '--excluded' skills/register/SKILL.md` 통과; 실행 검증은 `claude --plugin-dir {repo}/llm-wiki`로 연 새 세션의 `trendlog-backend` 체크아웃에서 `/llm-wiki:register --resurvey` 1회 실행 후 `python3 graph.py check` 종료 코드 0과 `registry.json` `repos.trendlog-backend`의 9키가 비지 않음 |
| 5 | `skills/update/SKILL.md`, `skills/add/SKILL.md`, `skills/audit/SKILL.md` | `! grep -q 'index.md' skills/update/SKILL.md skills/add/SKILL.md skills/audit/SKILL.md` 통과(frontmatter 포함), `grep -q '"deps"' skills/update/SKILL.md && grep -q '기존 영역 키' skills/update/SKILL.md && grep -q '미등록 상대' skills/update/SKILL.md && grep -q '새 영역 후보' skills/update/SKILL.md` 통과; 실행 검증은 `claude --plugin-dir {repo}/llm-wiki` 세션의 `my-claude-plugin-market`에서 `/llm-wiki:update --repo my-claude-plugin-market --dry-run`이 배정표(`assign.json`)에 `graph` 항목을 포함해 종료 |
| 6 | `README.md`, `plugin.json`, `marketplace.json` | `grep -h '"version"' llm-wiki/.claude-plugin/plugin.json .claude-plugin/marketplace.json \| sort -u \| wc -l` 출력 `1`이고 그 값이 `3.0.0`, `! grep -q 'index.md' llm-wiki/README.md && grep -q 'graph.py' llm-wiki/README.md` 통과 |

## 특이 사항

- **기존 위키 이관 없음**: `~/.ai-docs/wiki`의 `registry.json`은 새 필수 키가 없어 v3 `check`에서 에러가 나고 훅은 빈 값으로 관용 주입함(영역 0·간선 0). 채우는 절차는 각 레포 체크아웃에서 `/llm-wiki:register --resurvey` 실행, `knowledge/argon1025-side/index.md`는 일반 문서로 취급되므로 사용자가 `git rm`으로 지움 — 후속 작업
- **관용 vs 엄격**: 훅은 필드 누락을 빈 값으로 읽어 세션 시작을 막지 않고, `check`는 9키를 요구함 — 스킬은 `check` 에러 0에서만 커밋하므로 데이터 품질은 스킬 경로에서 보장됨
- **호스트 매핑 한계**: update의 무인 간선은 대상이 어느 노드의 `hosts`에 있을 때만 생김. register 조사가 `hosts`를 빠뜨리면 그 레포로 들어오는 간선은 `미등록 상대` 보고로만 남고, 사람이 `/llm-wiki:add`로 `hosts`를 보강하면 다음 update부터 연결됨 — 업그레이드 조건: 미등록 상대 보고가 반복되면 register 조사 입력에 OpenAPI 스펙 파일을 6번째 입력으로 추가
- **영역 어휘 증식 방지**: update는 기존 키에만 레포를 붙이고 새 이름은 inbox로 보냄 — 어휘 확장은 register·add(`확인`)에서만
- **타 도메인 영역 참여는 무인 보강 밖**: update 추출 프롬프트에는 그 레포 도메인의 영역 키만 전달하므로 `onestore-display/상품 정보` 같은 타 도메인 참여는 register 조사·확인이나 `/llm-wiki:add`로만 기록됨 — 의도적 단순화, 업그레이드 조건: inbox의 `새 영역 후보` 행에 타 도메인 이름이 반복해서 나오면 프롬프트에 간선 상대 도메인의 키도 전달
- **역인덱스 크기**: 원자 영역화로 레거시 복합 행(25행)이 35~40행으로 늘 수 있음. 도메인당 역인덱스가 3,000토큰을 넘으면 소프트 예산 권고가 나오며 그때 영역 병합은 audit `통합` 행으로 처리
- **실행 검증의 한계**: 커밋 1~3·6은 명령으로 검증하고 커밋 4·5의 스킬 문서는 grep 검증 뒤 실제 스킬 1회 실행으로 확인함. 세 use case의 최종 수용 검증(Front 세션이 Backend 코드를 여는가, 리뷰가 `from` 레포를 지목하는가, 타 도메인 `map`을 실행하는가)은 팀 규모 데이터가 있어야 하므로 이 계획 밖 후속 작업
- **범위 밖**: `init` 골격 변경 없음(`registry.json` `{"domains": {}, "repos": {}}` 유지), 문서 규격(1~8장) 변경 없음, 레거시 `system-repository-map.md` 이관 스크립트 없음
