# llm-wiki

LLM 위키 플러그인입니다. 위키는 "지금 무엇이 참인가"를 답하는 현행 합의이며, 코드에 없는 사실(레포 사이에 맞춰야 하는 값·방식, 결정 근거, 외부 계약, 함정)과 레포 그래프(노드·간선)를 별도 git 저장소에 모으고, 세션 시작 시 그 목록과 그래프를 주입합니다. 위키는 플러그인 저장소 밖에 있어 여러 머신과 팀원이 같은 저장소를 공유합니다.

| 스킬 | 트리거 예 | 역할 |
| --- | --- | --- |
| `/llm-wiki:init` | "위키 초기화", "위키 세팅" | 위키 clone 또는 생성, 원격 연결, 골격(`registry.json`·`deps.json`·`state/`·`knowledge/`) 생성 |
| `/llm-wiki:register` | "이 레포 위키에 등록", "도메인 이동" | 정본 remote를 판별하고 현재 레포를 4레인 병렬 조사·인벤토리 대조로 노드·의존 간선 기록, 근거 없는 호스트는 질문, 도메인·owner 선택, 상태 표 |
| `/llm-wiki:update` | "위키 업데이트", "머지 반영" | 전 도메인 미처리 머지를 시각 순으로 무인 반영 — 새 사실은 추가, 기존 값은 의도 인용이 있을 때만 교체, 나머지는 건너뛰어 최종 보고에 기록, 커서 전진 |
| `/llm-wiki:add` | "위키에 정리해줘", "정책으로 기록해줘" | 건넨 자료·대화·update가 건너뛴 행의 사실을 반영, 기존 값과 다른 건은 두 값을 보이고 질문 한 라운드 |
| `/llm-wiki:audit` | "위키 정리", "중복 정리" | 조각·중복·과길이 description·규약 위반을 승인 표 하나로 정리 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install llm-wiki@my-claude-plugin-market
```

설치 후 새 세션에서 `/llm-wiki:init`으로 위키 저장소를 놓고, 각 레포에서 `/llm-wiki:register`로 등록합니다. 위키 경로 기본값은 `~/.ai-docs/wiki`이며, 바꾸려면 `~/.claude/settings.json`의 `env`에 지정합니다.

```json
{ "env": { "LLM_WIKI_ROOT": "/절대/경로/wiki" } }
```

## 전제 조건

- **python3·git**: 훅과 스크립트가 둘 다 씀 — `python3`가 없으면 주입 없이 조용히 끝남
- **원격 저장소**: 위키는 원격이 있어야 다른 머신·팀원과 공유되며, 원격 없이도 동작하지만 로컬 전용이 됨

## 동작 방식

- **SessionStart**: 규약(`rules/agent-guide.md`) → 상태 헤더 → 그래프 파생 블록(레포 지도 → 현재 레포 기준 의존 3묶음) → 도메인 루트와 현재 레포 문서 목록 순으로 주입하며, matcher가 없어 startup·resume·clear·compact·fork 모두에서 다시 실행됨. 프로젝트 조건 없이 항상 주입하며 끄려면 `/plugin`에서 비활성화함
- **동기화**: 위키에 `origin`이 있으면 startup·resume에서 마지막 fetch가 10분(`LLM_WIKI_SYNC_MINUTES`)을 넘었을 때 `pull --ff-only`를 걸고 3초까지 기다림 — 늦거나 실패하면 이전 사본으로 주입하고 헤더에 알림. 쓰기 스킬은 시작에 `pull --ff-only`, 끝에 `pull --rebase && git push`
- **그래프 파생**: 레포 지도(도메인별 레포와 책임·소관, owner)와 좌표 패턴(로컬 경로·clone URL의 공통 규칙과 예외), 라이브러리를 거쳐 닿는 파급 대상(`(경유 {lib})` 1홉)은 저장하지 않고 `scripts/graph.py`가 `registry.json` 노드와 `deps.json` 간선에서 매번 계산함 — 노드 필드의 상한·열거도 같은 스크립트의 상수 하나에서 나와 `schema` 출력과 `check` 에러가 갈리지 않음
- **그래프 화면(디버깅용)**: `python3 scripts/view.py --wiki ~/.ai-docs/wiki`가 노드·간선을 `templates/graph.html`에 인라인 삽입한 자기완결 HTML을 `{wiki}/.local/graph.html`에 쓰고 macOS에서 브라우저로 염(`--out PATH`·`--no-open`). 도메인 상자·간선 종류별 색·상세 패널·검색·휴면 토글을 제공하며 Cytoscape.js와 fcose는 jsdelivr CDN에서 받음. 사람이 위키 데이터를 점검하는 용도라 세션 주입·규약에는 실리지 않음
- **주입 범위**: 레포 지도는 전 도메인 레포 전수(현재 도메인 행은 책임 문장, 타 도메인 행은 소관 한 줄, 휴면 노드는 이름만, `●`는 로컬 사본)와 좌표 패턴 한 줄, 의존은 현재 레포의 선행 조건·파급 대상 간선(계약 포함, 파급 대상에는 공용 라이브러리를 거쳐 닿는 `(경유 {lib})` 파생 행이 붙음)과 도메인의 다른 의존(from → to kind만), 문서는 현재 도메인 루트 전수(레포 폴더 제외) + 현재 레포 폴더 전수 — 스택·호스트·remote·간선 계약·문서 목록을 레포 하나 기준으로 보려면 `python3 scripts/graph.py repo {slug}`, 다른 도메인의 책임 문장·간선 전수는 `graph.py map --domain {d}`, 훅이 주입하는 블록 전체는 `graph.py render --domain {d} --slug {s}`로 그대로 다시 봄
- **레포 판정**: upstream(없으면 origin) URL을 정규화해 노드의 `remote`와 맞추고 실패하면 URL 마지막 경로 요소를 slug로 씀 — 개인 포크에서 열어도 같은 slug로 모이므로 노드에는 정본 remote만 둠. 미등록이면 규약·등록 안내·도메인 목록만 주입
- **커서 신호**: 레포 커서가 HEAD보다 뒤처지면 몇 커밋 뒤인지가 헤더에 표시됨
- **소프트 예산**: 목록은 어떤 크기에서도 줄이지 않으며 주입이 약 8,000토큰을 넘으면 정리 권고 한 줄이 붙음

## 위키 구조

```
~/.ai-docs/wiki/                    # LLM_WIKI_ROOT
├── registry.json                   # register가 편집: 도메인과 레포 노드 (project는 https://{host}/{owner})
├── deps.json                       # register·update·add가 편집: 레포 간 의존 간선
├── state/{slug}.json               # update만 편집: {"cursor", "at"}
├── .gitignore                      # .local/
├── .local/paths.json               # 머신별 로컬 경로 (미추적, 훅·register가 기록)
└── knowledge/
    └── {조직}-{도메인}/             # 도메인 루트 — 모르고 개발하면 다른 레포에서 문제가 되는 합의
        ├── adr/                    # 선택
        └── {레포 slug}/            # 레포 종속 — 그 레포 안에서만 관심 있는 세부와 레포 사정
            └── adr/                # 선택
```

위치 판정은 "이걸 모르고 개발하면 다른 레포에서 문제가 되는가" 한 단계이며, 도메인 루트와 다른 한 레포의 사정은 그 레포 폴더에 이유와 함께 둡니다. 문서 frontmatter는 `description`과 `type`(policy·domain·convention·external·procedure, `adr/`는 adr) 둘만 두어 문서 한 장이 유형 1개 × 주제 1개를 지키게 하고, 발견 레포와 교체 전후 값은 위키 커밋 메시지에 남기며, 전체 공통 폴더는 두지 않고 레포는 한 도메인에만 속합니다. 레포 소관·레포 책임·owner·의존은 문서가 아니라 노드와 간선에 둡니다. 노드에는 다른 레포가 자기 코드에 적는 이름을 두지 않으므로, 간선의 상대는 조인 표가 아니라 식별자에서 읽히는 slug와 상대 레포 코드 확인으로 정하고, `from`은 선언이 실제로 있는 레포이며, registry 밖 시스템에는 간선 대신 책임 문장이 소재를 밝힙니다. 문서 규격과 사실 판정 기준은 `references/doc-contract.md`, 노드·간선의 판단 기준은 같은 문서 9·10장에 있고 스킬 실행 시에만 읽힙니다. 필드 스키마·상한·간선 종류 정의는 문서가 아니라 `python3 scripts/graph.py schema --for survey|facts [--lane {레인}]` 출력이 정본이며, 조사·추출 스킬이 서브에이전트 프롬프트에 그대로 싣습니다. register의 누락 대조 분모는 `scripts/survey.py inventory`가 냅니다.

## 무인 갱신 범위

- **선택**: 도메인·레포 구분 없이 미처리 머지(PR 단위)를 머지 시각 순으로 세워 전역 40건(`--max-merges`)만큼 처리 — 사용자에게 묻지 않으며 `--repo`·`--range`는 지목 실행용
- **대상**: `.local/paths.json`에 로컬 경로가 있고 `status`가 `active`인 등록 레포만 — 그 레포에서 세션을 한 번 열면 훅이 경로를 기록함
- **범위**: 커서부터 대상 브랜치까지의 first-parent 커밋 — 추출은 레포 안에서 머지 5건 또는 diff 500KB 중 먼저 닿는 묶음 단위로 서브에이전트 1회씩(diff 1건은 400KB에서 절단)
- **권한**: 새 사실은 추가, 기존 값과 다른 사실은 plan·feedback·커밋 메시지에서 의도가 인용될 때만 교체하고 나머지는 건너뛰어 최종 보고의 건너뜀 표에 남김 — 시각 순은 적용 순서만 정하며, 건너뛴 행은 `/llm-wiki:add`로 처리

## 한계

- **slug 충돌**: 레포 판정이 owner를 보지 않아 다른 owner의 같은 이름 레포가 한 slug로 잡힘 — register가 `{domain}-{name}`을 제안함
- **diff 절단**: 400KB를 넘는 머지 diff는 잘려 뒷부분의 사실이 빠질 수 있음(프런트 레포에 집중)
- **직접 커밋 레포**: PR 없이 기본 브랜치에 직접 커밋하는 레포는 first-parent 단위가 커밋 하나가 되어 예산이 무의미함 — `status: dormant`로 둠
- **건너뜀 보존**: 건너뛴 행은 위키에 파일로 남지 않고 실행의 최종 보고에만 실리므로, 무인 실행의 건너뜀은 그 보고를 받아 `/llm-wiki:add`로 넘겨야 함

## 3.x에서 이관

4.0.0은 노드 스키마(`domains.{d}.repos.{slug}` 중첩, `remote`·`defaultBranch`·`responsibilities`·`hosts`·`project`, `dormant`)와 합의 모델(등급·출처·`verified`·낡음·`inbox/` 폐지)이 바뀌어 3.x 위키는 `graph.py check`에서 에러가 납니다. 설치 후 아래 순서로 옮깁니다.

- **노드·간선**: 등록 레포마다 그 레포에서 `/llm-wiki:register --resurvey`
- **inbox**: `inbox/{domain}.md`의 남은 행을 `/llm-wiki:add`로 처리한 뒤 `inbox/` 삭제
- **frontmatter**: 문서의 `updated`·`verified`·출처 줄은 `/llm-wiki:audit`로 정리

## 4.x에서 이관

5.0.0은 문서 frontmatter에 `type`을 필수로 더해 4.x 위키는 `catalog.py --check`에서 문서마다 `type 없음` 에러가 나고, update는 이 에러가 있으면 audit 안내 후 중단합니다. 설치 후 아래 순서로 옮깁니다.

- **유형 부여**: 도메인마다 `/llm-wiki:audit` — `유형` 조치가 승인 없이 type을 붙이고, 한 문서에 유형이 섞였으면 `분할 후보`로 보고
- **목록 확인**: 이관 전에는 세션 목록 행이 `[?]`로 나오며 문서는 빠지지 않음
