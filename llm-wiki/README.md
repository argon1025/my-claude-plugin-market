# llm-wiki

LLM 위키 플러그인입니다. 위키는 "지금 무엇이 참인가"를 답하는 현행 합의이며, 레포 밖에 공유할 사실과 코드에 없는 사실(레포 사이에 맞춰야 하는 값·방식, 정책, 결정 근거, 외부 계약, 함정)과 레포 그래프(노드·간선)를 별도 git 저장소에 모으고, 세션 시작 시 그 목록과 그래프를 주입합니다. 위키는 플러그인 저장소 밖에 있어 여러 머신과 팀원이 같은 저장소를 공유합니다.

| 스킬 | 트리거 예 | 역할 |
| --- | --- | --- |
| `/llm-wiki:init` | "위키 초기화", "위키 세팅" | 위키 clone 또는 생성, 원격 연결, 골격(`registry.json`·`deps.json`·`state/`·`knowledge/`) 생성 |
| `/llm-wiki:register` | "이 레포 위키에 등록", "도메인 이동" | 정본 remote를 판별하고 현재 레포를 4레인 병렬 조사로 노드·의존 간선 기록, 근거 없는 호스트는 질문, 도메인 선택, 상태 표 |
| `/llm-wiki:update` | "위키 업데이트", "머지 반영" | 전 도메인 미처리 머지를 시각 순으로 무인 반영 — 새 사실은 추가, 기존 값은 의도 인용이 있을 때만 교체, 나머지는 건너뛰어 PR 본문 사실 원장에 기록, 문서·커서 커밋을 PR로 올려 머지로 승인 |
| `/llm-wiki:add` | "위키에 정리해줘", "정책으로 기록해줘" | 건넨 자료·대화·update가 건너뛴 행의 사실을 반영, 기존 값과 다른 건은 두 값을 보이고 질문 한 라운드 |
| `/llm-wiki:audit` | "위키 정리", "중복 정리" | 조각·중복·과길이 description·위치·규약 위반을 승인 표 하나로 정리 |

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

- **python3·git**: 훅과 스크립트가 둘 다 씀 — `python3`가 없으면 훅이 실행되지 않아 주입이 없음
- **원격 저장소**: 원격이 없으면 로컬 전용으로 동작하며, `/llm-wiki:update`는 PR로 반영하므로 GitHub 원격과 `gh` 인증이 필요함

## 동작 방식

- **SessionStart**: `hooks/session_start.py`가 startup·resume·clear·compact·fork 모두에서 등록 레포에는 규약(`rules/agent-guide.md`) → 동기화 알림 → 레포 지도 → 문서 목록을, 미등록 레포와 git 밖에는 규약 대신 위키 경로·도메인 목록을 담은 짧은 블록만 주입함
- **동기화**: 위키에 `origin`이 있으면 startup·resume마다 `pull --ff-only`를 3초까지 기다리고 늦거나 실패하면 이전 사본으로 주입하며 알림, 쓰기 스킬은 `references/publish.md`대로 시작에 동기화하고 끝에 push 또는 update PR
- **그래프 파생**: 레포 지도(현재 도메인 레포의 책임과 현재 레포와의 의존 힌트)와 라이브러리를 거쳐 닿는 파급 대상(`(경유 {lib})` 1홉)은 저장하지 않고 `scripts/graph.py`가 `registry.json` 노드와 `deps.json` 간선에서 매번 계산함 — 노드 필드의 상한·열거도 같은 스크립트의 상수 하나에서 나와 `schema` 출력과 `check` 에러가 갈리지 않음
- **그래프 화면(디버깅용)**: `python3 scripts/view.py`가 노드·간선을 담은 자기완결 HTML을 `{wiki}/.local/graph.html`에 쓰고 macOS에서 염(`--out PATH`·`--no-open`) — 사람이 위키 데이터를 점검하는 용도라 세션 주입에 실리지 않으며 Cytoscape.js는 jsdelivr CDN에서 받음
- **주입 범위**: 레포 지도는 현재 도메인 레포 전수(책임 문장)와 현재 레포와 간선이 있는 다른 도메인 레포(소관 한 줄)를 행으로 두고 현재 레포와의 간선을 그 행 아래 힌트 줄(계약 식별자 포함)로 붙이고 나머지 도메인은 이름 한 줄로 접으며, 문서는 현재 도메인 루트 전수(레포 폴더 제외)와 현재 레포 폴더 전수이고, 규약은 다른 레포 코드로 본 저장소 옆 사본(`{상위 폴더}/{slug}`)이 있으면 그것을, 없으면 위키 전용 clone(`{wiki}/.local/repos/{slug}`)을 안내함 — 스택·호스트·remote·전체 간선과 다른 도메인은 에이전트가 `registry.json`·`deps.json`을 직접 읽음
- **레포 판정**: upstream(없으면 origin) URL을 정규화해 노드의 `remote`와 맞추고 실패하면 URL 마지막 경로 요소를 slug로 씀 — 개인 포크에서 열어도 같은 slug로 모이므로 노드에는 정본 remote만 둠
- **주입 용량**: 목록은 어떤 크기에서도 줄이지 않으며, Claude Code가 주입을 10,000자에서 경고 없이 자르므로 9,000자를 넘으면 맨 앞에 정리 권고 한 줄이 붙음

## 위키 구조

```
~/.ai-docs/wiki/                    # LLM_WIKI_ROOT
├── registry.json                   # register가 편집: 도메인과 레포 노드
├── deps.json                       # register·update·add가 편집: 레포 간 의존 간선
├── state/{slug}.json               # update만 편집: {"cursor", "at"}
├── .gitignore                      # .local/
├── .local/repos/{slug}             # 위키 전용 clone (미추적, update가 clone·fetch, 세션 에이전트도 사용)
└── knowledge/
    └── {조직}-{도메인}/             # 도메인 루트 — 레포 밖이 알아야 하거나 겪는 사실
        ├── adr/                    # 선택
        └── {레포 slug}/            # 레포 종속 — 그 레포 안에서만 관심 있는 세부와 레포 사정
            └── adr/                # 선택
```

위치 판정은 "레포 밖이 알아야 하거나 겪는 사실인가" 한 단계이며, 도메인 루트와 다른 한 레포의 사정은 그 레포 폴더에 이유와 함께 둡니다. 문서 frontmatter는 `description`과 `type`(policy·domain·convention·external·procedure, `adr/`는 adr) 둘만 두어 문서 한 장이 유형 1개 × 주제 1개를 지키게 하고, 발견 레포와 교체 전후 값은 위키 커밋 메시지에 남기며, 전체 공통 폴더는 두지 않고 레포는 한 도메인에만 속합니다. 레포 소관·레포 책임·의존은 문서가 아니라 노드와 간선에 둡니다. 문서 규격과 사실 판정 기준은 `references/doc-contract.md`, 노드·간선의 판단 기준은 같은 문서 9·10장에 있고 스킬 실행 시에만 읽힙니다. 필드 스키마·상한·간선 종류 정의는 문서가 아니라 `python3 scripts/graph.py schema --for survey|facts [--lane {레인}]` 출력이 정본이며, 조사·추출 스킬이 서브에이전트 프롬프트에 그대로 싣습니다.

## 무인 갱신 범위

- **선택**: 도메인·레포 구분 없이 미처리 머지(PR 단위)를 머지 시각 순으로 세워 전역 40건(`--max-merges`)만큼 처리 — 사용자에게 묻지 않으며 `--repo`·`--range`는 지목 실행용
- **대상**: `status`가 `active`인 등록 레포 — 로컬 체크아웃이 아니라 registry `remote`로 받은 위키 전용 clone의 `origin/{기본 브랜치}`를 읽음
- **범위**: 커서부터 대상 브랜치까지의 first-parent 커밋 — 추출은 레포 안에서 머지 5건 또는 diff 500KB 중 먼저 닿는 묶음 단위로 서브에이전트 1회씩(diff 1건은 400KB에서 절단)
- **권한**: 새 사실은 추가, 기존 값과 다른 사실은 plan·feedback·커밋 메시지에서 의도가 인용될 때만 교체하고 나머지는 건너뛰어 PR 본문 사실 원장에 남김 — 시각 순은 적용 순서만 정하며, 건너뛴 행은 `/llm-wiki:add`로 처리

## 변형 배포

- **분리 지점**: 변형 플러그인과 갈리는 곳은 저장소 절차 `references/publish.md` 한 파일과 스킬 네임스페이스(`/llm-wiki:`)·환경변수(`LLM_WIKI_`)·위키 기본 경로(`~/.ai-docs/wiki`) 문자열이며, 오버레이 폴더에 `overlay.json`(`{"replace": {"원문": "대체문"}}`)과 이 플러그인과 같은 상대 경로의 교체 파일(`.claude-plugin/plugin.json`은 얕은 병합)을 둠
- **생성**: 마켓플레이스 레포 루트에서 아래 명령으로 출력 폴더를 통째로 다시 만들며, 치환은 교체하지 않은 파일에만 걸림
- **실패 조건**: 치환 원문 적중 0건, 이 플러그인에 없는 교체 파일, README 외 교체 `.md`의 `##` 절 제목 불일치 중 하나라도 있으면 종료 코드 1로 멈추고 기존 출력은 그대로 둠 — 버전업으로 생긴 드리프트를 sync 시점에 드러냄

```
python3 tools/overlay.py --base llm-wiki --overlay {오버레이 폴더} --out {출력 플러그인 폴더}
```

## 한계

- **slug 충돌**: 레포 판정이 owner를 보지 않아 다른 owner의 같은 이름 레포가 한 slug로 잡힘 — register가 `{domain}-{name}`을 제안함
- **diff 절단**: 400KB를 넘는 머지 diff는 잘려 뒷부분의 사실이 빠질 수 있음(프런트 레포에 집중)
- **직접 커밋 레포**: PR 없이 기본 브랜치에 직접 커밋하는 레포는 first-parent 단위가 커밋 하나가 되어 예산이 무의미함 — `status: dormant`로 둠
- **건너뜀 보존**: 건너뛴 행은 위키 문서에 남지 않고 update PR 본문 사실 원장에만 실리므로 머지 뒤 `/llm-wiki:add`로 넘겨야 함
