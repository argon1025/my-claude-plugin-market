# share-context 플러그인 신설과 init 이관

## 의도

- **왜**: 기존 llm-wiki는 스크립트 4종(graph.py 704줄·catalog.py 387줄·update.py 356줄·view.py 118줄)과 `references/publish.md`·`references/doc-contract.md`를 스킬마다 장 번호로 교차 참조해 안내 프롬프트가 길고 수정 시 여러 스킬이 함께 깨짐
- **누가**: 플러그인 관리자는 규약·절차를 고칠 때, 팀원은 설치 직후 위키를 준비할 때 겪음
- **완료**: `share-context` 플러그인이 마켓에 추가되고 `/share-context:init` 한 번으로 config에 고정된 위키 저장소가 `~/.llm-wiki`에 준비되며, 위키 문서 구조(`registry.json`·`deps.json`·`knowledge/`)는 그대로이고 init은 스크립트·references 참조 없이 SKILL.md 하나로 완결됨

## 배경

- **대상 위키**: `https://github.com/argon1025/argon1025-llm-wiki.git`, 기본 브랜치 `main`, PUBLIC, 이미 `.gitignore`(`.local/`)·`deps.json`·`knowledge/`·`registry.json`·`state/` 보유
- **공개 레포**: 이 마켓 레포(`argon1025/my-claude-plugin-market`)는 PUBLIC이며 사내 변형(devcenter)은 사내 플러그인에서 URL을 별도 선언함
- **기존 init 동작**: `llm-wiki/skills/init/SKILL.md`는 clone URL 유무로 질문 분기, 새로 만들기(`git init`), 원격 없는 로컬 전용 모드, `publish.md` 1~4장 참조로 구성됨 — 요구사항 결과로만 참고하며 문구·구조는 재사용하지 않음
- **공존**: llm-wiki는 같은 `~/.llm-wiki`에서 update 시 `wiki-update/` 브랜치 전환·`stash`를 수행하므로 share-context가 같은 작업 트리를 공유함

### 원점 재검토 결과 (init 범위)

| 기존 요소 | 판정 | 근거 |
|---|---|---|
| clone·새로 만들기 선택 질문 | 폐지 | 위키 원격을 config에 고정 |
| 원격 없는 로컬 전용 모드 | 폐지 | 고정 원격 전제, 추적 브랜치 부재로 인한 pull 실패 분기도 함께 소멸 |
| `references/publish.md` | 폐지 | 저장소·기준 브랜치는 config.json `wiki` 객체로 대체, 동기화는 에이전트가 아는 git 명령 한 줄 |
| `catalog.py --check` 등 스크립트 | 미채용 | 골격은 JSON 리터럴 2개이고 기존 저장소는 clone만 하므로 검증 대상 없음 |
| 골격 `state/` | 제외 | update 전용 커서이며 update 이관 단계에서 결정 |
| 골격 `.gitignore`(`.local/`) | 유지 | llm-wiki와 같은 경로를 공유해 `.local/` 산출물이 생김 |
| SessionStart 훅 | 제외 | 세션 주입 이관 단계에서 설계 |

## 확정 결정 (사용자 확인 2026-09-29)

- **init 범위**: init은 위키 준비만 수행하고 레포 등록(register)은 다음 단계에서 별도 이관
- **init 방식**: init 스킬 + 빈 저장소 골격 — 경로 있으면 pull, 없으면 clone, clone 결과가 빈 저장소면 골격 작성·커밋·push, 스크립트 없음
- **위키 경로**: `~/.llm-wiki` 공유
- **위키 원격**: 이 레포 config.json에 `https://github.com/argon1025/argon1025-llm-wiki.git`을 저장하고, 사내 플러그인은 URL을 별도 선언
- **이관 원칙**: 위키 문서 구조(registry.json·deps.json·knowledge)는 유지, 기존 구현은 재활용·인용하지 않음, 에이전트가 익숙한 CLI(git)를 쓰고 엣지 케이스만 안내

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `share-context/.claude-plugin/plugin.json` | 신규 — name `share-context`, version `0.1.0`, author·keywords | ⑦ 플러그인 인식에 필수인 최소 매니페스트 |
| `share-context/config.json` | 신규 — `wiki.baseRoot`·`wiki.remote`·`wiki.baseBranch` 3키 | ⑦ 이후 훅(코드)과 스킬(에이전트)이 같은 값을 읽는 단일 정본, 사내 변형은 이 파일만 교체 |
| `share-context/skills/init/SKILL.md` | 신규 — 판정·골격·실패·보고 4절, 30줄 이내 | ⑦ 사용자 명시 호출 진입점이 필요하고 절차는 git 명령만으로 성립 |
| `share-context/README.md` | 신규 — 목적, 스킬 표(init 1종), 설치, 전제 조건(`git`), config 3키, 이관 현황(init 완료·register/세션 주입/update 예정) | ⑦ 마켓 README 표가 링크하는 문서 |
| `.claude-plugin/marketplace.json` | share-context 항목 추가(category `knowledge`, tags `wiki`·`knowledge`·`git`), metadata version `3.1.0`에서 `3.2.0` | ② 기존 항목 형식 그대로 |
| `README.md` | 설치 명령 한 줄과 플러그인 표 한 행 추가(요구 사항 `git`) | ② 기존 행 형식 그대로 |

### config.json

```json
{
  "wiki": {
    "baseRoot": "~/.llm-wiki",
    "remote": "https://github.com/argon1025/argon1025-llm-wiki.git",
    "baseBranch": "main"
  }
}
```

- **구조**: 위키 관련 값을 `wiki` 객체 하나로 묶고, 이후 단계의 설정도 같은 방식으로 용도별 최상위 객체를 추가함
- **키 표기**: `baseRoot`·`baseBranch`는 camelCase로 통일함

### skills/init/SKILL.md

- **frontmatter**: `name: init`, `disable-model-invocation: true`, description은 영문 한 문장(`Clone the configured wiki repo to the wiki root, or fast-forward it if already present.`)
- **도입**: `${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 3키를 읽고 git 명령은 `GIT_TERMINAL_PROMPT=0`으로 실행한다는 두 문장
- **판정 절**:
  - 경로 없음이면 `git clone {remote} {baseRoot}`
  - 경로 있음이면 `origin` URL이 `remote`와 같고 현재 브랜치가 `baseBranch`일 때만 `git -C {baseRoot} pull --ff-only origin {baseBranch}`, 어느 하나라도 다르거나 git 저장소가 아니면 아무것도 고치지 않고 두 값을 보고 후 중단 — llm-wiki가 같은 트리에서 브랜치를 바꿔 둘 수 있으므로 전환·stash 금지
  - clone 결과 커밋이 없는 빈 저장소면 골격 절로 진행
- **골격 절**: `registry.json` `{"domains": {}}`, `deps.json` `{"deps": {}}`, `knowledge/.gitkeep` 빈 파일, `.gitignore` `.local/` 4파일을 `baseBranch` 첫 커밋 `chore(init): 위키 골격`으로 만들고 `git push -u origin {baseBranch}`
- **실패 절**: 인증·네트워크 실패는 에러 핵심 한 줄과 함께 사용자가 직접 실행할 `! git clone {remote} {baseRoot}` 안내, pull 실패(로컬 변경·분기)는 해소하지 않고 보고, push 실패는 로컬 커밋 상태와 함께 보고
- **보고 절**: 위키 경로, 수행 결과(clone·pull·골격 생성), `git -C {baseRoot} log -1 --oneline` 한 줄
- **금지 사항**: 다른 파일 참조(references·scripts) 없음, 스킬 이름 외 다른 스킬 안내 없음(register는 아직 없음)

### plugin.json

- **키**: `name`·`description`·`version`·`author`(`argon1025`, `argon1025@gmail.com`)·`keywords` — 기존 플러그인과 같은 키 구성
- **description**: `공유 컨텍스트 — 고정 위키 저장소(registry.json·deps.json·knowledge)를 로컬에 준비하는 init 스킬, 세션 주입·레포 등록·문서 갱신은 순차 이관 예정`

## 커밋 분해

작업 전 `git switch -c feat/share-context-init`으로 브랜치를 만듦.

| # | 범위 | 검증 |
|---|---|---|
| 1 | `share-context/` 전체(plugin.json·config.json·skills/init/SKILL.md·README.md) — `feat(share-context): 플러그인 신설과 init 스킬` | `python3 -m json.tool share-context/.claude-plugin/plugin.json` 및 `python3 -m json.tool share-context/config.json` 종료 코드 0, `claude plugin validate ./share-context` 에러 0, `grep -rE 'references/|scripts/|llm-wiki:' share-context/skills` 출력 없음 |
| 2 | `.claude-plugin/marketplace.json`·`README.md` — `feat: share-context 마켓 등록 v0.1.0` | `python3 -m json.tool .claude-plugin/marketplace.json` 종료 코드 0, `claude plugin validate .` 에러 0 |
| 3 | 수동 E2E(커밋 없음) | ① 신규 clone: `~/.llm-wiki` 부재 상태에서 `claude --plugin-dir ./share-context` 세션으로 `/share-context:init` 실행 후 `test -f ~/.llm-wiki/registry.json` 성공 ② 재실행: 보고에 pull 결과(`Already up to date`) ③ 빈 저장소: 스크래치에 `git init --bare empty.git`을 만들고 config.json의 `wiki.remote`·`wiki.baseRoot`를 임시로 그 경로로 바꿔 실행한 뒤 `git -C {스크래치}/empty.git log --oneline`에 `chore(init): 위키 골격` 1건, 검증 후 config.json 원복을 `git diff --exit-code share-context/config.json`으로 확인 |

## 특이 사항

- **범위 밖**: register·SessionStart 주입·update·add·audit 이관, llm-wiki 플러그인 제거, 사내 변형 배포 설정
- **공존 한계**: llm-wiki와 share-context를 함께 설치하면 같은 `~/.llm-wiki`를 공유하므로, llm-wiki update가 `wiki-update/` 브랜치에 머문 상태에서 init은 pull하지 않고 보고만 함 — llm-wiki 제거 시점에 이 분기 재검토
- **골격 차이**: 빈 저장소 골격에 `state/`를 두지 않아 llm-wiki update가 같은 위키를 쓰면 `state/` 파일을 처음 만들 때 생성됨 — update 이관 단계에서 커서 저장 방식과 함께 결정
- **후속 작업**: 다음 이관 단계는 register 또는 SessionStart 주입이며, 주입 단계에서 "위키 없음 — `/share-context:init` 실행" 안내를 훅에 추가
- **승인 후 기록**: `.ai-docs/workspace/share-context-init/plan.md`에 이 계획을, `feedback.md`에 사용자 의도 `context`·고정 위키 트레이드오프 `why`·공개 레포와 공유 경로 `constraint`를 남겨 한 커밋으로 기록
