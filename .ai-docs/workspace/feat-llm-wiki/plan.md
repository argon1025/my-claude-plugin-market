# llm-wiki 리뷰 반영 계획 (v1 계획 개정)

브랜치 `feat/llm-wiki`, 워크스페이스 `feat-llm-wiki`. 2026-09-14 리뷰 세션의 확정 결정을 플러그인 코드·규약·스킬에 내리는 계획이다. 앞선 계획(`be484e5` 스냅샷)은 이 문서로 대체되며, 그 계획의 "프로젝트 하위 레포 층은 30건 초과 시 업그레이드" 항목은 폐기된다.

## 의도

- **왜**: v1의 `knowledge/common` + `knowledge/projects/{p}` 2층은 레포 종속 사실의 자리가 없어 description에 레포명을 넣는 우회를 강요하고, 회사 전체 공통 폴더는 실사용 문서가 없으며, init 한 스킬이 저장소 생성과 레포 등록을 겸해 빈 원격 저장소를 clone한 경우 골격이 만들어지지 않고, update가 공통 후보를 review.md로 넘겨 무인 갱신이 도메인 공통 사실을 남기지 못함
- **누가·언제**: 사용자와 팀원이 여러 레포가 한 도메인을 이루는 사내 프로젝트(onestore-devcenter)와 개인 사이드 프로젝트를 오가며 세션을 열 때, 그리고 무인 update를 돌린 뒤 문서 위치·충돌 인박스를 정리할 때 겪음
- **완료 조건**: `knowledge/{조직}-{도메인}/`(도메인 루트) + `{레포 slug}/` 2층 고정 구조를 `catalog.py --check`가 강제하고, init·register가 분리되어 registry.json 유무로 초기화를 판정하고, 도메인마다 index.md 본문이 세션에 통째로 주입되고, update가 묶음 단위로 추출해 도메인 루트까지 직접 보강하며, 훅이 startup·resume에서만 600초 주기로 pull하고, 각 커밋이 `--check` 에러 0과 픽스처 수동 검증으로 닫힘

사용자 원문(2026-09-14): "2026-09-14 리뷰 세션에서 아래 결정이 확정되었다. 결정 자체는 다시 묻지 말고, 결정이 코드·규약에 어떻게 내려가는지만 계획한다."

## 사용자가 확인한 결정 (원문)

| 축 | 결정 | 사용자 답 원문 |
|---|---|---|
| 폴더 구조 | `knowledge/{조직}-{도메인}/` 루트 = 도메인 공통, `{레포 slug}/` = 레포 종속, 2층 고정, adr/ 양층 허용, 회사 전체 공통 폴더 없음, 레포는 단일 도메인 | 결정 1 (A안) |
| 위치 판정 | "이 레포를 지워도 참이면 도메인 루트, 아니면 레포 폴더" 한 단계 | 결정 1 |
| 스킬 분리 | init = clone/git init·원격·골격, register = 레포 등록·도메인·브랜치·index.md 골격·paths.json·도메인 이동·remote 추가·상태 표. 초기화 판정은 registry.json 유무 | 결정 2 |
| index.md | 도메인 루트 예약 파일, 레포 구성·역할·접근 좌표·역인덱스, 훅이 본문 전체 주입, register 골격·update 보강, 2장 한 주제·6장 참조 금지 면제 | 결정 3 |
| index.md 토큰 상한 | 두지 않음 — 본문 템플릿을 정하고 필요한 내용만 기재되게 가이드 | "인덱스 상한은 둬도 의미가 없을 듯 큰 회사 도메인인 경우 그럼 누락될 가능성이 있으니 그냥 내부 본문 템플릿을 정하고 필요한 내용만 기재되도록 가이드되는편이 좋은거 같기도함 (해당 부분은 너가 추가 검토 …)" |
| index.md 원형 | 기존 `system-repository-map.md`의 저장소 표·의존 방향·역인덱스로 변경 파급 조회가 가능해야 함 | "실제로 index 와 유사한 문서를 기존에는 … system-repository-map.md 이렇게 쓰고 있었어 이렇게 하니 코드 변경 시 어떤 프로젝트를 확인해야하는지 영향받는 프로젝트가 뭔지 등 확인이 가능했음 이런 기능이 가능하도록 하고싶음" |
| 주입 범위 | 도메인 루트 전수 + 현재 레포 폴더 전수, 형제 레포는 이름·건수 한 줄, 다른 도메인은 이름만, 예산 소프트 8,000·하드 12,000 유지 | 결정 4 |
| update | 공통 후보 → review.md 규칙 삭제, 도메인 루트 직접 보강, 인박스에는 충돌·배치 내 상충만, 추출 단위 = 묶음(머지 5건 또는 diff 500KB 중 먼저) | 결정 5 |
| 묶음 경계 | `update.py pending`이 work.json에 냄 | "update.py pending이 work.json에 냄 (Recommended)" |
| 검색 보강 | 계획에서 제외 — keywords·agent-guide grep 규칙 모두 보류 | "일단 프론트메터 키워드 추가 계획은 제외 검색 보강은 이후 좀 사용해보고 다시" |
| 내부 파일 | registry.json `repos.{slug}` = domain·remotes·branch, `projects` → `domains`, summary·stack 삭제, state = cursor·at, `.local/paths.json` 유지, review.md → inbox.md | 결정 7 |
| 훅 pull | FETCH_HEAD 600초, `LLM_WIKI_SYNC_MINUTES` 덮어쓰기, 대기 3초 상한, pull은 startup·resume만, 주입은 전 이벤트 | 결정 8 |
| 보류 | 다중 위키, always 도메인, 레포 다중 도메인, 검색 보강 | "보류 (계획에 넣지 않음)" + 위 답 |

## 현재 코드 요약 (탐색 결과)

- **catalog.py 403줄**: `LOCATION_RE = ^(common|projects/[a-z0-9-]+)(/adr)?/[a-z0-9-]+\.md$`(L45), `docs()`가 rglob 전수(L124), `build()` 행 형식 `{name}{!} — {description}`(L140), `check()`·`inspect_across()`(description 완전 중복), `resolve_repo()`가 `(slug, project)` 반환(L338), 훅과 update.py가 import
- **update.py 311줄**: `pending`이 머지 1건당 `{sha7}.diff` 추출 후 work.json에 `project`·`commits[]`(L197), `advance`가 cursor·branch·at·merges·docs 5키 기록(L248), `status` 표 출력(L259), 미등록 안내가 `/llm-wiki:init`(L146)
- **session_start.sh 180줄**: 위키 판정 `[ -d $WIKI/knowledge ]`(L13), FETCH_HEAD 3600초 게이트(L27), stdin 미사용, 스페이스 = `knowledge/common` + `knowledge/projects/{p}`(L137~141), 형제 레포 summary 표시(L93), review.md 건수(L105), 하드 예산 접기(L160)
- **hooks.json**: SessionStart 1개, matcher 없음 — 전 이벤트 실행이라 결정 8의 "주입은 전 이벤트"를 이미 충족하며 변경 없음
- **doc-contract.md 84줄**: 3장 위치 판정 2단(common/projects), 2장 범위 낱말이 레포명을 description에 넣게 함, 7장 grep 경로가 common·projects, 충돌 → review.md
- **스킬 4종**: init이 저장소 생성 + 레포 등록(프로젝트·브랜치·summary·stack) 겸함, update 3장이 공통 후보를 review.md로, add/audit이 common·projects 어휘와 review.md 사용
- **실사용 위키 없음**: `~/.ai-docs/wiki` 부재 — 기존 문서 이관 없음, registry 스키마 비호환 변경 가능

## 설계 결정

### D1. 저장소 구조와 경로 검사

```
~/.ai-docs/wiki/                          # LLM_WIKI_ROOT, 별도 git 저장소
├── registry.json                         # register가 편집. 초기화 판정 기준(있으면 위키 있음)
├── state/{slug}.json                     # update만 편집: {"cursor": "<sha40>", "at": "YYYY-MM-DD"}
├── inbox.md                              # update가 append: 무인 갱신이 판정 못 한 충돌, add가 소비
├── .gitignore                            # .local/
├── .local/paths.json                     # 머신별 {slug: 절대경로}, 훅·register가 기록(미추적)
└── knowledge/
    └── {조직}-{도메인}/                   # 도메인 루트 — 레포를 지워도 참인 사실
        ├── index.md                      # 예약·필수: 레포 구성·접근 좌표·역인덱스
        ├── *.md
        ├── adr/                          # 선택
        └── {레포 slug}/                  # 레포 종속 — 이 레포를 지우면 거짓이 되는 사실
            ├── *.md
            └── adr/                      # 선택
```

- **LOCATION_RE**: `^(?P<domain>[a-z0-9]+-[a-z0-9-]+)(?:/(?!adr/)(?P<repo>[a-z0-9-]+))?(?:/adr)?/[a-z0-9-]+\.md$` — 도메인 이름은 하이픈 1개 이상(`common`·`projects` 자동 배제), 레포 폴더는 `adr` 예약어 제외, 깊이는 도메인 2·adr 3·레포 3·레포 adr 4 세그먼트만 통과. 에러 문구 `위치가 규약에 없음 ({relative}) — knowledge/{조직}-{도메인}/ 루트 또는 그 아래 {레포 slug}/ 평면과 각각의 adr/만, 파일명은 kebab-case`
- **registry 대조**: `check_location`이 `root.parent / "registry.json"`을 읽을 수 있으면 도메인 폴더가 `domains`에, 레포 폴더가 `repos`에 있고 그 `domain`이 폴더와 같은지 검사(`도메인 {d}가 registry.json에 없음 — /llm-wiki:register`, `레포 폴더 {slug}가 registry.json에 없거나 도메인이 다름`). registry.json이 없거나 깨졌으면 정규식 검사만 수행(사다리 ⑥: 함수 1개에 조건 2개 추가)
- **index.md 검사**: `knowledge/` 첫 단계 디렉터리마다 `index.md`가 없으면 에러 `{d}/index.md 없음 — /llm-wiki:register가 생성`, 레포 폴더 안의 `index.md`는 에러 `index.md는 도메인 루트에만` — frontmatter 3키·첫 줄 제목 검사는 일반 문서와 같고 토큰 상한은 두지 않음
- **shallow 목록**: `docs(root, shallow=False)`에 `shallow=True`이면 `root/*.md`와 `root/adr/*.md`만 수집. `build()`는 목록 모드에서 `root/index.md`를 행에서 제외(본문이 따로 주입되므로), `--check`는 포함. CLI `--shallow` 추가. 사다리 ⑥(조건 1개)
- **레포 판정**: `resolve_repo()` 반환을 `(slug, domain)`으로, `info.get("project")` → `info.get("domain")`. slug 규칙(remote 마지막 경로·common-dir 폴백)은 그대로
- **소트**: `sort_key`는 유지 — 레포 목록에서 `adr/` 문서가 먼저, 평면 문서가 뒤

### D2. registry.json·state·inbox

```json
{
  "domains": { "onestore-devcenter": {}, "personal-trendlog": {} },
  "repos": {
    "devcenter-api": { "domain": "onestore-devcenter", "remotes": ["bitbucket.example.com/cms/devcenter-api"], "branch": "develop" },
    "trendlog-backend": { "domain": "personal-trendlog", "remotes": ["github.com/argon1025/trendlog-backend"], "branch": "main" }
  }
}
```

- **domains 값**: 빈 객체 `{}` — 설명은 index.md 본문으로 가고, 보류 항목(always 도메인)이 들어올 자리를 남김. `domains`가 배열이면 키 추가 시 스키마가 바뀌므로 객체 유지
- **state/{slug}.json**: `{"cursor", "at"}` 2키 — `advance`의 `--merges`·`--docs` 인자와 `branch` 기록 삭제, 커밋 메시지의 건수는 스킬이 씀. 분리 유지 근거(레포별 커서 충돌 방지)는 그대로
- **inbox.md**: review.md 개명. 행 형식 `- [{날짜}] [{domain}] {주제} — 기존 {값} ({파일:절}, {출처}) / 새 {값} ({slug} @{sha7} {code})` 유지, 남기는 사유는 `충돌`·`배치 내 상충` 2종만
- **status 삭제**: `update.py status`를 지우고 register 스킬 6장이 registry.json·`state/*.json`·`.local/paths.json` 3파일을 Read해 표를 조립(사다리 ①: 에이전트가 JSON 3개를 읽어 표를 내는 데 코드가 필요 없음)

### D3. index.md 템플릿 (토큰 상한 대체)

사용자가 지목한 기존 문서 `onestore-devcenter-claude-plugin-marketplace/knowledge/system-repository-map.md`(약 9,200토큰)가 원형이다. 그 문서에서 "코드 변경 시 어떤 레포를 확인해야 하는지"를 답하는 절은 저장소 표(스택·접점·소관)·의존 방향·역인덱스 셋이고, 뒤에 붙은 반영 순서 계약 불릿(약 1,900토큰)은 사실이라 일반 문서로 분리하며 제외 저장소 표(약 1,200토큰)는 선택 절로 둔다. `references/doc-contract.md`에 `## 9. index.md` 절을 두고 아래 템플릿을 정본으로 싣는다.

```markdown
---
description: {도메인} 레포 소관·의존 방향·변경 파급을 볼 때
updated: YYYY-MM-DD
verified: YYYY-MM-DD
---

# {도메인 이름}

{한 줄 설명 — register 질문의 답}

## 레포 구성

| 레포 | 스택 | 접점 | 소관 |
|---|---|---|---|
| {slug} | {언어·프레임워크 — register가 package.json·pom.xml·build.gradle에서 초안} | {셀러·운영자·파트너·내부 중} | {한 줄 소관 — 모르면 "아직 정해지지 않음"} |

## 의존 방향

```
client ← autoconfigure ← starter ← {api, agent}
front → api
```

## 역인덱스

| 업무 영역 | 관련 레포(역할) |
|---|---|
| {업무 낱말} | {slug}({역할}) · {slug}({역할}) · {다른 도메인}/{slug}({역할}) |

## 접근 좌표

- {환경·시스템} — {호스트·URL·프로젝트 키·계정 이름} — 비밀값 금지, 좌표 1건당 1불릿, 호출 예시는 코드 블록

## 제외 레포

| 레포 | 사유 |
|---|---|
```

- **규칙**: 절은 위 5개만(`## 의존 방향`·`## 접근 좌표`·`## 제외 레포`는 내용이 있을 때만), 절 추가와 사실 불릿(반영 순서 계약·정책·함정) 금지 — 그런 사실은 도메인 루트 일반 문서(예: `cmsapp-release-order.md`)로 두고 역인덱스가 그 레포 집합을 가리킴. 역인덱스·의존 방향은 다른 도메인 레포를 `{domain}/{slug}` 꼴로 적을 수 있음(도메인을 나눠도 파급 조회가 끊기지 않게). `description` 고정문, 2장 한 주제·6장 참조 금지 면제, 기본 브랜치·remote는 registry.json이 정본이라 표에 두지 않음
- **작성 주체**: register가 골격(제목·한 줄 설명·레포 구성 1행: 스택 초안·접점 `—`·소관 "아직 정해지지 않음")을 만들고 레포 추가·도메인 이동 시 행을 옮김. update가 `관찰` 출처로 소관·접점·의존 방향(빌드 파일의 모듈 의존·Feign·AMQP 발신)·역인덱스(신규 문서가 다루는 업무 영역과 레포)를 보강. add가 `확인` 출처로 접근 좌표·역인덱스를 보강
- **크기 신호**: 원형 문서에서 지도 절만 남기면 35레포 기준 약 5,500토큰이고 도메인을 2~3개로 나누면 도메인당 약 2,000~2,500토큰이라 소프트 8,000 안에 든다. 훅이 index 블록 머리에 `# 도메인 {d} index.md · 약 N토큰`을 적고, 하드 예산 초과 시 목록 두 개를 먼저 접은 뒤에도 넘치면 index 본문을 `# index.md 약 N토큰 — Read {절대경로}` 한 줄로 접음. audit 진단 표에 `index.md에 템플릿 밖 절 또는 사실 불릿 → 이동(도메인 루트 일반 문서로)` 신호 행 추가
- **why**: 하드 상한은 대형 도메인에서 레포 행·역인덱스 행을 누락시키는 쪽으로 작동하고, 소프트 8,000 경고와 audit이 이미 크기 신호를 내므로 상한을 두지 않음(사용자 검토 요청에 대한 권장안). 사용자 원문 "코드 변경 시 어떤 프로젝트를 확인해야하는지 영향받는 프로젝트가 뭔지 등 확인이 가능했음 이런 기능이 가능하도록 하고싶음"

### D4. 스킬 5종과 경계

| 스킬 | 역할 | 정지점 | 쓰는 곳 |
|---|---|---|---|
| `init` | 위키 clone 또는 `git init`, 원격 연결, 골격 생성(registry.json 없을 때) | 원격 URL 질문 | registry.json·`state/`·`.gitignore` |
| `register` (신설) | 현재 레포 등록·도메인 선택 또는 신설·기본 브랜치·index.md 골격·paths.json·도메인 이동·remote 추가·상태 표 | 질문 1라운드 + 폴더 이동 승인 | registry.json·`knowledge/{d}/index.md`·`.local/paths.json` |
| `update` | 묶음 단위 추출 → 도메인 루트·레포 폴더 직접 보강 → 커서 전진 | 없음 | `knowledge/{d}/**`·`state/`·`inbox.md` |
| `add` | 자료·대화·inbox.md 행 반영 | 충돌 질문 1회 + 승인 1회 | `knowledge/{d}/**`·`inbox.md` 소비 |
| `audit` | 조각·중복·낡음·규약 위반·index.md 템플릿 이탈 정리 | 승인 표 1회 | 전체 |

- **init 판정**: `{WIKI_ROOT}/registry.json` 있음 → `pull --ff-only` 후 register 안내로 끝. 디렉터리만 있고 registry.json 없음(빈 원격 clone 포함) → 골격 생성. 디렉터리 없음 → 원격 URL을 물어 clone(빈 저장소면 골격 생성) 또는 `git init`. 골격 = `registry.json` `{"domains": {}, "repos": {}}`·`state/.gitkeep`·`.gitignore`(`.local/`)·첫 커밋·`remote add origin`·`push -u`. `knowledge/`는 register가 첫 도메인을 만들 때 생김
- **register 질문 1라운드**: 도메인(기존 `domains` 목록 선택 또는 신규 `{조직}-{도메인}` + 한 줄 설명 — `^[a-z0-9]+-[a-z0-9-]+$` 검증), 기본 브랜치(`git symbolic-ref refs/remotes/origin/HEAD` 꼬리를 초안). 이미 등록된 레포면 도메인 이동·remote 추가 여부를 같은 라운드에 물음
- **register 기록**: `repos.{slug}` 3키, 신규 도메인이면 `domains.{d}: {}` + `knowledge/{d}/index.md` 골격, 기존 도메인이면 index.md `## 레포 구성`에 행 추가, `.local/paths.json` 갱신. 도메인 이동은 `git mv knowledge/{old}/{slug} knowledge/{new}/{slug}`(폴더가 있을 때, 승인 필수)와 양쪽 index.md 행 이동. slug 충돌 시 `{domain}-{name}` 제안(v1 규칙 유지)
- **register 마무리**: `catalog.py --check --root {WIKI_ROOT}/knowledge {index.md}` 에러 0 → `chore(register): {slug} → {domain}` 커밋 → `pull --rebase && push` → 상태 표 `| 레포 | 도메인 | 브랜치 | 커서 | 갱신일 | 로컬 경로 |` 출력
- **훅 안내**: 위키 없음 → `/llm-wiki:init`, 미등록 레포 → `/llm-wiki:register`, index.md 없음 → `/llm-wiki:register`
- **update 위치 판정**: 3장에서 사실마다 "이 레포를 지워도 참인가"를 한 번 물어 도메인 루트·레포 폴더를 가르고 둘 다 직접 편집. 대조 대상은 도메인 루트 목록(`--shallow`)·레포 목록·index.md 세 가지. `공통 후보` 행 삭제, inbox.md에는 `충돌`·`배치 내 상충`만
- **update 추출 묶음**: work.json의 `batches`마다 에이전트 1회(`model: sonnet`), 묶음 1개(머지 3건 이하 단일 묶음)면 메인이 직접. 프롬프트가 diff 파일 N개를 읽고 묶음 내 같은 주장을 사전 병합해 `{facts_dir}/{slug}/{batch_id}.json`에 `[{"fact","topic","code","quote","shas":["sha7",…]}]`로 Write
- **update index.md 보강**: 반영 에이전트가 신규 문서를 만들면 index.md `## 역인덱스`에 행을 추가하고, diff에서 레포 역할·접근 좌표(호스트·환경 이름)가 확정되면 `## 레포 구성`·`## 접근 좌표`를 `관찰` 출처로 보강 — index.md도 문서 1장으로 에이전트 1회
- **add**: 위치 판정 어휘를 도메인 루트·레포 폴더로, 미등록 안내를 register로, 인박스를 inbox.md로, 신규 문서 생성 시 역인덱스 행 추가
- **audit**: 인자 `--scope {domain}|{domain}/{slug}`(기본 현재 도메인 루트 + 현재 레포), 도메인 루트 목록은 `--shallow`, 진단 표에 index.md 템플릿 이탈 신호 추가, index.md는 참조 신호 면제, 인박스 inbox.md

### D5. 훅 (session_start.sh)

- **stdin**: `INPUT="$(cat 2>/dev/null || true)"` → python3 한 줄로 `source` 추출(실패·빈 입력은 `startup`). 공식 문서상 값은 `startup`·`resume`·`clear`·`compact`·`fork` 5종이며 pull 게이트는 `startup`·`resume`에서만 열고(`fork`는 부모 세션이 이미 당김), 목록 주입은 전 이벤트. hooks.json matcher는 이 `source`로 매칭되므로 matcher 없음을 유지해 전 이벤트 실행
- **주기**: `SYNC_SECONDS=$(( ${LLM_WIKI_SYNC_MINUTES:-10} * 60 ))` — 정수가 아니면 600. FETCH_HEAD mtime 비교와 0.5초×6 폴링(3초 상한)은 유지
- **위키 판정**: `[ -f "$WIKI/registry.json" ]` — 문구 `LLM-WIKI: 위키가 $WIKI 에 없음 — /llm-wiki:init 으로 clone 하거나 새로 만들 것`
- **블록 순서**: 규약 → 헤더 → index.md 본문 → 도메인 루트 목록(`도메인 {d}`) → 레포 목록(`레포 {slug}`) → 꼬리(`# 다른 도메인 N개: a · b — 목록은 주입하지 않음`)
- **헤더**: 동기화 메모 · `# 위키 — 도메인 {d} · 레포 {slug} · 형제: repo-b 3건 · repo-c 0건`(형제 = 같은 domain의 다른 등록 slug, 건수 = `len(catalog.docs(knowledge/{d}/{sib}))`, 폴더 없으면 0건) · `# {d}/index.md 없음 — /llm-wiki:register` · `# 확인 필요 N건 — inbox.md, /llm-wiki:add 로 처리` · 커서 지연 줄(v1 유지). 미등록 git 레포는 `# 미등록 레포 {slug} — /llm-wiki:register 로 등록하면 도메인 목록이 함께 주입됨`만, 비git은 규약 + 다른 도메인 이름
- **접기**: 하드 12,000 초과 시 목록 2개 중 큰 것부터 `# {라벨} N건 — python3 "{catalog_py}" --root "{root}" [--shallow] 로 전체 보기`로 접고, 그래도 넘치면 index 본문을 한 줄로 접음. 소프트 8,000 경고 유지
- **paths.json 기록**: 유지(등록 레포에서 세션을 열면 경로 갱신) — update.py가 이 파일만 보므로 register만으로는 다른 머신 경로가 잡히지 않음

### D6. update.py 묶음

- **pending**: 추출 루프 뒤 `rows`를 순서대로 묶음 — 현재 묶음이 `--batch-merges`(기본 5)건이거나, 비어 있지 않은데 바이트 합계 + 이번 diff 파일 크기가 `--batch-bytes`(기본 500,000)를 넘으면 새 묶음. diff 파일 크기는 `extract_diff`가 쓴 파일의 실제 바이트(`row["bytes"]`)
- **work.json**: `repos.{slug}` = `{domain, path, branch, ref, head, cursor, bootstrapped, commits[{sha, parents, date, subject, files_changed, truncated, bytes, diff_path}], batches[{id: "b01", shas: [sha7…], bytes}], remaining, notes}`. 표준 출력 요약에 `묶음 N개` 추가
- **advance**: 인자 `slug sha`만, 파일 `{cursor, at}`
- **문구**: 미등록 안내 `/llm-wiki:register`, `SKIP_NO_PATH` 유지

### D7. 규약·가이드 어휘

- **doc-contract.md**: 2장 범위 낱말 → "도메인 루트 문서가 일부 레포에서만 참이면 `## 적용 대상`에 레포를 밝힘, 레포 문서는 폴더가 레포를 말하므로 description에 레포명을 넣지 않음". 3장 위치 판정 한 단계·폴더 2층 고정·index.md 예약. 6장 `공통 우선` → `도메인 루트 우선`(도메인 루트가 정한 값·목록은 레포 문서에 복제하지 않음), 참조 금지에 index.md 면제. 7장 grep 경로 `{WIKI_ROOT}/knowledge/{domain}`, 충돌 → inbox.md. 8장 커밋 `docs({domain}): {도메인 루트 기준 상대경로} {요약}`. 9장 index.md 신설(D3)
- **agent-guide.md**: "공통 + 현재 프로젝트" → "index.md 본문 + 도메인 루트 + 현재 레포", 범위 순서 "같은 주제가 도메인 루트와 레포 폴더에 있으면 도메인 루트를 먼저", 직접 수정 금지 줄에 register 추가, index.md는 도메인 지도로 먼저 읽음. "걸리는 문서가 없으면 열지 않음"은 유지(검색 보강 보류)
- **README.md**: 스킬 표 5행, 동작 방식(주입 범위·pull 600초·`LLM_WIKI_SYNC_MINUTES`·startup·resume 한정), 위키 구조 트리·registry 예시(D1·D2), `inbox.md` 설명 "무인 갱신이 판정 못 한 충돌, add가 소비", 무인 갱신 범위(묶음·도메인 루트 직접 보강), 미이전 기능의 추후 후보에서 "프로젝트 하위 레포 층" 삭제 및 보류 4건(다중 위키·always 도메인·레포 다중 도메인·keywords 검색 보강) 추가
- **버전**: `plugin.json` 1.0.0 → 2.0.0(폴더·registry 스키마 비호환), description "스킬 5종(init·register·update·add·audit)". `marketplace.json` 2.3.0 → 2.4.0, llm-wiki description 갱신. 루트 README 표 행 갱신

### D8. 사다리 판정

| 단위 | 단 | 근거 |
|---|---|---|
| LOCATION_RE·registry 대조·index 필수 검사·shallow | ⑥ catalog.py 기존 함수 확장 약 40줄 | 새 모듈 없음, `check_location`·`docs`·`check` 조건 추가 |
| index.md 본문 추출 | ② `body_lines()` 재사용 | 훅이 `"\n".join(catalog.body_lines(path))` |
| 묶음 경계 | ⑦ update.py 함수 1개 약 20줄 | diff 실제 바이트는 파일을 쓴 뒤에만 알 수 있고 스킬이 묶으면 실행마다 경계가 달라짐 |
| stdin source·주기 env | ⑥ bash 4줄 | |
| 상태 표 | ① 코드 없음 | register 스킬이 JSON 3개를 Read해 표를 냄 |
| index.md 토큰 상한 | ① 없음 | 템플릿 절 고정으로 대체(D3) |
| keywords | ① 보류 | 사용자 결정 |

## 작업 순서와 커밋 분해

각 커밋은 `python3 llm-wiki/scripts/catalog.py --check --root $FX/wiki/knowledge` 에러 0(의도한 에러 픽스처 제외)과 아래 V표로 닫는다. 규약과 검사가 어긋난 상태로 커밋하지 않는다.

| # | 커밋 | 파일 | 검증 |
|---|---|---|---|
| 0 | `docs: llm-wiki 리뷰 반영 계획 개정` | `.ai-docs/workspace/feat-llm-wiki/plan.md`(이 문서로 교체), `feedback.md` append(아래 항목) | 파일 존재 |
| 1 | `feat(llm-wiki): 도메인 2층 구조·registry/state 축소·inbox.md` | catalog.py(LOCATION_RE·registry 대조·shallow·`--shallow`·resolve_repo domain), update.py(domain·advance 2키·status 삭제·문구), doc-contract.md(2·3·6·7·8장), agent-guide.md 어휘, session_start.sh 최소 적응(registry.json 판정·domains·inbox.md·도메인 루트+레포 목록·register 안내), update/add/audit SKILL 어휘(inbox.md·도메인 루트·레포 폴더·`docs({domain})`), README 위키 구조·registry 예시 | V1~V5 |
| 2 | `feat(llm-wiki): init·register 분리·index.md` | skills/init/SKILL.md 재작성, skills/register/SKILL.md 신설, catalog.py(index 필수·예약 위치 검사·목록 제외), doc-contract.md 9장, session_start.sh(index 본문 주입·index 없음 안내·접기 순서), audit SKILL index 신호, add SKILL 역인덱스 행, README 스킬 표 | V6~V8 |
| 3 | `feat(llm-wiki): 훅 주입 범위·pull 주기` | session_start.sh(형제 건수·다른 도메인 이름·stdin source·600초·`LLM_WIKI_SYNC_MINUTES`), hooks.json 변경 없음 확인, README 동작 방식 | V9~V11 |
| 4 | `feat(llm-wiki): update 묶음 fan-out·도메인 루트 직접 보강` | update.py(batches·`--batch-merges`·`--batch-bytes`·bytes), skills/update/SKILL.md(2·3·4·5장 재작성), README 무인 갱신 범위 | V12~V14 |
| 5 | `feat: llm-wiki 2.0.0·marketplace 2.4.0·README` | plugin.json, marketplace.json, 루트 README, llm-wiki README 최종 대조, feedback.md 보충 | V15~V16 |

커밋 1의 훅 적응은 "삭제된 경로(common·projects)와 개명 파일을 참조하지 않는 최소"이며 형제 건수·source·주기는 커밋 3에서 한다. 커밋 순서상 커밋 1~2 사이에 훅이 index.md를 주입하지 않는 상태는 허용된다(문서가 없어 실사용 영향 없음).

## feedback.md 추가 항목 (커밋 0)

- `context` 개정 의도 — 사용자 원문 "결정 자체는 다시 묻지 말고, 결정이 코드·규약에 어떻게 내려가는지만 계획한다" + 결정 1~8 요지, source: 사용자 확인 2026-09-14
- `correction` v1의 "프로젝트 폴더는 평면이며 repos/{slug}/ 하위 층을 두지 않음(업그레이드 조건: 레포 종속 문서 30건 초과)"은 폐기 — llm-wiki 구조는 `knowledge/{조직}-{도메인}/`(도메인 루트) + `{레포 slug}/` 2층 고정이고 위치 판정은 "이 레포를 지워도 참인가" 한 단계이며 회사 전체 공통 폴더는 두지 않음
- `context` 보류 — 다중 위키, 조직·도메인 무관 사실의 자리(always 도메인), 레포 다중 도메인, frontmatter keywords·grep 1회 규칙(검색 보강)은 사용 후 재검토. 사용자 원문 "일단 프론트메터 키워드 추가 계획은 제외 검색 보강은 이후 좀 사용해보고 다시"
- `why` index.md에 토큰 상한을 두지 않고 절 5개 고정 템플릿(레포 구성·의존 방향·역인덱스·접근 좌표·제외 레포)으로 크기를 다루는 이유 — 사용자 원문 "인덱스 상한은 둬도 의미가 없을 듯 큰 회사 도메인인 경우 그럼 누락될 가능성이 있으니…"; 대안(--check 상한 1,500토큰)은 대형 도메인에서 레포 행 누락으로 작동해 기각. 원형 system-repository-map.md는 약 9,200토큰이나 사실 불릿·제외 표를 빼면 약 5,500토큰이고 도메인 분할 시 도메인당 2,000~2,500토큰
- `constraint` index.md 역인덱스·의존 방향은 다른 도메인 레포를 `{domain}/{slug}`로 적을 수 있음 — 회사 전체 공통 폴더가 없어 도메인을 나누면 도메인 간 파급(예: 로그인이 devcenter-api와 dcsapp-gateway에 걸침)을 적을 자리가 이 면제 외에는 없음
- `why` 추출 묶음 경계를 update.py pending이 work.json `batches`로 내는 이유 — diff 실제 바이트는 파일을 쓴 뒤에만 알 수 있고 스킬이 묶으면 실행마다 경계가 달라짐. evidence: llm-wiki/scripts/update.py
- `why` registry.json `domains` 값을 빈 객체로 두는 이유 — 설명은 index.md로 갔고 보류 항목(always 도메인)의 키 자리를 배열로는 남길 수 없음

## 검증

픽스처 `$FX`는 스크래치패드에 만들고 커밋하지 않는다.

```
$FX/wiki (git init)
  registry.json: domains {onestore-demo:{}, personal-side:{}}, repos {repo-a:{domain:onestore-demo, remotes:[github.com/x/repo-a], branch:main}, repo-b:{domain:onestore-demo, …}, side-app:{domain:personal-side, …}}
  knowledge/onestore-demo/index.md         템플릿 골격(레포 구성 2행)
  knowledge/onestore-demo/a.md             정상, verified 오늘
  knowledge/onestore-demo/adr/0001-x.md    정상
  knowledge/onestore-demo/repo-a/b.md      verified: 2025-01-01 (낡음)
  knowledge/onestore-demo/repo-a/adr/0001-y.md
  knowledge/onestore-demo/repo-b/c.md      정상
  knowledge/personal-side/index.md
  (에러 픽스처, V2·V7에서만 추가) knowledge/common/z.md · knowledge/onestore-demo/repo-z/d.md · knowledge/onestore-demo/repo-a/index.md · knowledge/personal-side/index.md 삭제
$FX/repo-a, $FX/repo-b, $FX/side-app (git init, 커밋 2개, repo-a는 머지 7개 + 500KB 파일 커밋 1개)
$FX/wiki/.local/paths.json: 세 경로
```

| # | 커밋 | 명령 | 기대 |
|---|---|---|---|
| V1 | 1 | `catalog.py --root $FX/wiki/knowledge/onestore-demo --shallow --label 도메인` | `# 도메인 2건`(a·adr/0001-x, index.md·레포 폴더 제외), exit 0 |
| V2 | 1 | 에러 픽스처 3종 추가 후 `catalog.py --check --root $FX/wiki/knowledge` | `common/z.md 위치가 규약에 없음`, `repo-z/d.md 레포 폴더 repo-z가 registry.json에 없거나 도메인이 다름`, exit 1 → 제거 후 에러 0·exit 0 |
| V3 | 1 | `update.py pending --wiki $FX/wiki --out $FX/out` → work.json | `repos.repo-a.domain == "onestore-demo"`, `project` 키 없음 |
| V4 | 1 | `update.py advance repo-a $(git -C $FX/repo-a rev-parse HEAD) --wiki $FX/wiki`; `cat state/repo-a.json` | 키 `cursor`·`at` 2개만, `update.py status` → argparse 에러 |
| V5 | 1 | 훅 실행(`LLM_WIKI_ROOT=$FX/wiki CLAUDE_PLUGIN_ROOT=$PWD/llm-wiki CLAUDE_PROJECT_DIR=$FX/repo-a`, stdin `{"source":"startup"}`) | 헤더 `도메인 onestore-demo · 레포 repo-a`, 블록 `# 도메인 onestore-demo 2건`·`# 레포 repo-a 2건`(`b!`), `common` 문자열 없음; `rm registry.json` 후 실행 → 위키 없음 안내 JSON |
| V6 | 2 | `personal-side/index.md` 삭제 후 `--check`; `repo-a/index.md` 추가 후 `--check` | `personal-side/index.md 없음 — /llm-wiki:register가 생성`, `index.md는 도메인 루트에만`, 원복 후 에러 0 |
| V7 | 2 | V5 훅 실행; index.md에 `## 배포 순서` 절과 사실 불릿을 넣은 사본으로 audit 진단 프롬프트 문구 확인 | 규약 다음 블록이 `# 도메인 onestore-demo index.md · 약 N토큰` + 본문(`## 레포 구성`·`## 역인덱스` 표 포함), 목록 행에 `index` 없음; audit SKILL 진단 표에 index.md 템플릿 이탈 → `이동` 행 존재 |
| V8 | 2 | `grep -c 'llm-wiki:register' llm-wiki/hooks/session_start.sh llm-wiki/skills/*/SKILL.md llm-wiki/scripts/update.py`; `skills/register/SKILL.md` frontmatter | 훅·init·add·update.py에 register 안내 존재, register description이 마켓 관례 공식(`Use when … ("트리거") — 동작. NOT for …`) |
| V9 | 3 | 훅에 `.local/paths.json`·registry 그대로, `CLAUDE_PROJECT_DIR=$FX/repo-a` | 헤더 `형제: repo-b 1건`, 꼬리 `# 다른 도메인 1개: personal-side` |
| V10 | 3 | `$FX/wiki`에 원격(bare) 연결 후 FETCH_HEAD mtime 20분 전으로 `touch -t`; stdin `{"source":"compact"}` 실행 → mtime 불변, `{"source":"startup"}` 실행 → mtime 갱신; `LLM_WIKI_SYNC_MINUTES=60`로 startup 실행 → 불변 | pull 게이트가 source·주기를 따름 |
| V11 | 3 | 문서 60건을 repo-a 폴더에 생성 후 훅 실행 | 하드 초과 시 레포 목록이 `--root … 로 전체 보기` 한 줄로 접히고 index 본문은 유지 |
| V12 | 4 | repo-a 커서를 첫 커밋으로 두고 `pending --out $FX/out` | `batches` 2개 이상(5건 경계), 500KB 파일 머지가 단독 묶음, `commits[].bytes` 존재, 표준 출력 `묶음 N개` |
| V13 | 4 | `pending --batch-merges 2` | 묶음 크기 2 이하 |
| V14 | 4 | `grep -n '공통 후보\|review.md\|projects/' llm-wiki -r` | 0줄 |
| V15 | 5 | `claude plugin validate .`; marketplace version·plugins 이름 출력; `python3 -c 'import json;print(json.load(open("llm-wiki/.claude-plugin/plugin.json"))["version"])'` | 통과, `2.4.0`, `2.0.0` |
| V16 | 5 | `grep -rniE 'bitbucket|onestorecorp|devcenter|confluence|jira|1000377|CMS_APP|PD[0-9]{6}' llm-wiki/ --exclude=README.md`; `find llm-wiki -name '__pycache__'` | 0줄(README 예시 도메인 `onestore-devcenter`는 사용자 지정 예시라 허용) |
| V17 | 머지 후 | `/plugin marketplace update` → 새 세션 `/llm-wiki:init`(빈 원격) → `/llm-wiki:register`(신규 도메인) → 세션 재시작 → `/llm-wiki:update` | 골격 커밋·index.md 생성·세션에 index 본문과 목록 주입·묶음 추출 후 커서 전진 |

## 범위 밖

- **기존 문서 이관**: 실사용 문서 없음 — 대상 없음
- **보류 4건**: 다중 위키, always 도메인, 레포 다중 도메인, 검색 보강(keywords·grep 1회 규칙)
- **`llm-wiki-structure.html`**: 리뷰 세션 산출물(미추적) — 이 계획의 커밋에 담지 않으며 처리는 사용자 판단

## 핸드오프

- **승인 시**: `.ai-docs/workspace/feat-llm-wiki/plan.md`를 이 계획 전문으로 교체하고 `feedback.md`에 위 6항목을 append해 커밋 0으로 남긴 뒤 정지
- **구현**: 새 세션에서 `/plan-workflow:execute`로 커밋 1~5를 순서대로, 각 커밋의 V표를 통과한 뒤 커밋
