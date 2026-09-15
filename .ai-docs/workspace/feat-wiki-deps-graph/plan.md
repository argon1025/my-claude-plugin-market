# llm-wiki 의존 간선 분리와 3층 세션 주입 v2.9.0

## 의도

- **왜**: 도메인이 `onestore-devcenter`·`onestore-display`처럼 여럿으로 늘고 도메인마다 레포가 10개 이상이 되면, 다른 도메인 레포가 현재 레포에 의존한다는 사실이 세션에 보이지 않아 개발자센터 작업 중 제품전시 파급을 놓침 — 현재 `index.md`의 `## 의존 방향`은 자유 서식이라 역방향 조회와 기계 검사가 불가하고 훅은 현재 도메인 index만 읽음
- **누가**: 등록 레포에서 세션을 여는 에이전트가 코드를 바꾸기 전 파급 레포를 찾는 시점, 그리고 `update`·`add`가 의존 사실을 어디에 적을지 정하는 시점
- **완료**: 세션 주입이 ① 도메인 목록·한 줄 설명·현재 도메인에 닿는 의존 간선(양방향) ② 도메인 `index.md` 본문·도메인 루트 목록 ③ 현재 레포 목록의 3층으로 나오고, 간선은 위키 루트 `deps.json` 한 곳에만 있으며 `catalog.py --check`가 끝점을 `registry.json`과 대조함

## 배경

- **현재 주입**: `llm-wiki/hooks/session_start.sh`가 규약(`rules/agent-guide.md`) → 헤더(도메인·레포·형제 건수·inbox·커서) → 도메인 `index.md` 본문 전체 → 도메인 루트 목록(shallow) → 현재 레포 목록 → `# 다른 도메인 N개: a · b — 목록은 주입하지 않음` 순으로 조립하며, HARD 12,000토큰 초과 시 목록부터 접고 마지막에 index 본문을 접음
- **도메인 간 관계의 현재 자리**: `references/doc-contract.md` 9장이 역인덱스·의존 방향에 `{domain}/{slug}` 꼴 타 도메인 참조를 허용하는 것이 전부이며, `registry.json`의 `domains.{d}`는 빈 객체
- **registry.json 편집 주체**: register만 편집(`skills/register/SKILL.md` 3장) — 의존 간선을 여기에 넣으면 무인 `update`가 등록 파일을 건드리게 되어 별도 파일로 분리
- **실제 위키 상태**: `~/.ai-docs/wiki`에 도메인 1개(`argon1025-side`)·레포 2개, `index.md`에 `## 의존 방향` 절 없음 → 템플릿에서 절을 제거해도 이전 작업 없음
- **버전 파일**: `.claude-plugin/marketplace.json` `metadata.version`이 2.8.0, `llm-wiki/.claude-plugin/plugin.json` `version`이 2.2.0으로 드리프트 상태
- **catalog.py 검사 구조**: `check()`가 `root.parent/registry.json`을 읽어 `inspect()`(문서 단위)·`inspect_across()`(문서 간)·`missing_indexes()`를 돌리며, `selected_names()`는 knowledge 밖 경로를 조용히 버림

## 확정 결정 (사용자 확인 2026-09-15)

- **그래프 분리**: 사용자 원문 "도메인, 하위 프로젝트 의존성 그래프를 들고있는게 필요하지 않을까 싶음 Index는 그럼 의존관계 보다는 각 프로젝트별 책임 등을 적는것으로" — 의존 간선은 `index.md`에서 빼고 별도로 보유
- **저장 위치**: 위키 루트 `deps.json`(`registry.json` 형제), `{"edges": [{"from","to","note","source"}]}` — `from`이 `to`를 호출·참조함, `note` 선택, 나머지 필수
- **index.md 절 축소**: `## 의존 방향` 절 제거 → 레포 구성·역인덱스·접근 좌표·제외 레포 4절, description 고정문 `{d} 레포 소관·역인덱스·변경 파급을 볼 때`
- **검사 추가**: `catalog.py --check`가 `deps.json` 끝점과 `index.md` 역인덱스의 `{domain}/{slug}` 참조를 `registry.json`과 대조 (사용자 선택 "넣음")
- **1층은 파생**: 전역 index 문서를 저작하지 않고 훅이 `registry.json`·각 도메인 `index.md` 첫 단락·`deps.json`에서 계산해 주입, 도메인 단위 화살표는 두지 않음
- **다른 도메인 문서**: 목록·본문 주입 없음, 간선이 가리키면 에이전트가 직접 Read

## 외부 계약

`deps.json` 규격(규약 신규 10장이 정본이 됨):

```json
{
  "edges": [
    {
      "from": "onestore-display/display-front",
      "to": "onestore-devcenter/devcenter-api",
      "note": "상품 조회 REST",
      "source": "관찰 — display-front @a1b2c3d 머지, 2026-09-15"
    }
  ]
}
```

- **키**: `from`·`to`·`source` 필수, `note` 선택, 그 밖의 키 금지 — `from`·`to`는 `^[a-z0-9]+-[a-z0-9-]+/[a-z0-9-]+$`
- **source**: 4장 출처 줄과 같은 꼴 `확인 — {자료·결정}, {날짜}` 또는 `관찰 — {slug} @{sha7} 머지, {날짜}`
- **유일성**: `(from, to)` 쌍은 하나, 자기 간선 금지 — 같은 쌍을 다시 관찰하면 `source`만 최신으로 갱신하고 `확인` 간선의 `note`는 `관찰`이 바꾸지 못함
- **정렬**: `from`, `to` 사전순 유지, 들여쓰기 2칸, 파일 끝 개행 — 병합 충돌 축소
- **부재**: 파일 없음 = 간선 0건, 에러 아님
- **삭제**: 기존 간선 삭제·방향 변경은 기존 값 교체이므로 7장 근거 판정을 거친 `확인`만 가능(`add`·`audit`)

훅 1층 출력 형식(헤더 다음, index 본문 앞):

```
# 도메인 2개 · 현재 onestore-devcenter
- onestore-devcenter — 개발자센터 셀러 콘솔·앱 등록 레포 모음
- onestore-display — 제품 전시·매대 레포 모음

# 의존 간선 2건 · onestore-devcenter에 닿는 것 (from → to = from이 to를 호출·참조)
- onestore-display/display-front → onestore-devcenter/devcenter-api — 상품 조회 REST
- onestore-devcenter/devcenter-front → onestore-devcenter/devcenter-api
```

- 도메인 설명은 그 도메인 `index.md` 본문에서 `# 제목` 다음 첫 비어 있지 않은 줄, index가 없으면 `(index.md 없음 — /llm-wiki:register)`
- 간선은 `from` 또는 `to`의 도메인이 현재 도메인인 것만, `from`·`to` 사전순, `note` 있으면 ` — {note}` 꼬리
- 간선 0건이면 간선 블록 자체를 두지 않음, 도메인 블록은 도메인 1개여도 항상 둠
- HARD 예산 초과 시 접는 순서: 목록(기존) → 간선 블록을 `# 의존 간선 N건 — Read {WIKI_ROOT}/deps.json` 한 줄로 → index 본문(기존). 도메인 블록은 접지 않음

## 선행 읽기

- `llm-wiki/references/doc-contract.md` 9장 — index.md 템플릿과 작성 주체 분담이 이번 변경의 기준선
- `llm-wiki/hooks/session_start.sh` 100~207행 — 블록 조립·접기 순서에 1층을 끼워 넣는 자리
- `llm-wiki/scripts/catalog.py` 190~370행 — `check_location`·`inspect`·`check`의 에러 수집 방식을 그대로 따름

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/scripts/catalog.py` | `DEPS_NAME`·`EDGE_RE` 상수, `load_edges(wiki_root)`, `lead_line(index_path)`, `check_deps(wiki_root, registry)`, `check_index_refs(path, registry)` 추가, `inspect`·`check`·`selected_names` 연결 | ⑦ — 표준 라이브러리(json·re)로 짜며 기존 검사 함수 구조에 붙임. 하위 단 불성립: 간선 스키마·registry 대조는 이 저장소에만 있는 규칙이라 기존 코드·라이브러리에 없음 |
| `llm-wiki/hooks/session_start.sh` | `tail` 블록을 1층 블록(도메인 목록 + 간선)으로 교체, 접기 단계 추가 | ⑦ — 기존 python 조립 코드 안에 약 30줄. 하위 단 불성립: 파생 규칙이 훅 고유 |
| `llm-wiki/rules/agent-guide.md` | 도입 문장·`도메인 지도` 불릿 수정, `의존 간선` 불릿 추가 | ⑥ |
| `llm-wiki/references/doc-contract.md` | 6장 면제 문구, 9장 절 축소·템플릿·고정문·작성 주체, 신규 10장 `deps.json` | ⑥ |
| `llm-wiki/skills/update/SKILL.md` | 3장 배정 불릿 분리(index.md / deps.json), 4장 deps.json 메인 직접 편집, 5장 커밋 규칙 | ⑥ |
| `llm-wiki/skills/add/SKILL.md` | 5장 초안·index.md 보강 불릿에 deps.json 간선 추가·삭제 | ⑥ |
| `llm-wiki/skills/register/SKILL.md` | 4장 고정문 변경, 도메인 이동 시 deps.json 끝점 치환 불릿 | ⑥ |
| `llm-wiki/skills/audit/SKILL.md` | 2장 신호 표에 `## 의존 방향` 절 → `이동`(deps.json) 행 추가 | ⑥ |
| `llm-wiki/README.md` | 동작 방식·위키 구조 갱신 | ⑥ |
| `.claude-plugin/marketplace.json`, `llm-wiki/.claude-plugin/plugin.json` | 버전 2.9.0, description에 "의존 간선" 반영 | ⑥ |

### catalog.py

- **상수**: `DEPS_NAME = "deps.json"`, `EDGE_RE = re.compile(r"^(?P<domain>[a-z0-9]+-[a-z0-9-]+)/(?P<repo>[a-z0-9-]+)$")`, `EDGE_KEYS = {"from", "to", "note", "source"}`, `EDGE_REQUIRED = {"from", "to", "source"}`
- **`load_edges(wiki_root) -> list[dict]`**: `load_json(wiki_root / DEPS_NAME, {})`에서 `edges`가 리스트면 dict 항목만 반환, 아니면 빈 리스트 — 훅과 검사가 공유하며 모양 검증은 하지 않음
- **`lead_line(index_path) -> str`**: `body_lines()` 결과에서 `# `로 시작하는 첫 줄 다음의 첫 비어 있지 않은 줄, 없으면 빈 문자열 — 훅의 도메인 설명 파생용
- **`check_deps(wiki_root, registry) -> list[str]`**: 파일 없음 → 빈 리스트. JSON 깨짐·`edges` 리스트 아님 → 에러 1건. 간선마다 순서대로 검사: 허용 외 키, 필수 키 누락 또는 빈 문자열, `from`·`to` 형식, 자기 간선, 끝점 도메인이 `domains`에 없음, 끝점 레포가 `repos`에 없거나 `domain` 불일치, `(from,to)` 중복 — 메시지 앞에 `간선 {i}: {from} → {to}` 접두. registry가 None이면 형식·중복·자기 간선만 검사
- **`check_index_refs(path, registry) -> list[str]`**: `path.name == INDEX_NAME`일 때만, `## 역인덱스` 절의 `|`로 시작하는 행에서 `EDGE_RE` 패턴과 같은 `{domain}/{slug}` 토큰(정규식 `\b[a-z0-9]+-[a-z0-9-]+/[a-z0-9-]+\b`)을 뽑아 `repos`에 없거나 `domain`이 다르면 `역인덱스 참조 {token}가 registry.json에 없음` — 역인덱스 절로 한정하는 이유는 접근 좌표의 URL 경로가 오탐되지 않게 하기 위함
- **`inspect`**: `check_body` 뒤에 `check_index_refs(path, registry)` 결과를 덧붙임(registry 있을 때만)
- **`selected_names`**: `candidate.resolve() == (root.parent / DEPS_NAME).resolve()`이면 `"deps.json"`을 names에 추가한 뒤 계속
- **`check`**: `only is None or DEPS_NAME in only`이면 `check_deps(root.parent, registry)`의 메시지를 `(DEPS_NAME, message)`로 errors에 추가. `files`가 비고 index 에러도 없더라도 deps 에러가 있으면 출력하도록 초기 조기 반환 조건에 deps 에러 포함. 마지막 요약 줄은 기존 형식 유지
- **하지 않는 것**: `## 의존 방향` 절 존재를 에러로 내지 않음 — 다른 사용자 위키의 기존 index를 즉시 깨지 않고 audit 신호로 이동시킴

### session_start.sh

- **입력**: `edges = catalog.load_edges(wiki_root)`, `domains = sorted(registry.get("domains", {}) or {})`
- **도메인 블록**: `# 도메인 {len}개 · 현재 {domain}` 머리 + 도메인마다 `- {name} — {catalog.lead_line(knowledge/name/index.md)}`(index 없으면 안내문). `domain`이 None(미등록 레포)이면 머리를 `# 도메인 {len}개`로 두고 목록만 — 미등록 상태에서도 어떤 도메인이 있는지 보이는 것이 register 안내에 도움
- **간선 블록**: `domain`이 있을 때 `from`·`to` 중 하나의 앞부분(`/` 앞)이 `domain`과 같은 간선을 `(from, to)` 정렬로 `- {from} → {to}[ — {note}]`, 머리 `# 의존 간선 {n}건 · {domain}에 닿는 것 (from → to = from이 to를 호출·참조)`. `EDGE_RE`에 맞지 않는 항목은 건너뜀(검사는 `--check`의 몫)
- **조립 순서**: `guide` → `header` → 도메인 블록 → 간선 블록 → `index_block` → `spaces` → (기존 `tail` 제거)
- **접기**: 기존 목록 접기 while 루프 뒤, index 접기 앞에 `if edge_block and 초과: edge_block = f"# 의존 간선 {n}건 — Read {wiki_root / 'deps.json'}"` 한 단계 삽입
- **주석**: 파일 머리 주석의 주입 순서 설명과 148행 주석("도메인 지도… 레포 구성·의존 방향·역인덱스")에서 의존 방향을 빼고 1층 설명 한 줄 추가

### rules/agent-guide.md

- **도입 문장**: "아래 도메인 목록·의존 간선, 도메인 `index.md` 본문과 목록(도메인 루트 + 현재 레포)에서 요청에 걸리는 문서를 골라 읽고 진행하며"
- **도메인 지도 불릿**: "`index.md` 본문은 레포 구성·역인덱스라 코드 변경 시 어느 레포가 그 업무를 맡는지 찾을 때 먼저 봄"
- **의존 간선 불릿(신규, 도메인 지도 다음)**: "주입된 간선에서 현재 레포를 `to`로 가진 `from` 레포가 변경의 파급 대상이며, 다른 도메인 레포이면 그 도메인 `index.md`를 Read하고 `python3 {catalog.py} --root {WIKI_ROOT}/knowledge/{domain}/{slug}`로 목록을 본 뒤 필요한 문서만 엶 — 간선의 추가·삭제도 스킬로만 함"

### references/doc-contract.md

- **6장 참조 금지**: "`index.md`의 역인덱스·의존 방향은" → "`index.md`의 역인덱스와 `deps.json`의 간선은"
- **9장**: 첫 문단 "어느 레포를 확인해야 하는가" 유지. `절 고정` 4개(`## 레포 구성`·`## 역인덱스`·`## 접근 좌표`·`## 제외 레포`), `도메인 밖 참조`는 역인덱스만 언급하고 "레포 간 의존은 10장 `deps.json`에 두며 index.md에 적지 않음" 추가, `작성 주체`의 update 보강 항목에서 의존 방향 제거, description 고정문 교체, 템플릿에서 `## 의존 방향` 블록 삭제
- **10장 `deps.json`(신규)**: 외부 계약 절의 규격을 그대로 옮기고 다음 불릿을 더함 — `담는 기준`: 레포 사이의 호출·참조·소비 관계만, 한 레포 안 모듈 의존은 담지 않음, 1장 grep 테스트 면제(지도이지 사실 문서가 아님) / `작성 주체`: update가 diff의 빌드 파일 모듈 의존·HTTP 클라이언트·메시지 발신·DB 공유에서 `관찰` 간선 추가, add가 자료·대화에서 `확인` 간선 추가·삭제, register가 도메인 이동 시 끝점 치환, audit가 `## 의존 방향` 절 이동 / `검사`: `catalog.py --check`가 위 외부 계약 규칙과 registry 대조를 봄 / `커밋`: `docs(deps): {요약}`

### skills/update/SKILL.md

- **3장 `index.md 배정` 분리**: index.md는 "신규 문서 → `## 역인덱스` 행, 레포 역할·접근 좌표 → `## 레포 구성`·`## 접근 좌표` 보강"으로 좁히고, 새 불릿 `deps.json 배정`: "diff에서 레포 간 의존(빌드 파일의 모듈 의존·HTTP·Feign 클라이언트·AMQP 발신·DB 공유)이 확정되고 양 끝이 등록 레포면 규약 10장 형식의 `관찰` 간선으로 배정, 한쪽이 미등록이면 `기각 — 미등록 레포`"
- **4장**: 머리 문단에 "deps.json은 문서 에이전트에 보내지 않고 메인이 규약 10장 유일성·정렬 규칙대로 직접 편집" 한 문장
- **5장 커밋**: 문서 커밋 규칙 뒤에 "deps.json이 바뀌면 `docs(deps): 간선 N건 · {slug} @{sha7}` 한 커밋" 추가, 전수 검사 명령은 deps.json도 보므로 변경 없음
- **6장 보고 `문서`**: "간선 추가 건수" 덧붙임

### skills/add/SKILL.md

- **5장 `index.md 보강`**: "의존 방향" 언급이 없으므로 유지하고, 새 불릿 `deps.json`: "자료·대화에서 레포 간 의존이 확정되면 규약 10장 형식의 `확인` 간선을 추가하며 기존 간선 삭제·방향 변경은 3장 교체 판정을 거침 — 초안 승인 표에 간선 행을 `from → to — note` 꼴로 포함, 커밋은 `docs(deps): {요약}`"

### skills/register/SKILL.md

- **4장 신규 도메인**: description 고정문 `{d} 레포 소관·역인덱스·변경 파급을 볼 때`
- **4장 도메인 이동**: 승인 하나 불릿 끝에 "`deps.json`의 `{old}/{slug}` 끝점을 `{new}/{slug}`로 치환하고 `--check`로 대조" 추가, 같은 커밋에 포함

### skills/audit/SKILL.md

- **2장 신호 표**: `| index.md에 ## 의존 방향 절 (규약 9장) | 이동 — 후: deps.json 간선 from·to·note, 비고에 원문 줄 |` 행을 템플릿 밖 절 행 다음에 추가 — 4장 적용 에이전트는 index.md에서 절을 지우고, deps.json 편집은 메인이 승인 표대로 직접 수행(update 4장과 같은 이유)
- **5장 커밋**: deps.json 변경은 `docs(deps): audit 의존 방향 이동 N건`

### README.md

- **동작 방식**: `SessionStart`·`주입 범위` 불릿에 1층(도메인 목록·설명, 현재 도메인에 닿는 간선)을 더하고 `도메인 지도` 불릿에서 의존 방향 제거, 신규 불릿 `의존 간선`: "`deps.json`의 레포 간 간선 중 현재 도메인에 닿는 것을 양방향으로 주입하며 `--check`가 끝점을 registry와 대조, 다른 도메인 문서는 간선이 가리킬 때 직접 엶"
- **위키 구조**: 트리에 `├── deps.json  # update(관찰)·add(확인)가 편집: 레포 간 의존 간선 {from,to,note,source}` 행 추가, `index.md` 주석에서 의존 방향 제거
- **검사 항목 문장**: "위치·설명 중복" 뒤에 "간선 끝점·역인덱스 참조" 추가

### 버전 파일

- `.claude-plugin/marketplace.json` `metadata.version` 2.9.0, llm-wiki description 끝에 ", 세션 주입은 도메인 목록·의존 간선 → 도메인 index → 현재 레포 3층"
- `llm-wiki/.claude-plugin/plugin.json` `version` 2.9.0 — 2.2.0 드리프트 정정

## 커밋 분해

픽스처는 스크래치 디렉터리에 만들며 커밋에 포함하지 않음. 픽스처 구성: `wiki/registry.json`(도메인 `acme-dev`·`acme-shop`, 레포 `dev-api`(acme-dev)·`dev-front`(acme-dev)·`shop-front`(acme-shop), remotes `github.com/acme/{slug}`), `wiki/knowledge/{domain}/index.md` 2장(제목·한 줄 설명·레포 구성), `wiki/deps.json`(간선 `acme-shop/shop-front → acme-dev/dev-api` note "상품 조회 REST", `acme-dev/dev-front → acme-dev/dev-api`), 프로젝트 `proj/`는 `git init` 후 `git remote add origin https://github.com/acme/dev-api.git`.

| # | 범위 | 검증 |
|---|---|---|
| 1 | `catalog.py` 간선·역인덱스 검사와 헬퍼 | `python3 llm-wiki/scripts/catalog.py --check --root {fix}/wiki/knowledge` → `에러 0건` exit 0. deps.json에 `acme-dev/dev-api → acme-dev/dev-api`(자기 간선), `acme-dev/nope → acme-dev/dev-api`(미등록), 중복 쌍, 키 `via` 추가 후 재실행 → 에러 4건에 각각 `자기 간선`·`registry.json에 없음`·`중복`·`허용되지 않는 키` 문구, exit 1. `python3 … --check --root … {fix}/wiki/deps.json` 경로 지정 시에도 같은 에러. index.md 역인덱스에 `acme-shop/ghost(역할)` 행 추가 → `역인덱스 참조 acme-shop/ghost가 registry.json에 없음` exit 1. 실제 위키 `python3 llm-wiki/scripts/catalog.py --check --root ~/.ai-docs/wiki/knowledge` → 기존과 같이 exit 0 |
| 2 | `session_start.sh` 1층 주입 | `cd {fix}/proj && echo '{"source":"clear"}' \| LLM_WIKI_ROOT={fix}/wiki CLAUDE_PLUGIN_ROOT=$PWD/../../llm-wiki(절대경로) bash llm-wiki/hooks/session_start.sh \| python3 -c 'import json,sys;print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'` → 출력에 `# 도메인 2개 · 현재 acme-dev`, `- acme-shop — ` 설명 줄, `# 의존 간선 2건 · acme-dev에 닿는 것`, `acme-shop/shop-front → acme-dev/dev-api — 상품 조회 REST` 순서로 포함되고 `# 다른 도메인` 문자열은 없음. deps.json 삭제 후 재실행 → 간선 블록 없고 도메인 블록만. 실제 레포에서 `echo '{"source":"clear"}' \| bash llm-wiki/hooks/session_start.sh` → `# 도메인 1개 · 현재 argon1025-side` 포함, exit 0, JSON 파싱 성공 |
| 3 | `doc-contract.md` 9·10장, `agent-guide.md` | `grep -c '의존 방향' llm-wiki/references/doc-contract.md llm-wiki/rules/agent-guide.md` → 0, `grep -n '^## 10\. deps.json' llm-wiki/references/doc-contract.md` → 1행. 훅 재실행 출력에 `의존 간선` 불릿 포함 |
| 4 | 스킬 4종(update·add·register·audit) | `grep -c 'deps.json' llm-wiki/skills/{update,add,register,audit}/SKILL.md` → 각 1 이상, `grep -rn '의존 방향' llm-wiki/skills` → audit 신호 표 행 1건만 |
| 5 | README·버전 2.9.0 | `python3 -c 'import json;print(json.load(open(".claude-plugin/marketplace.json"))["metadata"]["version"], json.load(open("llm-wiki/.claude-plugin/plugin.json"))["version"])'` → `2.9.0 2.9.0`, `grep -c 'deps.json' llm-wiki/README.md` → 2 이상 |

## 특이 사항

- **범위 밖**: 도메인 단위 요약 그래프, 전역 index 문서 저작, 다른 도메인 목록 주입, `init` 스킬 변경(deps.json 부재는 정상), `update.py` 변경
- **의도적 단순화**: 간선 `note`는 자유 문장이며 접점 종류(HTTP·메시지·DB)를 열거형으로 두지 않음 — 종류별 조회가 필요해지면 그때 `kind` 키를 검사와 함께 추가
- **의도적 단순화**: `## 의존 방향` 절 존재를 `--check` 에러로 내지 않고 audit 신호로만 둠 — 기존 사용자 위키를 즉시 깨지 않기 위함이며, 모든 위키가 이전되면 에러로 승격 가능
- **역인덱스 참조 검사 한계**: `## 역인덱스` 절의 표 행만 보므로 다른 절의 `{domain}/{slug}` 표기는 검사하지 않음
- **후속**: 실제 위키 `argon1025-side/index.md`의 description 고정문은 `/llm-wiki:audit`의 `설명` 조치로 새 고정문에 맞춤, 커서가 HEAD보다 뒤인 상태는 머지 후 `/llm-wiki:update`로 반영
- **핸드오프**: 승인 시 slug `feat-wiki-deps-graph`로 `.ai-docs/workspace/feat-wiki-deps-graph/plan.md`(신규)·`feedback.md`를 한 커밋으로 남기고 구현은 새 세션 `/plan-workflow:execute`로 시작

## 추가 계획 2026-09-15 — 세션 주입 접기 제거

- 폐기: `## 외부 계약`의 "HARD 예산 초과 시 접는 순서" 불릿과 `### session_start.sh`의 `접기` 불릿 — 목록·index 본문·간선 블록 어느 것도 접지 않음

### 의도

- **왜**: 에이전트는 목록의 `description`만으로 문서를 열지 말지 정하므로 목록이 한 줄로 접히면 그 세션은 문서의 존재를 모른 채 코드를 고치며, 접힘을 푸는 명령을 건너뛰어도 신호가 없음 — 하드 12,000토큰은 문서 약 200건에서 닿는 값이라 접기가 아니라 audit 분할이 답인 상태임
- **누가**: 문서가 많은 도메인·레포에서 세션을 여는 에이전트, 특히 명령 재실행 단계를 건너뛰기 쉬운 무인 실행과 서브에이전트
- **완료**: `session_start.sh`가 예산과 무관하게 도메인 목록·간선·index 본문·도메인 루트 목록·레포 목록을 항상 전체 주입하고, 소프트 8,000토큰 초과 시 `# 위키 목록이 약 N토큰 — /llm-wiki:audit 로 정리 권장` 한 줄만 앞에 붙음

### 확정 결정 (사용자 확인 2026-09-15)

- **접기 제거**: 사용자 원문 "위키 문서 목록을 접는 기능이 있는데 이건 제외해도 되지 않을지? 결국 해당 프로젝트 수정 시 해당 문서 목록 전체를 알고 있어야함으로.. 누락되면 그게 더 위험할듯함" — 목록 접기, index 본문 접기, 간선 블록 접기를 모두 제거
- **소프트 경고 유지**: 8,000토큰 초과 시 audit 권고 한 줄은 그대로 둠 — 누락 없이 목록 비대를 알리는 유일한 신호

### 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/hooks/session_start.sh` | `HARD_BUDGET` 상수, `folded` while 루프, index 본문 접기 블록 삭제, `spaces`를 본문 문자열 목록으로 단순화(접기용 `root`·`shallow` 필드 불필요), 관련 주석 정리 | ⑥ |
| `llm-wiki/README.md` | `주입 범위` 불릿에서 "하드 12,000토큰을 넘으면 가장 큰 목록이 전체 보기 명령 한 줄로 접힘" 삭제 | ⑥ |

- **session_start.sh**: `SOFT_BUDGET = 8000`과 마지막 `if catalog.estimate_tokens(context) > SOFT_BUDGET:` 블록만 남기고, `assemble()`는 `guide` → `header` → 도메인 블록 → 간선 블록 → `index_block` → `spaces` 순 그대로 유지
- **doc-contract.md**: 9장 "토큰 상한은 두지 않으며 크기는 절 고정으로 다룸"이 이미 같은 방향이라 변경 없음

### 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 6 | `session_start.sh` 접기 제거 — 커밋 1~5는 이미 브랜치에 있으므로(`4650f9a`~`eb448a4`) 새 커밋으로 | 픽스처 `wiki/knowledge/acme-dev/dev-api/`에 `for i in $(seq 1 300)`으로 frontmatter 3키를 갖춘 문서 300건 생성 후 커밋 2와 같은 훅 명령 실행 → 출력에 `doc-001` … `doc-300` 300행 전부 포함(`grep -c '^doc-' → 300`), 첫 줄이 `# 위키 목록이 약` 으로 시작, `전체 보기`·`Read ` 접기 문자열 없음, exit 0. `grep -c 'HARD_BUDGET\|folded' llm-wiki/hooks/session_start.sh` → 0 |
| 7 | README 주입 범위 문구 | `grep -c '접힘' llm-wiki/README.md` → 0 |

### 특이 사항

- **주입 크기 상한 없음**: 목록이 커질수록 세션 시작·compact마다 그만큼 주입되며 제어 수단은 audit 권고와 사용자의 문서 정리뿐 — 상한이 다시 필요해지면 접기가 아니라 "레포 목록은 전체, 도메인 루트 목록만 축약" 같은 누락 없는 대안을 검토
