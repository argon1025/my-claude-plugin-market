# devcenter-wiki 최소 이전 → `llm-wiki` 플러그인 추가 계획

## 의도

- **왜**: 사내 `devcenter-wiki`는 팀 위키·Bitbucket PR 게이트·무인 파이프라인에 묶여 개인 레포에서 못 쓰고, 규약 690줄과 스킬 9종의 프롬프트 과부하가 크다
- **누가·언제**: 사용자 본인이 서로 무관한 여러 사이드 프로젝트를 오가며 개발할 때, 세션마다 코드에 없는 지식(정책·결정 근거·외부 계약·함정)을 다시 설명하는 비용을 겪는다
- **완료 조건**: 개인 마켓에 최소 기능(위키 초기화·세션 주입·무인 갱신·정리)만 가진 플러그인이 설치되어 동작하고, 프롬프트가 better-communication 문체로 재작성되며, 제외 기능이 기록된다

사용자 확인 원문: "맞음" (2026-09-14, 의도 3문장 복창에 대한 답)

## 사용자가 확인한 결정 (원문)

| 축 | 결정 | 사용자 답 원문 |
|---|---|---|
| 스킬 집합 | `init`·`update`·`add`·`audit` 4종 | "init·update·add·audit 4종 (Recommended)" |
| 기존 사내 문서 이관 | 이번 범위 밖 | "이번 범위 밖 (Recommended)" |
| 다중 머신 | 여러 머신, 원격 필수 | "여러 머신, 원격 필수" |
| 폴더 층 | 2층 `common/` + `projects/{p}/` | "2층: common + projects/{p} (Recommended)" |
| 훅 동기화 | 훅이 자동 pull, 팀원 공유 가능, 지식 베이스는 플러그인 레포 밖 별도 저장소 | "훅이 자동 관리, 여러 사용자(팀원) 가 공유해도 가능하도록.. 그리고 기존과 달리 지식 베이스는 플러그인 레포 내가 아니라 별도 레포지토리에서 관리되도록 구성" |
| 이름·경로 | `llm-wiki`, 기본 `~/.ai-docs/wiki`, env `LLM_WIKI_ROOT` | "llm-wiki + ~/.ai-docs/wiki (Recommended)" |
| 매 턴 리마인더 | UserPromptSubmit 훅 제외 | "제외 (Recommended)" |
| 주 사용 경로 | 무인 갱신 → 정리, 대화형 반영은 부차 | "주로 harvest 스킬보다는, 무인 업데이트 스킬인 auto-* 스킬들을 주로 이용하는편임 이후 문서정리 스킬 사용" |
| 다중 프로젝트 | 서로 무관한 사이드 프로젝트 다수, 유지보수 용이성이 핵심 | "특정 도메인에 한정되지 않고 다양한 사이드 프로젝트에 대한 문서들도 관리될 수 있을듯함.. 이를 어떻게 풀어나갈지, 쉽게 유지보수 가능한 설계가될지가 핵심" |

## 탐색·검증 결과 요약

- **원본 규모**: 9,604줄 — 스킬 9종, 규약 4편 690줄(장·절 번호 앵커 100회 이상 상호 참조), 파이썬 7종(catalog.py 1,002줄), 훅 3종, 테스트 2,894줄. `add-material` 실행 시 실제 로드 612줄
- **사내 결합**: `gate.sh`가 origin URL `bitbucket.onestorecorp.com`으로 그룹 스페이스를 켬, 반영 게이트는 Bitbucket MCP PR, Confluence·Jira 좌표가 규약·스킬에 산재
- **로컬 위키 가설 검증**(onestore-devcenter-front 128문서 2,971주장): 67%는 코드 grep 1~2회로 복원 가능, 33%(ADR 기각 대안 58불릿·코드에 흔적 없는 외부 계약·자기 불확실성 표기·비강제 컨벤션·반파리티 경고)는 코드로 대체 불가. 최근 17커밋 미수확으로 6건 불일치, `verified` 최신인데 전체 낡은 문서 1건 — 날짜만으로는 낡음 감지 실패
- **개인용 함의**: 팀 위키에 못 올리던 사유(시크릿·개인 경로·기한부 리스크)가 1인·소규모 공유 위키에서는 소멸하므로 레포 로컬 위키 없이 글로벌 단일 저장소가 성립. 단 레포 종속 사실의 자리와 커밋 기반 낡음 신호는 필요
- **폴더 분포**: 그룹 policy 122/172, 레포 policy 93/128 — 모양 폴더 5종은 정보량이 낮음
- **원본 무인 경로**: auto-collect(추출 → `facts/` 원자재) → auto-publish(판정 → PR)의 2단계는 PR 게이트와 재소비를 위한 구조. PR 게이트가 없으면 한 실행·한 커서·직접 편집으로 접힘
- **개인 마켓 관례**: `{name}/.claude-plugin/plugin.json`(version 1.0.0), `hooks/hooks.json`(matcher 없음), python3 히어독 JSON 출력, `rules/agent-guide.md` 상시 주입, SKILL description 공식 `Use when ... ("트리거") — 동작. NOT for ... (that is /x:y's job).`, 본문 `## N. 명사구` + `**라벨**: 명사형 종결`. `marketplace.json` minor bump, 루트 README 설치 한 줄 + 표 한 행, 브랜치 `feat/{name}` → squash 머지, 제목 `feat: {원본} 최소 이전 {신규명} 추가 v{버전}`. `.claude/settings.local.json`은 전역 gitignore로 커밋 대상 아님

## 설계 결정

### D1. 저장 구조 — 별도 git 저장소, 2층 + `adr/`

```
~/.ai-docs/wiki/                    # LLM_WIKI_ROOT. 별도 git 저장소(원격 필수), 플러그인 레포와 무관
├── registry.json                   # 사람·init이 편집: 프로젝트와 레포 등록
├── state/{slug}.json               # update만 편집: 레포별 커서 (레포별 파일 → 팀원·머신 간 충돌 최소)
├── review.md                       # update가 append하는 확인 필요 인박스, add·audit이 소비
├── .gitignore                      # .local/
├── .local/paths.json               # 머신별 slug → 로컬 절대경로 (훅이 방문 시 기록, 미추적)
└── knowledge/
    ├── common/                     # 전 프로젝트 공통 — 라이브러리 함정·설계 원칙·개인 컨벤션
    │   ├── adr/                    # 선택
    │   └── *.md
    └── projects/{project}/         # 프로젝트 = 레포 1~N개의 도메인 묶음. 프로젝트 공통 + 레포 종속 문서 평면
        ├── adr/                    # 선택
        └── *.md
```

- **폴더**: 각 스페이스(`common`, `projects/{p}`)는 평면 + `adr/`만 허용. policy/process/domain/external 폴더 폐지 — 원본 분포가 policy에 71~73% 몰려 정보량이 없고, 골격(적용 대상·규칙·예외 등)은 규약의 권장 골격으로만 유지. 기존 문서 이관이 범위 밖이라 호환 부담 없음
- **레포 종속 문서**: 프로젝트 폴더 평면에 두고 `description`에 레포명을 넣어 구별. 프로젝트가 커지면 `repos/{slug}/` 하위를 추가할 수 있도록 카탈로그·검사는 스페이스 루트 기준 상대 경로만 다룸(의도적 단순화, 업그레이드 조건: 한 프로젝트의 레포 종속 문서가 30건을 넘을 때)
- **경로 검사 정규식**: `^(common|projects/[a-z0-9-]+)(/adr)?/[a-z0-9-]+\.md$`
- **위치 판정(재작성 테스트 2단)**: 이 프로젝트를 통째로 지워도 참이면 `common/`, 아니면 `projects/{p}/`. 둘 이상 프로젝트가 함께 지키는 계약은 `common/`에 두고 `## 적용 대상`에 프로젝트 명시

### D2. 레지스트리·커서·로컬 경로

`registry.json` (추적, 사람·`init`이 편집):

```json
{
  "projects": {
    "trendlog": {"summary": "개인 사이드 — 트렌드 로그 서비스"}
  },
  "repos": {
    "trendlog-backend": {
      "project": "trendlog",
      "remotes": ["github.com/argon1025/trendlog-backend"],
      "branch": "main",
      "stack": "NestJS 11",
      "summary": "트렌드 수집·집계 API"
    }
  }
}
```

`state/{slug}.json` (추적, `update`만 편집):

```json
{"cursor": "3f2c1a9e…40자", "branch": "main", "at": "2026-09-14", "merges": 3, "docs": 2}
```

`.local/paths.json` (미추적, 훅이 편집): `{"trendlog-backend": "/Users/.../trendlog-backend"}`

- **분리 근거**: 사람 편집 파일과 기계 커서를 한 파일에 두면 무인 커밋이 매번 사람 표를 건드리고, 팀원·다중 머신이 다른 레포를 갱신할 때 같은 파일에서 충돌함. 레포별 커서 파일은 서로 다른 레포 갱신이 충돌 없이 머지됨
- **slug 규칙**: origin(없으면 upstream) URL의 마지막 경로 요소에서 `.git` 제거·소문자·`[^a-z0-9-]`→`-`. remote 없으면 `git rev-parse --path-format=absolute --git-common-dir` 부모 디렉터리명(Orca 워크트리도 본 저장소와 같은 slug, 실측 확인). 등록 매칭은 정규화 remote(scheme·`user@`·`.git` 제거, 소문자)가 `remotes` 배열 중 하나와 일치 → slug 폴백. owner를 slug에 넣지 않음(포크 `~1000377/x`와 팀 `cms/x`가 갈라짐), 동명 충돌은 `init`이 `{project}-{name}` 제안
- **무인 대상 조건**: `.local/paths.json`에 경로가 있는 레포만 처리, 없으면 건너뛰고 사유 보고(클론·미러 팜 없음 — 의도적 단순화)

### D3. 세션 주입 스코프·낡음 신호

- **주입 순서**: `rules/agent-guide.md` → 헤더(동기화 시각·slug·프로젝트·형제 레포 summary 한 줄씩·`review.md` 미처리 건수·커서 지연 줄) → `common/` 카탈로그 전수 → 현재 프로젝트 카탈로그 전수. 다른 프로젝트는 "다른 프로젝트 N개: a · b" 한 줄만
- **카탈로그 행**: `{스페이스 루트 상대 경로}{!} — {description}`, 머리 `# {라벨} N건 · 약 T토큰`, `!` = `verified` 180일 초과(단일 상수 `STALE_DAYS=180`)
- **커서 지연**: 등록 레포면 `git rev-list --count {cursor}..HEAD` 1회로 `# 커서 {sha7} · HEAD보다 N커밋 뒤 — /llm-wiki:update 권장` 한 줄. 커서 없음이면 "첫 update가 등록". 문서별 `anchor`·`watch` 드리프트는 v1 미도입(의도적 단순화, 업그레이드 조건: 커서 최신인데 낡은 문서가 관측될 때)
- **예산**: 소프트 8,000토큰 초과 시 헤더에 경고 한 줄(audit 권고), 하드 12,000 초과 시 가장 큰 스페이스 행을 `# {라벨} N건 — catalog.py --root {경로}로 전체 보기` 한 줄로 대체. 행을 조용히 빼지 않음
- **미등록 git 레포**: `common/` + "미등록 레포 `{slug}` — /llm-wiki:init" 한 줄. **비git**: `common/`만. **위키 없음**: 안내 한 줄(`LLM_WIKI_ROOT` 경로와 `/llm-wiki:init` 포함) 후 exit 0
- **동기화**: 원격이 있고 `.git/FETCH_HEAD`가 60분 이상 오래되면 백그라운드 `git pull --ff-only` 최대 3초 대기(원본 로직 축약, macOS `timeout` 부재로 `kill -0` 폴링). 실패·지연은 헤더에 한 줄로 알리고 첫 응답에서 사용자에게 전달 지시. 자동 clone은 하지 않음(URL 상수 없음 — `init`이 clone)

### D4. 스킬 4종과 경계

| 스킬 | 역할 | 정지점 | 출처 종류 | 쓰는 곳 |
|---|---|---|---|---|
| `init` | 위키 clone 또는 `git init`, 프로젝트·레포 등록, `.local/paths.json` 기록 | 등록 문답 1회 | — | `registry.json`, 폴더 |
| `update` | 등록 레포 순회, 커서 이후 first-parent 머지 diff → 사실 추출 → 문서 반영 → 커서 전진 | 없음(완주) | `관찰` | `projects/{p}/`, `state/`, `review.md` |
| `add` | 사용자 자료·대화 확정 사실·`review.md` 행 반영 | 충돌 질문 1회 + 초안 승인 1회 | `확인` | `common/`, `projects/{p}/` |
| `audit` | 조각·중복·낡음·규약 위반 정리 | 승인 표 1회 | — | 전체 |

- **update/add 분리 근거**: 정지점(무인 0회 vs 질문이 본체), 입력(diff vs 자료), 권한(`관찰`은 보강만, `확인`은 교체 가능), 커서(update만 전진). 한 스킬 두 모드로 두면 원본 fact-verdict 3.1의 분기 복잡도가 재현됨
- **harvest 흡수**: `update --repo {slug}` 또는 `--range`로 지목 실행 가능, 갈래 질문이 필요한 행은 `review.md` → `add`
- **`update`의 `common/` 쓰기 금지**: 공통 판정 사실은 `review.md`에 `공통 후보`로 기재 — 무인 경로에서 위치 판정 한 단계 제거
- **`disable-model-invocation`**: `init`·`update`에 추가(원본 setup·auto-* 동일). `add`·`audit`은 트리거 기반

### D5. 규약 파일 구성과 로드량

| 파일 | 로드 | 목표 줄 | 담는 것 |
|---|---|---|---|
| `rules/agent-guide.md` | 매 세션 | 12 | 문서 우선·여는 기준·범위 순서·낡음·모순 보고·직접 수정 금지·레지스트리 불변 |
| `references/doc-contract.md` | 스킬 실행 시 | 약 65 | 담는 것·문서 단위·위치와 이름·문서 모양·문체·겹치는 사실·사실 판정·반영 |
| `skills/*/SKILL.md` | 호출 시 | init 25 · add 45 · update 80 · audit 55 | 순서·정지점·서브에이전트 프롬프트 |

- **fact-verdict 흡수**: 근거 층위 3층 → 종류 2종(`확인`·`관찰`), 판정 4종 → 3종(`동일`·`보강`·`충돌`), 게이트 표 8행 → 규칙 3개("새 사실 추가는 두 종류 모두, 기존 값 교체는 `확인`만, 충돌은 대화형이면 묻고 무인이면 `review.md`")
- **apply-change 대체**: PR·작업 클론·리뷰어·PR 본문 틀 전부 소거 → "`--check` 통과 후 문서마다 커밋, `--no-verify` 금지, 끝에 `pull --rebase` 후 push"
- **출처 줄**: `> 출처: {종류} — {식별자}, {날짜}` 1줄 형식, 종류 `확인`(자료명·판본 또는 `사용자 확인`)·`관찰`(`{slug} @{sha7} 머지`). 같은 레포의 `관찰` 줄은 최신 하나만 유지 → 병합 스크립트(sources.py) 불필요
- **로드량**: add 약 120줄(원본 612), update 약 160줄(원본 auto-collect+auto-publish+규약 3편 약 1,065)

### D6. 코드 최소 사다리 판정

| 단위 | 단 | 근거 |
|---|---|---|
| 카탈로그 생성·`--check` | ⑦ `scripts/catalog.py` 약 180줄 | 낡음 판정(날짜 차)·BOM/CP949/미닫힘 frontmatter 방어·JSON 출력이 bash 3.2/BSD date로 성립하지 않고, 훅과 스킬 3종이 같은 목록·검사를 호출 |
| 무인 범위·diff 추출·커서 | ⑦ `scripts/update.py` 약 140줄 | 레포 N개 순회·부트스트랩·`origin/{branch}` 선택·force-push 검사·400KB 절단·제외 pathspec·work.json 조립을 에이전트가 bash 5×N회로 하면 재현성이 무너짐. 원본 `collect.py`의 `list_first_parent`·`extract_diff` 범위 규칙·`EXCLUDE_PATHSPECS`·`baseline_before`만 이식 |
| slug 계산 | ⑥ bash 2줄 + python 5줄 | remote basename, 폴백 common-dir 부모 |
| 훅 pull | ⑥~⑦ 약 20줄 | 원본 로직 축약(60분 게이트·백그라운드·3초 폴링) |
| 위키 생성 | ④ git + 프롬프트 | `init` 스킬이 `git clone` 또는 `git init` |
| UserPromptSubmit·gate.sh | ① 없음 | 훅 1개, 게이트 공유 대상 없음 |
| sources.py·preserve.py·pick/ledger/assemble·`--review` | ① 제외 | 출처 병합은 규약으로 제거, 재구조화는 v2, 원장·샤드·PR은 게이트 전제 |
| 테스트 파일 | ① 제외 | 마켓 관례(테스트 없음), 원본 test_hooks는 동기화 축 전용. 픽스처 + 수동 검증 명령으로 대체 |

## 산출물 초안

아래 초안은 계획에 그대로 실리는 정본이며, 구현 시 문체 규약(라벨 2~8자·명사형 종결·단일 문장)과 대조해 다듬는다. `{PLUGIN_ROOT}`·`{WIKI_ROOT}`는 훅이 치환하는 자리표시자다.

### `rules/agent-guide.md`

```markdown
# 위키 규약 (세션 전체 적용)

`{WIKI_ROOT}`의 문서는 코드에 없는 사실의 정본입니다. 세션에 주입된 목록(공통 + 현재 프로젝트)에서 요청에 걸리는 문서를 골라 읽고 진행하며, 사용자가 세션에서 다르게 지시하면 그 지시가 우선합니다.

- **문서 우선**: 사전 지식과 문서가 어긋나면 문서를 믿음
- **여는 기준**: 목록의 `description`이 이번 요청의 작업과 맞는 문서는 코드를 읽기 전에 열고, 걸리는 문서가 없으면 열지 않음
- **범위 순서**: 같은 주제가 공통과 프로젝트 폴더에 둘 다 있으면 공통을 먼저 읽고 프로젝트 문서는 그 위에서 좁힌 부분만 읽음
- **낡음 표시**: 목록의 `!` 문서는 확인 기한이 지난 것이라 코드로 대조한 뒤 사용함
- **모순 보고**: 문서끼리 또는 문서와 코드가 어긋나면 임의로 고르지 않고 두 값을 병기해 사용자에게 알림
- **직접 수정 금지**: 위키는 스킬로만 고침 — 자료·대화에서 정한 사실은 `/llm-wiki:add`, 등록 레포의 머지 반영은 `/llm-wiki:update`, 조각·중복·낡음·규약 위반 정리는 `/llm-wiki:audit`, 저장소 생성·레포 등록은 `/llm-wiki:init`
- **기록 제안**: 대화에서 정책·결정·함정처럼 코드에 없는 사실이 확정되면 작업 끝에 `/llm-wiki:add`를 제안하며 임의로 기록하지 않음
- **커서 불변**: `state/`의 커서는 `update`만 전진시키며 손으로 고치지 않음
```

### `references/doc-contract.md` (절 제목 + 핵심 불릿)

```markdown
# 위키 문서 규약

문서 한 장의 규격과 사실 하나의 판정 기준입니다. 기계가 볼 항목(frontmatter 키·날짜 형식·`description` 길이·경로 규칙·파일명·첫 줄 제목·`description` 중복)은 `catalog.py --check`가 검사하며 에러 메시지가 정본이고, 아래는 사람과 에이전트가 판단할 것만 적습니다.

## 1. 담는 것
- **grep 테스트**: 불릿 하나가 코드 검색 한 번으로 참이 확인되면 담지 않음 — 판정 단위는 문서가 아니라 불릿
- **제외 판정선**: 한 심볼의 정의로 환원되는 것(타입·시그니처·enum·파일 위치·호출 관계), 식별자의 내부 동작 서술, 이번 변경의 서사("A에서 B로 바꿈")는 제외
- **담는 것**: 코드 밖 맥락(도메인 정책·외부 서비스 제약·계정·인프라), 트레이드오프가 있던 결정과 버린 대안, 금지와 함정, 코드에 없는 컨벤션, 반복 절차, 소비처가 이 레포 밖인 외부 계약, 개인 개발 환경의 도구·경로·함정(공통)
- **담지 않는 것**: 코드·다른 시스템에 원본이 있는 사실, 모델이 아는 일반 지식, 미확정 계획·할 일, 린터·CI가 이미 막는 규칙(도구 위치 한 줄과 우회·예외만), 비밀값
- **자료 필터**: 기획서·설명서의 화면 시안, UI 문구 원문, 일정·담당자, "검토 중" 미확정 항목 제외

## 2. 문서 단위와 description
- **트리거**: 요약이 아니라 "어떤 작업을 할 때 열어야 하는지" 한 문장 — 40자 목표·60자 상한, "때" 종결, 이 문서에서만 참인 낱말 1개 이상 (좋음: `상품 상태를 바꾸거나 상태별 노출 조건을 다룰 때`)
- **한 주제**: 40자 한 문장으로 전체가 덮이지 않으면 분할 — 범주어로 올려 여러 주제를 한 문장에 넣는 것 금지, 각 40줄 미만·같은 주제·항상 함께 읽히면 병합
- **범위 낱말**: 공통 문서는 어느 프로젝트에서 참인지 문장에 밝히고, 프로젝트 문서 중 한 레포에서만 참인 사실은 레포명을 넣음
- **역커버리지**: 제목·description이 약속한 범위를 본문이 덮지 못하면 제목과 description을 본문 범위로 좁히고 채울 사실 없는 절은 두지 않음

## 3. 위치와 이름
- **위치 판정**: 이 프로젝트를 통째로 지워도 참이면 `knowledge/common/`, 아니면 `knowledge/projects/{project}/` — 둘 이상 프로젝트가 함께 지키는 계약은 공통에 두고 `## 적용 대상`에 프로젝트 명시, 한 사실이 두 성격이면 둘로 나눔
- **폴더**: 스페이스 평면이 기본, `adr/`만 하위 폴더 — 되돌리기 어렵고 근거를 의심할 만하며 실제로 버린 대안이 있는 결정 셋을 모두 충족할 때만
- **파일명**: kebab-case 2~5단어 명사구, `adr/NNNN-slug.md`는 그 스페이스 최대 번호 +1

## 4. 문서 모양
- **frontmatter**: `description`·`updated`·`verified` 3키만, 날짜 `YYYY-MM-DD`, 본문 첫 줄 `# 제목`
- **updated·verified**: updated는 고친 날, verified는 현실과 맞는지 확인한 날 — 대조 없이 verified 갱신 금지
- **권장 골격**: 규칙 문서 `## 적용 대상`·`## 규칙`·`## 예외`, 절차 문서 `## 트리거`·`## 단계`·`## 분기와 실패`, 용어 문서 `## 용어`·`## 상태와 전이`·`## 코드값`, `adr/` `## 컨텍스트`·`## 결정`·`## Why`·`## Apply when` — 내용에 맞지 않으면 변경 가능(adr 제외)
- **절 응집**: 한 절은 제목이 답하는 질문의 사실만, 같은 주장 둘은 하나로 — 값이 다르면 통합하지 않고 충돌로 보고
- **출처 줄**: 본문 맨 아래 `> 출처: {종류} — {식별자}, {날짜}` — 종류는 `확인`(자료명·판본 또는 `사용자 확인`)과 `관찰`(`{slug} @{sha7} 머지`) 2종, 원본이 다르면 줄을 더하고 같은 레포의 `관찰` 줄은 최신 하나만
- **예시**: (frontmatter 3키 · `# 연체 시 대출 제한` · `## 적용 대상` 2불릿 · `## 규칙` 2불릿 · 출처 줄 1개 — 10줄)

## 5. 본문 문체
- **어미**: 음·함·됨·명사구 종결, 합니다체 금지 (`개발자 등급 변경 시 기존 약관 동의 무효화`)
- **불릿 단위**: 사실 하나 — 150자를 넘으면 둘 이상이거나 표 한 행
- **인과**: `규칙 — 근거` 꼬리, "~때문에 ~한다" 순서 금지
- **업무 낱말 우선**: 식별자는 업무 낱말 뒤 괄호 병기 `국외 이전 여부(isTransferCrossBorder)`, 식별자로 시작하는 불릿 금지, 코드 블록·따옴표 문구·표는 원형
- **모호 표현 금지**: 적절히·필요시·일부 경우는 조건과 수치로 교체, 미확정은 "아직 정해지지 않음"으로 명시

## 6. 겹치는 사실
- **참조 금지**: 다른 위키 문서 링크·이름 표기·`참고` 절 금지 — 목록이 매 세션 주입되어 참조가 탐색에 기여 없음
- **접점**: 다른 주제와 맞닿아 없으면 틀린 결론에 이르는 사실만 문서 이름 없이 한 문장, 값 목록·표는 소유 문서만
- **공통 우선**: 공통이 정한 값·목록은 프로젝트 문서에 복제하지 않음

## 7. 사실 판정
- **대조**: 사실마다 목록 `description` 전수와 `grep -ril '{핵심어}' {WIKI_ROOT}/knowledge/common {WIKI_ROOT}/knowledge/projects/{project}`로 대상 문서를 찾고, 값 단위로 `동일`(verified만 갱신)·`보강`(추가, updated 갱신)·`충돌`(값 다름 또는 기존 문장이 거짓) 중 하나로 판정
- **종류가 가르는 것**: 새 사실 추가는 두 종류 모두, 기존 값 교체는 `확인`만 — 코드는 "지금 도는 것"만 답하고 "그렇게 하기로 했는지"는 답하지 않음
- **충돌 처리**: 사용자가 있으면 기존 값·기존 출처·새 값·새 출처를 병기해 묻고 답이 정본, 없으면(무인) 편입하지 않고 `review.md`에 기재
- **병합 방식**: 기존 본문을 유지하고 해당 값만 고침 — 문서 전체 재작성·변경 서사 금지, 뜻이 달라지면 `description`도 다시 씀
- **되돌리기 어려운 편집**: 문서 삭제·분할·폴더 이동·`adr/` 신설은 사실 편입과 별개로 사용자 승인 필요

## 8. 반영
- **검사 후 커밋**: `catalog.py --check` 에러 0 상태에서 문서마다 `docs({space}): {파일명} {요약}` 커밋, `--no-verify` 금지
- **동기화**: 스킬 시작에 `git pull --ff-only`, 끝에 `git pull --rebase && git push` — 충돌은 멈추고 보고
- **입력 밖 금지**: 확정된 입력(자료·대화·diff) 밖의 사실을 사전 지식으로 채우지 않음
```

### `skills/init/SKILL.md` (절 구성)

- **frontmatter**: `name: init`, `disable-model-invocation: true`, description: `Use when the wiki repo is not present on this machine or the current repo is not registered ("위키 초기화", "위키 세팅", "이 레포 위키에 등록") — clones the shared wiki into {WIKI_ROOT} (or git-inits a new one and asks for the remote), registers the project and the current repo in registry.json, records the local path, prints the catalog. NOT for writing facts (that is /llm-wiki:add and /llm-wiki:update's job).`
- **1. 저장소**: `{WIKI_ROOT}` 부재 시 원격 URL을 묻고 `git clone`, 새로 만들 때는 `git init` + `knowledge/common/` + `registry.json` + `.gitignore(.local/)` + 첫 커밋 + 원격 등록(URL 제공 시 push). 있으면 `pull --ff-only`
- **2. 레포 등록**: 현재 디렉터리가 git 레포이고 미등록이면 AskUserQuestion 1회(프로젝트 선택 또는 신규·기본 브랜치·한 줄 summary — stack은 `package.json`/`pom.xml`/`build.gradle`에서 초안), `registry.json` 갱신, `knowledge/projects/{p}/` 생성(`.gitkeep` 없음, 첫 문서 생길 때), `.local/paths.json`에 경로 기록, 커서는 만들지 않음(첫 `update`가 HEAD로 부트스트랩, `--baseline-days N`으로 소급 가능)
- **3. 커밋·보고**: `registry.json` 커밋·push, 목록 출력, "다음 세션부터 자동 주입" 안내

### `skills/add/SKILL.md`

```markdown
---
name: add
description: Use when material the user hands over or a decision settled in conversation must become wiki facts — a pasted spec, a read file, a fetched page, "we agreed X", or rows left in review.md ("위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘", "확인 필요 처리") — extracts durable facts, routes each to common or the project folder, checks against existing docs, asks once on every conflict and treats the answer as canonical, lands them as 확인-tier facts with one commit per doc. NOT for merged code (that is /llm-wiki:update's job) and NOT for sweeping existing docs (that is /llm-wiki:audit's job).
---

사용자가 건넨 자료와 대화에서 확정된 사실을 위키에 반영합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`를 먼저 읽고 따르며, 이 스킬은 순서와 정지점만 정합니다.

## 1. 입력 확정

- **입력 집합**: 붙여넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 직접 정한 문장, `review.md`의 미처리 행 — 이 밖의 사실 기록 금지
- **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
- **큰 자료**: 한 세션에 못 담으면 장 단위로 나눠 실행하고 사실을 요약으로 줄이지 않음
- **저장소 상태**: `{WIKI_ROOT}`가 없거나 현재 레포가 미등록이면 `/llm-wiki:init` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only`

## 2. 사실 추출

- **번호 목록**: 오래 남을 사실을 번호를 매겨 나열하고 각 사실에 원문 위치(장·절·페이지)를 붙임
- **제외 적용**: 규약 1장의 grep 테스트·제외 판정선·자료 필터를 사실마다 적용
- **구조 분리**: 원문의 절 구조를 문서 구조로 옮기지 않고 규약 2장의 한 주제 기준으로 문서 수를 정함 — 대개 원문 하나가 문서 여럿
- **원문 내부 충돌**: 같은 주제에 두 값이 있으면 개정 표기로 가리고, 갈리지 않으면 4장 질문에 올림 — 뒤쪽이 최신이라 가정하지 않음

## 3. 위치와 대조

- **위치**: 규약 3장의 위치 판정으로 공통과 프로젝트 폴더를 가름 — 기본은 현재 프로젝트
- **대조**: 주입된 목록의 `description` 전수와 grep으로 대상 문서를 찾고 사실마다 동일·보강·충돌을 판정
- **기존 문서 우선**: 덮는 문서가 있으면 신규 생성 대신 그 문서 수정

## 4. 질문 — 정지점 하나

- **묻는 것**: 충돌 행(기존 값·기존 출처·새 값·새 출처 병기, 코드로 확인 가능한 값은 현재 값을 `관찰` 열에 첨부), 원문 내부 미결 충돌, 위치가 갈리지 않는 사실을 AskUserQuestion 한 라운드로 물음 — 각 질문에 권장안 포함
- **답이 정본**: 사용자 답을 `확인 — 사용자 확인 {오늘}` 출처로 기록하고, `모름`·`알아서`는 권장안 채택으로 처리하며 다시 묻지 않음
- **0건 통과**: 물을 것이 없으면 멈추지 않음

## 5. 반영 — 승인 하나

- **초안**: 문서별 경로·`description`·바뀌는 절과 불릿을 보이고 승인을 받음 — 삭제·분할·이동이 있으면 그 항목을 따로 표시
- **병합**: 기존 본문을 유지하고 해당 절 끝에 불릿 추가 또는 값 교체 — 문서 전체 재작성 금지, 변경 서사 금지
- **frontmatter**: 보강·교체는 `updated`·`verified` 오늘, 동일은 `verified`만
- **출처 줄**: `> 출처: 확인 — {문서명 판본}, {날짜}` 또는 `> 출처: 확인 — 사용자 확인, {오늘}`
- **신규 문서**: 규약 3·4장의 위치·골격·description으로 세우고 40자 한 문장으로 안 덮이면 나눔
- **검사·커밋**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {바꾼 파일}` 에러 0 확인 후 문서마다 커밋, 처리한 `review.md` 행 삭제를 같은 실행의 마지막 커밋에 담고 `pull --rebase && push`

## 6. 보고

- **파일 목록**: 생성·수정 문서와 보강·교체·동일 건수
- **미기록**: 원본에 없어 기록하지 못한 항목, 사용자가 기존 값 유지로 답한 행
- **반영 시점**: 다음 세션 목록에 반영
```

### `skills/update/SKILL.md`

```markdown
---
name: update
description: Use when merged code in registered repos must be reflected into the wiki without questions ("위키 업데이트", "무인 갱신", "머지 반영", "최근 머지 위키에 반영", a scheduled run, or a pointed --repo/--range) — walks every registered repo from its cursor, fans out one subagent per first-parent merge to extract facts, assigns facts to docs against the catalog, fans out one subagent per doc to apply, runs --check, commits per doc, advances the cursor, pushes. 관찰-tier only: confirms and adds, never overwrites; conflicts and common-space candidates go to review.md. NOT for material the user hands over (that is /llm-wiki:add's job) and NOT for sweeping existing docs (that is /llm-wiki:audit's job).
disable-model-invocation: true
---

등록된 레포의 머지된 코드를 사용자 응답 없이 프로젝트 폴더에 반영합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`가 정본이며 서브에이전트에게는 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. 이 스킬은 `관찰` 출처만 만들므로 기존 값을 지우거나 바꾸지 않고, `common/`을 고치지 않습니다.

인자: `--repo {slug}`(대상 한정), `--range {rev-range}`(지목 범위, 커서 불변), `--max-merges N`(레포별 예산, 기본 20), `--baseline-days N`(커서 없는 레포 소급), `--dry-run`(3장까지).

## 1. 범위 확정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단(팀원 커밋과 갈라진 상태에서 무인 편집 금지)
- **실행**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" pending --out {스크래치} {인자}` — 레포별 커서 이후 first-parent 커밋 목록과 머지별 diff 파일을 만들고 `work.json` 경로를 마지막 줄에 냄
- **종료 코드**: 0 작업 또는 부트스트랩 있음(`work.json`만 Read), 10 미처리 없음(한 줄 보고 후 종료), 1 오류(stderr 전달 후 중단)
- **건너뜀**: `work.json`의 `skipped`(로컬 경로 없음·force-push 의심·fetch 실패)는 그대로 보고에 옮김
- **부트스트랩**: 커서 없던 레포는 커밋 0건이라도 5장에서 HEAD를 커서로 기록함
- **입력 집합**: 추출된 diff와 그 범위의 커밋 메시지·함께 커밋된 노트만 — 범위 밖 작업 트리·사전 지식·현재 코드 재조회로 채우지 않음

## 2. 추출 fan-out — 머지 1건 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`, 출력은 파일 Write, 응답은 건수만 — 사실이 메인 컨텍스트를 지나지 않아야 한 세션이 수십 건을 처리함. 머지 3건 이하면 메인이 직접 처리. 응답 없는 머지는 3장 전에 재실행.

````
머지 1건에서 오래 남을 사실을 추출하는 작업입니다. 위키 문서 작성이 아니라 사실 목록 기록입니다.

- diff: {diff_path}를 Read로 읽으세요. 머리말에 커밋 메시지·변경 파일 목록·절단 여부가 있습니다.
- 커밋 메시지와 diff에 함께 실린 .md 노트도 근거입니다 — 결정 근거 문장은 원문 그대로 quote에 옮기세요.
- 코드 저장소의 다른 파일을 열지 마세요. 사전 지식으로 공백을 채우지 마세요.

기록 기준은 규약 원문입니다 — `sed -n '/^## 1\. 담는 것/,/^## 2\./p' {doc_contract_path}`를 읽고 후보 문장마다 적용하세요.
코드 검색 한 번으로 확인되는 문장(시그니처·타입·enum·파일 위치·호출 관계·한 심볼의 내부 동작)과
이번 변경의 서사("A를 B로 바꿈")는 사실이 아닙니다. 남는 것은 코드에 없는 결정·제약·금지·외부 계약·컨벤션입니다.

출력: {facts_dir}/{slug}/{sha7}.json에 Write — 객체 1개 = 사실 1건.
[{"fact": "현재 상태를 말하는 한 문장(업무 낱말 우선, 식별자는 괄호 병기, 줄바꿈 금지)",
  "topic": "2~4낱말 주제",
  "code": "저장소 상대 경로 또는 파일#심볼 — 필수",
  "quote": "커밋 메시지·노트의 결정 근거 원문 — 있을 때만"}]
사실 0건이면 []을 쓰세요. 응답은 사실 건수만 반환하세요.
````

## 3. 배정 — 메인 세션 전담

- **입력**: `{facts_dir}/**/*.json`을 전부 읽음 — 사실 문장이 메인을 지나는 유일한 지점
- **중복 병합**: 같은 레포에서 같은 주장을 하는 사실은 하나로 합침
- **위치**: 규약 3장 위치 판정에서 공통으로 가는 사실은 편입하지 않고 `review.md`에 `공통 후보` 행으로 기재
- **대조**: 현재 프로젝트 목록(`catalog.py --root {WIKI_ROOT}/knowledge/projects/{p}`)의 `description` 전수와 grep으로 대상 문서를 찾음 — 후보가 둘이면 범위가 좁은 문서
- **신규 문서**: 대상이 없는 사실은 주제로 묶어 40자 한 문장으로 덮이면 신규 1장, 덮이지 않으면 나누고 그래도 서지 않으면 `기각 — 한 주제 아님`
- **배치 내 상충**: 같은 주제에 값이 다른 사실 둘은 둘 다 `review.md`
- **배정표**: `{스크래치}/assign.json`에 문서별 사실 목록·신규 여부를 씀 — `--dry-run`이면 배정표를 보고하고 종료

## 4. 반영 fan-out — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`. 같은 파일을 두 에이전트가 고치지 않게 문서 단위로 묶고, 에이전트는 커밋하지 않음.

````
위키 문서 한 장에 사실 여러 건을 대조·반영하는 작업입니다. 이 문서 밖의 파일을 고치지 말고 커밋하지 마세요.

- 배정: {assign_path}의 "{doc}" 항목을 읽으세요 — 문서 경로·신규 여부·사실 행(fact·topic·code·quote·slug·sha·머지 날짜).
- 입력 집합은 이 파일이 전부입니다. 코드 저장소를 조회하지 말고 사전 지식으로 채우지 마세요. 오늘은 {today}입니다.
- 규약 전문을 Read {doc_contract_path}로 읽고 4·5·7장을 그대로 적용하세요.

기존 문서: 본문을 열어 사실마다 값 단위로 판정하세요.
- 동일 — 본문 유지, frontmatter verified만 {today}. code가 그 값 자체를 짚었을 때만이며 주제가 겹친다는 이유로 올리지 마세요.
- 보강 — 해당 절 끝에 불릿 추가, updated·verified {today}. 문서 전체 재작성 금지.
- 충돌 — 기존 값과 다르면 본문을 고치지 말고 excluded에 {기존 값(절), 기존 출처 줄 전사, 새 값, code}를 적으세요. 관찰은 기존 값을 지우지 못합니다.
신규 문서: description은 40자 목표·60자 상한·"때" 종결·이 문서에서만 참인 낱말 1개, 한 레포에서만 참이면 레포명 포함,
채울 사실 없는 절은 두지 않고, 제목은 사실이 실제로 답하는 범위로만 — 조각에 주제 이름을 붙이지 마세요.

공통: 다른 위키 문서 이름·링크 금지, 변경 서사 금지, 업무 낱말 먼저. 업무 낱말을 붙일 수 없는 식별자만 남는 행은 blocked "내부 동작 서술".
출처 줄: 블록 끝에 `> 출처: 관찰 — {slug} @{sha7} 머지, {머지 날짜}`를 두고 같은 레포의 옛 관찰 줄은 이 줄로 대체하세요.
검사: `python3 {catalog_py} --check --root {knowledge_root} {doc_abs}` — 에러가 남으면 고치고, 못 고치면 편집을 되돌리고 blocked에 사유.

출력: {applied_dir}/{doc_slug}.json에 Write —
{"doc","created","verdicts":[{"id","verdict":"동일|보강","heading"}],"excluded":[{"id","기존 값","기존 출처","새 값","code"}],"blocked":null|"사유","check":"pass|fail"}
응답은 판정별 건수만 반환하세요.
````

## 5. 검증·커밋·커서

- **전수 검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge` — 이번에 손대지 않은 문서의 에러는 고치지 않고 보고에 남김
- **되돌림**: `blocked`·`check: fail` 문서는 `git -C {WIKI_ROOT} checkout -- {경로}`로 원복하고 그 사실은 보고의 `기각`, 되돌린 머지가 있으면 커서는 그 머지 직전까지만
- **review.md**: `excluded`·`공통 후보`·배치 내 상충 행을 `- [{날짜}] [{project}] {주제} — 기존 {값} ({파일:절}, {출처}) / 새 {값} ({slug} @{sha7} {code})` 형식으로 append
- **커밋**: 문서마다 `docs({project}): {파일명} {요약}`, 그 뒤 `python3 update.py advance {slug} {sha}`로 `state/{slug}.json` 갱신 + `review.md`를 `chore(update): {slug} 커서 {sha7} · 머지 N건 · 문서 M건` 한 커밋 — 사실 0건 머지도 전진, 예산으로 잘린 머지 앞에서 멈춤, `--range` 실행은 커서 불변
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 재시도 2회, 실패는 로컬 커밋 상태와 함께 보고

## 6. 보고

- **레포별**: 처리 머지 수·사실 수·커서 전후·건너뜀 사유
- **문서**: 생성·수정 목록과 동일·보강 건수
- **확인 필요**: `review.md`에 남긴 행 전부 — 이 실행이 사람에게 남기는 판정 요청이며 `/llm-wiki:add`로 집음
- **기각**: 사유별 건수(담지 않는 것·한 주제 아님·내부 동작 서술·검사 실패)
- **후속**: 신규 문서 목록과 `/llm-wiki:audit` 권고
```

### `skills/audit/SKILL.md`

```markdown
---
name: audit
description: Use when the wiki must be swept after unattended updates or on a schedule ("위키 정리", "위키 감사", "문서 정리", "중복 정리", "낡은 문서 확인") — measures the wiki with catalog.py --check, fans out subagents over 5–6 docs per batch to flag fragments, duplicate facts, stale docs, over-long descriptions and contract violations, presents one approval table with before/after lines, applies per doc, re-checks, commits and pushes. Adds no new facts. NOT for landing new material or merged code (that is /llm-wiki:add and /llm-wiki:update's job).
---

기존 문서만 고치고 새 사실을 들이지 않습니다. 규약은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`가 정본이며 서브에이전트에게는 절대 경로로 넘깁니다. 인자: `--scope common|{project}`(기본 공통 + 현재 프로젝트), `--docs {경로...}`(지목 문서만).

## 1. 측정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only`, 실패 시 중단
- **검사·목록**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge`의 에러와 `catalog.py --root {루트}` 목록을 `{스크래치}/catalog.md`로 저장 — `!` 낡음·60자 초과·description 중복이 여기서 나옴
- **인박스**: `review.md`의 해당 스코프 행 수를 세고 "처리는 `/llm-wiki:add`" 안내
- **묶음**: 대상 문서를 스페이스별 5~6건으로 나누고 문서마다 검사 줄을 힌트로 붙임 — 메인은 문서 본문을 열지 않음

## 2. 진단 fan-out — 묶음 1개 = 에이전트 1회

한 메시지에 병렬 Agent 호출, 모델은 메인 상속(삭제·통합 판정은 품질이 갈리는 자리). 응답 없는 묶음은 재실행.

````
위키 문서를 진단하는 작업입니다. 판정만 하고 문서를 고치지 마세요. 커밋하지 마세요.

- 대상: {절대 경로 5~6건}. 목록 전체는 {catalog.md}. 힌트: {문서별 --check 에러 — 없으면 "없음"}.
- 읽을 수 있는 것은 대상 문서·목록·규약 `sed -n '/^## 1\./,/^## 7\./p' {doc_contract_path}`뿐입니다. 코드 저장소 조회 금지, 사전 지식으로 공백 채우기 금지.
- 오늘은 {today}입니다.

문서마다 아래 신호를 판정하고 조치 행을 쓰세요. 값이 어긋나는 불릿 쌍은 통합하지 않고 `충돌`로 적으세요.

| 신호 | 조치 |
|---|---|
| 같은 문서 안에서 같은 주장을 하는 불릿 둘 | `통합` — 전: 두 줄 원문, 후: 조건·수치·근거를 합집합한 한 줄 |
| 코드 검색 한 번으로 참이 확인되는 불릿 | `삭제` — 후 비움, 비고에 확인 위치 |
| 변경 서사 불릿("A에서 B로", "추후", "폐기") | 현재 상태로 다시 쓸 수 있으면 `재작성`, 없으면 `삭제` |
| 다른 위키 문서 링크·이름 참조 | 접점 사실로 `재작성`, 남는 것이 "다른 곳에 있다"뿐이면 `삭제` |
| description 60자 초과·"때" 미종결·범주어만 | `설명` — 후: 새 문장. 한 주제로 60자에 안 덮이면 `분할 후보` |
| 40줄 미만이고 목록의 다른 문서 description이 이미 그 주제를 덮음(조각) | `흡수` — 후: 소유 문서 경로와 절, 비고에 옮길 불릿 원문 |
| 절 제목과 다른 질문에 답하는 불릿 | `이동` — 후: 대상 절 |
| `!` 낡음 문서 | 위 점검을 마쳤으면 `검증`, 코드 대조가 필요한 값은 `확인 필요` |

응답은 표 행만 — `| 조치 | 문서:절 | 전 | 후 | 비고 |`. 전·후는 원문 줄 그대로(여러 줄은 <br>), 요약 금지. 신호 없는 문서는 `없음` 행 하나.
````

## 3. 승인 — 정지점 하나

- **승인 대상**: `삭제`·`통합`·`흡수`·`이동`·`분할 후보` 행 — 번호·조치·문서:절·전·후를 채팅에 그대로 싣고, 사용자가 제외한 번호 외는 전부 승인
- **승인 불필요**: `재작성`·`설명`·`검증`은 `{스크래치}/approval-{날짜}.md`에만 두고 적용
- **충돌·확인 필요**: 적용하지 않고 `review.md`에 append
- **0행**: 승인 대상이 없으면 표를 제시하지 않고 4장으로

## 4. 적용 fan-out — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`(전사와 검사만 남음). 흡수 행은 소유 문서의 에이전트가 맡음. 에이전트는 커밋하지 않음.

````
위키 문서 한 장에 승인된 조치를 적용하는 작업입니다. 이 문서와 지시된 흡수 조각 밖의 파일을 고치지 말고 커밋하지 마세요.

- 문서: {절대 경로}. 행: 아래 표가 편집의 전부 — `전` 줄을 찾아 `후`로 바꾸고 그 밖의 문장은 한 글자도 바꾸지 마세요. `후`가 빈 행은 `전` 줄 삭제입니다.
{이 문서의 행}
- 흡수 행: 조각 {조각 경로}의 불릿을 이 문서의 지정 절 끝에 옮기고 조각의 출처 줄을 이 문서 블록 끝으로 옮긴 뒤 조각 파일을 삭제하세요.
- 문체는 `sed -n '/^## 5\./,/^## 6\./p' {doc_contract_path}`. frontmatter updated는 {today}, verified는 `검증` 행이 있을 때만 {today}.
- 적용 뒤 행마다 `grep -cF '{후 첫 줄}' {문서}`로 반영을 확인하고(흡수는 옮긴 불릿마다), `python3 {catalog_py} --check --root {knowledge_root} {문서}` 에러가 남으면 고치고 못 고치면 `git -C {WIKI_ROOT} checkout -- {문서}`로 되돌려 blocked에 사유.

응답: 적용 행 번호, 건너뛴 행과 사유, 삭제·생성 파일, check 결과, blocked 사유.
````

## 5. 검증·커밋

- **전수 검사**: 삭제·흡수 뒤 `catalog.py --check --root {WIKI_ROOT}/knowledge` 재실행 — description 충돌은 문서 단위 검사가 못 봄
- **커밋**: 본문이 바뀐 문서마다 `docs({space}): {파일명} audit {조치 요약}`, `verified`만 바뀐 문서는 `docs: verified 갱신 N건 (audit)` 한 커밋, `pull --rebase && push`

## 6. 보고

- **처리**: 문서 수·조치별 건수·삭제 파일
- **승인**: 승인 행 수·제외 번호
- **충돌·확인 필요·분할 후보**: 문서와 내용 — `review.md`에 남긴 다음 작업
- **검사**: 남은 에러와 그 문서
```

## 스크립트·훅 사양

### `hooks/session_start.sh` (목표 약 60줄)

```
set -uo pipefail
WIKI="${LLM_WIKI_ROOT:-$HOME/.ai-docs/wiki}"; PLUGIN="$CLAUDE_PLUGIN_ROOT"; PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -d "$WIKI/knowledge" ] || { printf JSON "LLM-WIKI: 위키가 $WIKI 에 없음 — /llm-wiki:init 으로 clone 또는 생성"; exit 0; }

# 원격 동기화: 원격 있고 FETCH_HEAD가 60분 초과면 백그라운드 pull --ff-only, 0.5초×6 폴링, GIT_TERMINAL_PROMPT=0
SYNC_NOTE=""  # 미완/실패 시 "# 위키 동기화 {지연|실패} — 아래 목록은 이전 사본. 첫 응답에서 사용자에게 알릴 것"

REMOTE="$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || git -C "$PROJECT_DIR" remote get-url upstream 2>/dev/null || true)"
COMMON_DIR="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"

python3 -B - "$PLUGIN" "$WIKI" "$PROJECT_DIR" "$REMOTE" "$COMMON_DIR" "$SYNC_NOTE" <<'PY' 2>/dev/null || exit 0
  sys.path.insert(0, scripts); import catalog
  guide = rules/agent-guide.md 읽고 {WIKI_ROOT} 치환
  slug, project = catalog.resolve_repo(registry, remote, common_dir)     # 정규화 remote 매칭 → slug 폴백 → 미등록
  if project: upsert .local/paths.json[slug] = toplevel (값이 다를 때만 쓰기)
  header = [sync_note, "# 위키 — 프로젝트 {p} · 레포 {slug} · 형제: {slug2}: {summary}", review 미처리 N건, cursor lag 줄]
  blocks = [guide, header, catalog.build(knowledge/common, "공통"), catalog.build(knowledge/projects/{p}, "프로젝트 {p}") if p]
  + "# 다른 프로젝트 N개: … — 주입 안 함" / 미등록이면 "# 미등록 레포 {slug} — /llm-wiki:init"
  apply_budget(soft=8000, hard=12000)
  print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ...}}, ensure_ascii=False))
PY
```

- `hooks.json`: SessionStart 1개, matcher 없음. `python3 -B`로 `__pycache__` 생성 방지
- 실패 모드: python3 없음 → 무음 exit 0(README 요구 사항 명시). `registry.json` 파싱 실패 → 목록은 주입, 헤더에 한 줄. 문서 frontmatter 깨짐 → `!! frontmatter 파싱 실패` 행 유지(원본 계약). `catalog` 예외 → 규약은 주입, 목록 자리에 실패 문장

### `scripts/catalog.py` (목표 약 180줄)

- **재사용(그대로)**: `parse_frontmatter`(BOM·CP949·미닫힘 방어), `parse_date`, `staleness_date`(필드 `verified`→`updated`), `sort_key`, `estimate_tokens`, `build`의 행 형식·파일 수 기준 머리·`(아직 문서가 없음)`·어떤 입력에도 exit 0
- **수정**: `build(root, label, today, stale_days=180)` 시그니처, 스페이스 루트 상대 경로 출력, `_`로 시작하는 `.md` 제외. `check_fields`는 필수 3키·미승인 키·날짜 형식·미래 날짜·60자 상한만(에러만, 경고 개념 없음). `check_location`은 정규식 `^(common|projects/[a-z0-9-]+)(/adr)?/[a-z0-9-]+\.md$`. `inspect_across`는 description 중복만(스페이스 무관 전역). `check_body` 첫 줄 `# ` 유지
- **신규**: `resolve_repo(registry, remote, common_dir)`(정규화·매칭·slug 폴백, 약 25줄) — 훅과 update.py가 공유
- **버림**: `Space`·`SPACE_PRESETS`·`--space/--label/--branch-warning`·`git()` HEAD 머리·`path_note`·`over_limit`·`ALLOWED_DIRS`·`DEPRECATED_FIELDS`·`TRANSITIONAL_WARNINGS`·`--strict`·`selected_names`·`doc_links`·`check_links`·`check_source_lines`·`JIRA_KEY_RE`·`import sources`·`--review` 전체와 그 정규식(`CODE_ID_RE`의 `CMS_APP_`·`PD\d{6}` 사내 식별자 포함)
- **CLI**: `catalog.py --root DIR [--label L] [--check [FILES...]] [--stale-days N]`, 종료 코드 목록 0 / 검사 에러 시 1

### `scripts/update.py` (목표 약 140줄)

```
EXCLUDE_PATHSPECS = collect.py L59~74 그대로(lock·min·svg·dist·node_modules 등 11개), DIFF_MAX_BYTES = 400_000
git(cwd, *args, timeout=60)
pending --out DIR [--repo SLUG...] [--range REV] [--max-merges 20] [--baseline-days N]:
  registry = load(registry.json); paths = load(.local/paths.json)
  for slug, info in registry.repos:
    path = paths.get(slug) or skipped "로컬 경로 없음 — 그 레포에서 세션을 한 번 열면 등록됨"
    git fetch --quiet origin (실패 → note "fetch 실패 — 로컬 ref 기준")
    branch = info.branch or symbolic-ref refs/remotes/origin/HEAD 꼬리 or "main"; target = origin/{branch} if verify else branch
    head = rev-parse target; cursor = state/{slug}.json.cursor
    bootstrapped = cursor is None → cursor = baseline(--baseline-days) or head
    if not merge-base --is-ancestor cursor head: skipped "커서가 HEAD 조상이 아님(force-push 의심) — advance로 재설정"
    rows = log --first-parent --reverse --format=%H%x09%P%x09%ad%x09%s --date=short {cursor}..{head} [:max]; remaining
    for row: extract(path, row, DIR/slug/sha7.diff)   # parents≥2 → diff sha^1 sha, 아니면 show --format= sha; --name-status 머리말 + %B 커밋 본문 + 절단 표기
  work.json {repos: {slug: {project, path, branch, head, cursor, bootstrapped, commits[], remaining}}, skipped}
  exit 0 if any(commits or bootstrapped) else 10
advance SLUG SHA: state/{slug}.json = {cursor, branch, at, merges, docs}; 조건 "SHA가 target의 조상"
status: registry + state를 표로 출력(사람용 표 파일을 두지 않는 대체)
```

- **버림**: 미러 팜·락·오프라인 마커·`facts/` 원자재·manifest runs·assemble·pick 샤드·ledger 원장·PR 본문. 순번 원자성은 "레포별 커밋 → 커서 전진" 순서로 자연 성립
- **신규 근거(⑦)**: 표준 라이브러리에 first-parent 순회·diff 절단·JSON 커서를 묶은 것이 없고, 스킬 프롬프트 bash 5×N회는 재현성이 무너짐

## 파일 목록과 마켓 등록

| 경로 | 내용 |
|---|---|
| `llm-wiki/.claude-plugin/plugin.json` | name `llm-wiki`, version `1.0.0`, author argon1025, keywords `["wiki","knowledge","위키","지식"]` |
| `llm-wiki/hooks/hooks.json`, `hooks/session_start.sh`(755) | D3 |
| `llm-wiki/scripts/catalog.py`, `scripts/update.py` | 사양 참조 |
| `llm-wiki/rules/agent-guide.md`, `references/doc-contract.md` | 초안 |
| `llm-wiki/skills/{init,update,add,audit}/SKILL.md` | 초안 |
| `llm-wiki/README.md` | `## 설치`(`/plugin install llm-wiki@my-claude-plugin-market`, `LLM_WIKI_ROOT`는 `~/.claude/settings.json`의 `env`로 지정) · `## 전제 조건`(`python3`, `git`, 위키 원격 저장소) · `## 동작 방식`(주입 스코프·커서·`review.md`) · `## 위키 구조`(D1 트리·`registry.json` 예시) · `## 스킬`(4종 표) · `## 미이전 기능`(아래 제외 목록) |
| `.claude-plugin/marketplace.json` | `metadata.version` 2.2.0 → 2.3.0, plugins 항목 `{name: llm-wiki, source: ./llm-wiki, description: "LLM 위키 — 별도 git 저장소의 공통·프로젝트 문서 목록을 세션 시작 시 주입 + 스킬 4종(init·update·add·audit), 무인 갱신은 등록 레포 커서 기준", category: knowledge, tags: [wiki, knowledge, git]}` |
| 루트 `README.md` | 설치 코드블록 한 줄 + 표 한 행(요구 사항 `python3`, `git`, 위키 원격 저장소) |
| `.claude/settings.local.json` | 로컬에서 `"llm-wiki@my-claude-plugin-market": true` 추가 — 전역 gitignore라 커밋 대상 아님 |

## 제외 기능 기록 (README `## 미이전 기능`과 커밋 본문에 기재)

- **영구 제외**: `sync`(훅이 pull, 스킬이 push), `scope-review`(Jira·system-repository-map 전제), `auto-collect`·`auto-publish`의 `facts/` 원자재 대장·원장·샤드·락·오프라인 마커·PR 본문 생성, `apply-change.md`(PR 게이트), `gate.sh`(Bitbucket 게이트), UserPromptSubmit 리마인더, `sources.py`(출처 병합 — 규약으로 제거), `pick.py`·`ledger.py`·`assemble.py`, 테스트 4종, `catalog.py --review`
- **추후 후보**: `pdf-to-material`(대형 PDF 입력 시 `add` 전처리), `clean-space`의 restructure·split·complete 코드 보완 모드, `preserve.py`(재구조화 도입 시), 문서별 `anchor`·`watch` 드리프트 표시, 프로젝트 하위 `repos/{slug}/` 층, 레포 내 `.ai-docs/knowledge/` 오버레이, 모양 폴더(policy/process/domain/external)
- **의도적 단순화(feedback.md `context`)**: 커서 기반 낡음 신호만(업그레이드 조건: 커서 최신인데 낡은 문서 관측), 로컬 체크아웃 있는 레포만 무인 대상(업그레이드 조건: 다른 머신에서 갱신 필요), 2층 폴더(업그레이드 조건: 한 프로젝트 레포 종속 문서 30건 초과), 테스트 파일 없음(업그레이드 조건: catalog.py 두 번째 수정 시 원본 `BuildContract` 7개 이식)

## 작업 순서와 커밋 분해

브랜치 `feat/llm-wiki`(main에서 분기), 워크스페이스 slug `feat-llm-wiki`. 브랜치 위 4커밋 → PR → squash 머지(main 1커밋, 관례).

| # | 커밋 | 내용 | 검증 |
|---|---|---|---|
| 0 | `docs: llm-wiki 이관 계획 스냅샷` | `.ai-docs/workspace/feat-llm-wiki/plan.md`(이 계획 전문), `feedback.md`(의도 `context` + 의도적 단순화 `context` 항목, 형식은 `plan-workflow/references/record-format.md`) | 파일 존재 |
| 1 | `feat(llm-wiki): 골격·SessionStart 훅·catalog.py` | plugin.json, hooks.json, session_start.sh, scripts/catalog.py, rules/agent-guide.md | V1~V4 |
| 2 | `feat(llm-wiki): update.py·규약·스킬 4종` | scripts/update.py, references/doc-contract.md, skills/*/SKILL.md, llm-wiki/README.md | V5~V10, V12 |
| 3 | `feat: marketplace 2.3.0·루트 README 등록` | marketplace.json, 루트 README | V11 |

Squash 제목: `feat: devcenter-wiki 최소 이전 llm-wiki 추가 v2.3.0`. 본문 불릿 4개 — 이전 내용(SessionStart 목록 주입·catalog 목록/`--check`·update 무인 갱신·스킬 4종) / 범용화(별도 git 위키 저장소 `LLM_WIKI_ROOT`, `common/`+`projects/{p}` 2층, `registry.json`·`state/{slug}.json` 등록·커서, 훅 60분 게이트 pull) / 제외+압축(위 제외 목록, 훅 300줄→약 60줄, 스크립트 4,569줄→약 320줄, 규약 690줄→약 80줄, 실측치로 교체) / marketplace 2.3.0·README 갱신. 꼬리 `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. PR 본문 4절(`## 개요`·`## 작업 내역`·`## 영향도`·`## 검증 결과`) + `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## 검증

픽스처는 스크래치패드 `$FX`에 생성하고 커밋하지 않음: `$FX/wiki`(`git init`, `knowledge/common/a.md` 정상 `verified` 오늘, `knowledge/projects/demo/b.md` `verified: 2025-01-01`, `knowledge/projects/demo/broken.md` frontmatter 없음, `knowledge/projects/demo/dup.md` description이 a.md와 동일, `registry.json`에 `repo-a`·`repo-b`를 project `demo`로 등록, `.gitignore` `.local/`), `$FX/repo-a`·`$FX/repo-b`(`git init` + 커밋 2개, repo-a는 `git merge --no-ff` 머지 1개, origin URL `https://github.com/x/repo-a.git` 등록만), `$FX/wiki/.local/paths.json`에 두 경로.

| # | 명령 | 기대 |
|---|---|---|
| V1 | `python3 llm-wiki/scripts/catalog.py --root $FX/wiki/knowledge/projects/demo --label 프로젝트; echo $?` | `# 프로젝트 3건 · 약 N토큰`, `b! — …`, `broken — !! frontmatter 파싱 실패: frontmatter 없음. 직접 읽을 것`, exit 0 |
| V2 | `python3 llm-wiki/scripts/catalog.py --check --root $FX/wiki/knowledge; echo $?` → broken·dup 삭제 후 재실행 | `에러  projects/demo/broken.md: frontmatter 없음`, `에러  projects/demo/dup.md: description이 common/a.md와 같음`, `# 문서 4건 · 에러 2건`, `1` → `# 문서 2건 · 에러 0건`, `0` |
| V3 | `LLM_WIKI_ROOT=$FX/wiki CLAUDE_PLUGIN_ROOT=$PWD/llm-wiki CLAUDE_PROJECT_DIR=$FX/repo-a bash llm-wiki/hooks/session_start.sh \| python3 -c 'import json,sys;print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'` | 규약 본문({WIKI_ROOT} 치환) + `# 위키 — 프로젝트 demo · 레포 repo-a · 형제: repo-b` + `# 커서 없음 — 첫 update가 등록` + 공통·프로젝트 목록, `.local/paths.json`에 repo-a 경로 |
| V4 | 같은 명령을 `LLM_WIKI_ROOT=$FX/none`으로 / `CLAUDE_PROJECT_DIR=/tmp`로 | 안내 한 줄 JSON에 `$FX/none`·`/llm-wiki:init` 포함, exit 0 / 공통 목록만 + `# 미등록 레포 tmp` 없이 비git 처리(프로젝트 블록 없음) |
| V5 | `python3 llm-wiki/scripts/update.py pending --wiki $FX/wiki --out $FX/out; echo $?` | 두 레포 `bootstrapped: true`, `commits: []`, exit 0 |
| V6 | `update.py advance repo-a $(git -C $FX/repo-a rev-parse HEAD)`(repo-b도) → repo-a에 커밋 1 + 머지 1 추가 → V5 재실행 | `state/repo-a.json`·`state/repo-b.json` 생성, repo-a `commits` 2건(머지 `parents: 2`, diff 머리말에 name-status·커밋 본문), repo-b 0건, exit 0 |
| V7 | `state/repo-b.json` 삭제 후 `pending --baseline-days 30` | repo-b 커서가 30일 전 first-parent sha(픽스처가 전부 30일 내면 HEAD), `commits`에 그 이후 전부 |
| V8 | `.local/paths.json`에서 repo-b 삭제 후 V5 | `skipped.repo-b: 로컬 경로 없음`, repo-a 정상 |
| V9 | V6 뒤 `advance repo-a {마지막 sha}` → V5 | exit 10, `(미처리 없음)` |
| V10 | repo-a에 500KB 파일 커밋 후 V5 | 해당 diff 머리말 `절단됨`, 파일 약 400KB |
| V11 | `claude plugin validate .`; `python3 -c 'import json;m=json.load(open(".claude-plugin/marketplace.json"));print(m["metadata"]["version"],[p["name"] for p in m["plugins"]])'`; `git ls-files -s llm-wiki/hooks/session_start.sh` | 통과, `2.3.0 [..., 'llm-wiki']`, `100755` |
| V12 | 사내 문자열: `grep -rniE 'bitbucket\|onestorecorp\|onestore\|devcenter\|confluence\|jira\|\.devcenter\|mcp__onestore__\|1000377\|CMS_APP\|PD[0-9]{6}\|GA[0-9]{6}\|그룹 스페이스\|레포 스페이스\|harvest-log\|facts/\|auto-publish\|auto-collect\|clean-space\|scope-review\|pdf-to-material' llm-wiki/`; `find llm-wiki -name '__pycache__' -o -name '*.pyc'` | 둘 다 출력 0줄 (README `## 미이전 기능` 절의 원본 스킬명 나열은 허용 — 그 절만 grep 제외 처리하거나 스킬명을 한글로 기재) |
| V13 | 머지 후 `/plugin marketplace update my-claude-plugin-market` → `/plugin install llm-wiki@my-claude-plugin-market` → 새 세션 `/llm-wiki:init`(원격 URL 지정) → 세션 재시작 → 사이드 프로젝트 레포에서 `/llm-wiki:update` → `/llm-wiki:audit` | 세션 컨텍스트에 규약·목록·커서 줄 주입, update가 문서·커서 커밋과 push, audit가 승인 표 1회 후 커밋 |

## 범위 밖 알림

- `~/.claude/plugins/cache/my-claude-plugin-market/{dev-harness,pull-request-workflow}/1.0.0` 잔존 캐시와 `~/.claude/plugins/installed_plugins.json`의 두 project 스코프 항목은 이번 커밋과 무관한 로컬 상태 — 해당 프로젝트에서 `/plugin uninstall`로 별도 처리
- 기존 사내 위키 문서(172 + 128건) 이관은 범위 밖 — 필요 시 폴더 접두 제거·`projects/devcenter/` 배치 1회성 스크립트로 별도 작업

## 핸드오프

- **승인 시**: `main`에서 `feat/llm-wiki` 분기 → `.ai-docs/workspace/feat-llm-wiki/plan.md`에 이 계획 전문, `feedback.md`에 `context` 항목(의도 3문장 원문, 사용자 결정 원문, 의도적 단순화 4건) 기록 → 커밋 0 → 정지
- **구현**: 새 세션에서 `/plan-workflow:execute`로 시작, 커밋 1~3을 표 순서대로 검증과 함께 수행
