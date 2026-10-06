# 개인판·사내판 플러그인 3종 공통 본문·고유 파일 분리와 버전 정합

## 의도

- **왜**: 사내판 devcenter-pr·devcenter-flow·devcenter-comms가 개인판 pr-workflow·plan-workflow·better-communication과 파일 단위로 갈라져 있음. 플러그인 이름·기록 경로·Bitbucket 절차가 본문 곳곳에 섞여 있어, 개인판을 개선할 때마다 사내판으로 옮기려면 수작업 병합이 필요함
- **누가**: 사용자 본인이 개인판 플러그인을 고친 뒤 사내판으로 미러링할 때 겪음
- **완료**: 플러그인마다 사내 고유 파일 목록이 정해지고 그 밖의 파일은 개인판과 바이트 동일함(`diff -rq` 결과에 고유 파일만 나옴). 양쪽 `plugin.json` version이 같고, 미러링 절차가 사내판 README에 기록된 상태

## 배경

- **경로**: 개인판 `/Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market`(GitHub, 기본 브랜치 `main`, PR 머지 관례), 사내판 `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace`(Bitbucket, `master` 직접 커밋 관례, 2026-10-06 기준 `7ce5de2` 1커밋 미푸시)
- **대응**: `pr-workflow` ↔ `plugins/devcenter-pr`, `plan-workflow` ↔ `plugins/devcenter-flow`, `better-communication` ↔ `plugins/devcenter-comms`, `agent-wiki` ↔ `plugins/agent-wiki`
- **agent-wiki 선례**: 공통 본문은 바이트 동일하고 사내 고유 파일은 `config.json`·`references/publish.md`·`README.md` 3개임. 스킬은 "`publish.md` 2장"처럼 고유 파일을 장 번호로 참조해 조합하며, 절차는 사내판 `plugins/agent-wiki/README.md`의 `## 미러링` 절에 있음
- **현재 차이**: pr은 13개 파일 전부, flow는 10개 중 `hooks/hooks.json`을 뺀 9개가 다름. comms는 `plugin.json`·`README.md`·`hooks/user_prompt_submit.sh` 3개와 사내 전용 `NOTICE`가 다름
- **이름 고정 사유**: 사내 cms·devcenter 25개 레포 develop의 공유 `.claude/settings.json`이 `devcenter-flow@onestore-devcenter`·`devcenter-comms@onestore-devcenter`·`devcenter-pr@onestore-devcenter`·`agent-wiki@onestore-devcenter`를 켬
- **버전 이력**: 개인판은 pr 1.0.0·flow 1.2.0·comms 1.0.0임. 사내판 pr은 2.0.0~3.0.1, flow는 1.0.0~3.0.1(사내 marketplace 항목에 3.1.0이 한때 기재됨), comms는 2.0.0~4.0.0을 거쳤음
- **캐시 구조**: 플러그인 캐시가 `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/` 폴더 단위라서, 과거 버전 번호를 재사용하면 옛 본문이 로드될 수 있음
- **위키 어휘**: agent-wiki 세션 주입은 레포 전용 문서·도메인 공유 문서 목록이며 `!` 미검증 표시나 '스페이스' 구분이 없음. 사내판 devcenter-pr의 `!`·`그룹 스페이스`·`레포 스페이스` 문구는 제거된 devcenter-wiki 시절의 어휘임
- **치환 선례**: `plan-workflow/hooks/session_start.sh`가 `rules/agent-guide.md`의 `{PLUGIN_ROOT}`를 이미 치환함

## 확정 결정 (사용자 확인 2026-10-06)

- **범위**: 구조 개편·버전 정합만 수행하고, 그 과정에서 드러난 낡은 문구(사내판 Layer 2의 devcenter-wiki 어휘)만 함께 정리함
- **이름**: 사내판 플러그인 이름은 유지하고, 공통 본문에서는 플러그인 이름을 제거함
- **공통 승격**: 위키 연동(pr review의 Layer 2, planning의 위키 대조, execute의 위키 문서 선행 읽기, record-format의 위키 편입 안내)과 이슈 키 slug 규칙(Jira 예시를 일반 이슈 키 `PROJ-123`으로 바꿈)을 공통 본문에 넣어 개인판에도 반영함
- **사내 고유 유지**: comms의 `NOTICE`와 typescript-react 체크리스트의 lint 제외 절은 사내판에만 둠. lint 제외 절은 공통 체크리스트에서 빼서 사내 devcenter-pr README로 옮김
- **버전**: pr-workflow·devcenter-pr 3.1.0, plan-workflow·devcenter-flow 3.2.0, better-communication·devcenter-comms 4.1.0. 개인 marketplace `metadata.version`은 4.4.0, 사내 marketplace `version`은 5.1.0

## 외부 계약

- **설정 키**: 위 4개 `enabledPlugins` 키와 사내판 플러그인 `name`은 변경 금지
- **코멘트 접두사**: `[AI 리뷰]`·`[AI 코드리뷰]`·`[AI 반영]` 접두사와 요약 상태 줄(`리뷰 스냅샷: <SHA>`)은 기존 PR 코멘트와의 호환 계약이므로 한 글자도 변경 금지
- **주입 제목**: 스킬이 참조하는 세션 주입 제목 `## 현재 워크스페이스`와 규약 제목 `작업 기록 규약`은 유지함

## 선행 읽기

- 사내판 `plugins/agent-wiki/README.md` `## 미러링` 절: 고유 파일 표와 버전 규칙의 형식 원본
- 개인판 `agent-wiki/skills/update/SKILL.md` 7행: 고유 절차 파일을 장 번호로 참조하는 문장 형식
- `~/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/plugin-authoring.md`: plugin.json·marketplace.json 버전 올림 규칙
- 짝별 `diff -r`(개인판 플러그인 폴더와 사내판 플러그인 폴더): 편집 전 줄 단위 차이 확인용. 사내판 원문은 rsync 이후에도 `git -C <사내판> show HEAD:<경로>`로 조회 가능

## 작업

### 공통 규칙 (3종)

- **고유 파일**: `.claude-plugin/plugin.json`(name·description·author·keywords는 고유하고 version은 개인판과 같음), `README.md`, 그리고 플러그인별 고유 파일(아래 절)
- **원본 방향**: 그 밖의 파일은 개인판이 원본이며, 사내판은 rsync로 덮어씀
- **공통 파일 금지어**: 플러그인 이름, 사내 경로(`.devcenter/…`), Bitbucket 도구명(`bitbucket_*`), 개인판 경로 상수(`.ai-docs/…`)
- **이름 지칭**: 훅이 주입하는 텍스트는 `plugin.json`의 `name`을 읽어 치환함. 스킬·참조 문서는 "이 플러그인의 `review` 스킬"로 지칭하고, 사용자에게 안내할 명령은 "이 스킬을 부른 이름의 콜론 앞부분"으로 조립하게 함
- **문구 충돌**: 기본은 개인판 문구를 따름. 사내판에만 있는 환경 무관 지침 5개는 공통 본문에 넣음
  - ① pr-protocol의 fix 2승인 근거 문장
  - ② pr-protocol의 재시도 금지 근거 절("추측으로 성공한 조회가 엉뚱한 저장소를 가리키는 것이 실패보다 나쁨")
  - ③ create의 `관례 비참조`
  - ④ create의 기록 폴더 gitignore 시 직접 읽기
  - ⑤ review-comment의 "플러그인 이름이 바뀌어도 접두사는 그대로"
- **환경 문장**: 사내 환경에 묶인 문장은 고유 파일(`host.md`·`config.json`·README)로 옮김

### better-communication ↔ devcenter-comms

고유 파일: `plugin.json`, `README.md`, `NOTICE`(사내판만)

| 파일 | 변경 | 사다리 |
|---|---|---|
| `better-communication/hooks/user_prompt_submit.sh` | REMINDER를 `COMMUNICATION RULES ACTIVE: 세션 시작에 주입된 산출물 작성 규약을 그대로 따릅니다.`로 바꿔 플러그인 이름 제거 | ⑥ 한 줄 |
| `better-communication/.claude-plugin/plugin.json` | version 4.1.0 | ⑥ 한 줄 |

- **이름 비치환 근거**: UserPromptSubmit 훅은 매 프롬프트마다 실행되므로, plugin.json을 파싱하려고 python을 기동하는 비용을 더하지 않음

### plan-workflow ↔ devcenter-flow

고유 파일: `plugin.json`, `README.md`, `config.json`(신규)

| 파일 | 변경 | 사다리 |
|---|---|---|
| `plan-workflow/config.json` | 신규 `{"workspace": {"root": ".ai-docs/workspace"}}`, 사내판은 `".devcenter/workspace/progress"` | ② agent-wiki `config.json` 선례 |
| `plan-workflow/hooks/session_start.sh` | `config.json`의 `workspace.root`와 `.claude-plugin/plugin.json`의 `name`을 읽어 아래 변경을 적용 | ② 기존 `{PLUGIN_ROOT}` 치환 확장 |
| `plan-workflow/hooks/post_exit_plan.sh` | REMINDER를 `계획 핸드오프: 계획이 승인되었습니다. 이 세션은 구현을 시작하지 않습니다 — planning 스킬 7절대로 plan.md·feedback.md 스냅샷을 커밋하고 새 세션에서 이 플러그인의 execute 스킬로 시작하도록 안내한 뒤 턴을 끝냅니다.`로 바꾸고, 주석의 플러그인 이름도 제거 | ⑥ 한 줄 |
| `plan-workflow/rules/agent-guide.md` | `.ai-docs/workspace/{slug}/`를 `{WORKSPACE_ROOT}/{slug}/`로, `/plan-workflow:`를 `/{PLUGIN_NAME}:`으로 바꿈 | ⑥ 한 줄 |
| `plan-workflow/references/plan-format.md` | 첫 문단의 경로를 "세션 `## 현재 워크스페이스` 블록의 기록 폴더에 있는 `plan.md`"로 바꾸고, `## 선행 읽기` 항목에 사내판의 위키 카탈로그 문장을 넣음 | ⑥ 한 줄 |
| `plan-workflow/references/record-format.md` | 경로는 위와 같이 처리하고, `source:` 정의를 "그 사실을 정한 문서(기획서·규격서의 이름과 판본, 이슈 키, 정책 문서) 또는 `사용자 확인 YYYY-MM-DD`"로 바꿈. 사내판의 `위키 편입` 불릿을 추가하고 템플릿 예시는 개인판 것을 유지 | ⑥ 한 줄 |
| `plan-workflow/skills/planning/SKILL.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `plan-workflow/skills/execute/SKILL.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `plan-workflow/README.md` | 기록 경로는 `config.json`의 `workspace.root` 값이고, slug는 이슈 키 우선이며, 위키 연동 줄을 추가함 | ⑥ 한 줄 |
| `plan-workflow/.claude-plugin/plugin.json` | version 3.2.0 | ⑥ 한 줄 |

#### session_start.sh

- **치환**: 기존 `{PLUGIN_ROOT}` 치환 옆에서 `{PLUGIN_NAME}`·`{WORKSPACE_ROOT}`도 치환함
- **경로 계산**: `os.path.join(project_dir, root, slug)`로 계산함
- **블록 추가**: `## 현재 워크스페이스` 블록에 ``- **기록 폴더**: `{root}/{slug}/` ``을 추가함. slug가 미확정이면 `{slug}` 자리표시자를 그대로 둠
- **명령 치환**: plan.md 있음 줄의 명령을 `/{name}:execute`·`/{name}:planning`으로 바꿈
- **slug 미확정 줄**: "요청·커밋에 이슈 키(`PROJ-123`)가 있으면 그 키, 없으면 작업 주제의 kebab-case 2~4단어로 폴더를 만들고 세션 안에서 바꾸지 않음"
- **실패 처리**: 기존 동작인 `2>/dev/null || exit 0`을 유지함

#### planning SKILL.md

- **description**: 경로를 "plan.md in the session's workspace folder"로, 다른 스킬 언급을 "this plugin's execute skill"로 바꿈
- **위키 문장**: `검색 선행`·`선택형`·`확정 조건`을 사내판 문장으로 바꿈
- **모드 판정**: 경로를 "워크스페이스 블록의 기록 폴더"로 바꿈
- **승인 후 순서**: ③을 "새 세션에서 이 플러그인의 execute 스킬(작업 기록 규약의 `계획` 항목에 적힌 명령)로 시작하도록 안내"로 바꿈

#### execute SKILL.md

- **변경 범위**: description, `위치` 경로를 기록 폴더 기준으로 바꾸고, `선행 읽기`는 사내판의 위키 카탈로그 문장으로 바꿈

### pr-workflow ↔ devcenter-pr

고유 파일: `plugin.json`, `README.md`, `references/host.md`(신규)

- **host.md 근거**: ⑦ 판정. 기존 `pr-protocol.md`는 호스트 무관 규약(승인 게이트·금지·보고·오류)과 호스트 절차가 한 파일에 섞여 있어, 그대로 고유 파일로 두면 공통 규약까지 판별로 갈라짐. agent-wiki `publish.md`처럼 호스트 절차만 떼어 장 번호로 참조하는 방식이 최소 분리임

#### host.md 장 구성

장 구성은 양 판이 같고 내용만 다름.

| 장 | 내용 | 개인판 원천 | 사내판 원천 |
|---|---|---|---|
| 1. 도구 | 사용할 PR 도구, 없으면 시작하지 않고 보고, 도구 이름 추측 금지 | pr-protocol `사전 조건`의 PR 호스트 도구·도구 부재 | pr-protocol `onestore MCP` 줄 |
| 2. 저장소 좌표·베이스 | 원본 저장소 좌표와 fork 판별, 베이스 브랜치 결정과 존재 확인 | pr-protocol 1절의 원본 저장소·베이스 브랜치 | pr-protocol 1절의 fork 판별·원본 판별·결과·`develop` 고정, create 3절의 `bitbucket_get_repository`·`bitbucket_get_branches` |
| 3. PR 조회 | OPEN 목록과 단건(소스·베이스·상태·인라인·최상위 코멘트) 조회 | "호스트 도구로" 문장 | `bitbucket_get_pull_requests(state="OPEN")`, `bitbucket_get_pull_request` |
| 4. diff 조달 | 상태별 로컬 fetch와 폴백 | review 1절의 로컬 diff·폴백 | review 1절의 OPEN(`refs/pull-requests/<id>/from`)·MERGED(머지 커밋)·폴백(`max_chars=500000`) |
| 5. 저장소 관례 | 리뷰어, PR 제목 관례, 리뷰 제외 경로 | create 3절의 "사용자가 지정한 경우에만, 추측 금지", 제목은 기존 PR 관례, 제외 경로 없음 | create 4절의 도출·관례·도출 불가, 제외 경로 `.devcenter/knowledge/**` |
| 6. push·생성·확인 | push 리모트, 거부 처리, 생성 파라미터, 생성 후 확인과 URL 보고 | create 6절 | create 7절, 가드레일 `크로스 fork 불가` |
| 7. 코멘트 게시 | 인라인 앵커 지정, 답글 방식, 게시 후 수정 가능 범위 | review-comment의 앵커·답글, "편집 불가 호스트가 있음" | review-comment의 `{path, line, line_type:"ADDED", file_type:"TO"}`·`parent_id`, MCP 편집·삭제·resolve 불가 |

#### 공통 파일 변경

| 파일 | 변경 | 사다리 |
|---|---|---|
| `pr-workflow/references/host.md` | 위 장 구성으로 신규 작성 | ⑦ (위 근거) |
| `pr-workflow/references/pr-protocol.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `pr-workflow/references/review-comment.md` | 호환 계약 문장에 공통 지침 ⑤를 넣음. suggestion_code·앵커·답글·처리 완료 제외 문장은 호스트 무관 문구로 바꾸고 "host.md 7장"을 참조 | ⑥ 한 줄 |
| `pr-workflow/references/subagent-prompts.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `pr-workflow/references/checklists/*.md` 4종 | 제목을 `# PR 리뷰 Layer 1 체크리스트 — …`로 바꾸고, 사내판의 `우선순위` 줄을 추가함. lint 제외 절은 넣지 않음 | ⑥ 한 줄 |
| `pr-workflow/skills/create/SKILL.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `pr-workflow/skills/review/SKILL.md` | 아래 변경 적용 | ⑥ 한 줄 |
| `pr-workflow/skills/fix/SKILL.md` | description에서 이름을 제거하고, 코멘트 조회는 "host.md 3장", 답글은 "host.md 7장"을 참조함. review 스킬은 "이 플러그인의 `review` 스킬"로 지칭 | ⑥ 한 줄 |
| `pr-workflow/README.md` | 리뷰 룰 2층과 `references/host.md`(호스트 절차) 안내를 추가 | ⑥ 한 줄 |
| `pr-workflow/.claude-plugin/plugin.json` | version 3.1.0 | ⑥ 한 줄 |

#### pr-protocol.md

- **사전 조건**: 저장소 체크아웃과 "도구는 `host.md` 1장"
- **1절**: `host.md` 2장의 결과(좌표 한 쌍·베이스 브랜치)를 쓰고, 확정하지 못하면 사용자에게 물음
- **2절**: 인자가 없을 때의 목록 조회는 `host.md` 3장을 따름
- **3절**: 편도 문장을 "코멘트 수정·삭제, PR 본문 편집, 스레드 resolve를 지원하지 않는 호스트가 있으므로"로 바꾸고 공통 지침 ①을 넣음
- **4절**: "approve·decline·merge 계열 도구"처럼 호스트 무관 문구로 씀
- **6절**: 공통 지침 ②를 넣음

#### subagent-prompts.md

- **호칭**: "pull request"로 씀
- **MATCHED_DOCS**: `{MATCHED_DOCS}` Layer 2 문장은 사내판 것을 쓰되 `!` 관련 문장은 제거함
- **rule 필드 예시**: `"L1:common.md" / "L2:{위키 문서 이름}"`
- **suggestion_code 근거**: "편집·삭제가 안 되는 호스트에서는 틀린 코드를 되돌리기 어려움"
- **lint 줄**: 개인판 문장을 유지함

#### create SKILL.md

- **절 구성**: 사내판 7절 구성을 따름
  - 3절 `원본 저장소·베이스 확인`은 `host.md` 2장
  - 4절 `리뷰어`는 `host.md` 5장
  - 7절 `push·생성·확인`은 `host.md` 6장
- **description**: 개인판 description에서 이름을 제거해 씀
- **기록 문서 줄**: "세션 작업 기록 규약의 기록 폴더 아래 `plan.md`·`feedback.md` 등"으로 쓰고 공통 지침 ④를 넣음
- **관례 비참조**: 공통 지침 ③을 넣음
- **핸드오프**: ``리뷰: /<플러그인>:review 실행``. `<플러그인>`은 이 스킬을 부른 이름의 콜론 앞부분임

#### review SKILL.md

- **description**: 이름을 제거하고 session-injected wiki docs를 언급함
- **1절**: `host.md` 3·4장을 따름
- **2절 스킵**: "작업 기록 문서(세션 기록 폴더 아래)와 `host.md` 5장의 리뷰 제외 경로"
- **3절**: Layer 1은 기존 스택 감지를 유지함. Layer 2는 "세션에 주입된 agent-wiki 문서 목록(레포 전용·도메인 공유 문서)에서 이 PR이 만지는 문서"를 고르고, 우선순위·카탈로그 부재·구 룰 파일 처리는 사내판 문장을 쓰되 '스페이스' 어휘는 제거함
- **보고**: `적용 룰 소스`에서 `!` 문장을 제거함
- **재리뷰 답글**: `host.md` 7장을 따름
- **다음 단계**: ``다음 단계: /<플러그인>:fix로 반영``

### 마켓플레이스·루트 문서

| 파일 | 변경 | 사다리 |
|---|---|---|
| 개인 `.claude-plugin/marketplace.json` | `metadata.version` 4.4.0 | ⑥ 한 줄 |
| 사내 `.claude-plugin/marketplace.json` | devcenter-pr `version` 3.1.0, devcenter-flow 3.2.0, devcenter-comms 4.1.0, 최상위 `version` 5.1.0 | ⑥ 한 줄 |
| 사내 `README.md` | devcenter-flow·devcenter-comms·devcenter-pr 절 끝에 agent-wiki 절과 같은 형식의 미러링 한 줄("개인 마켓플레이스 원본을 버전 그대로 미러링하며, 사내 고유 파일과 미러링 절차는 `plugins/<이름>/README.md`에 있습니다") | ⑥ 한 줄 |

### 사내판 미러링

1. **고유 파일 선작성**: devcenter-pr의 `references/host.md`(사내판 원천은 표의 사내판 열이며 `git show HEAD:`로 조회)와 devcenter-flow의 `config.json`을 작성함
2. **rsync**: 아래 명령을 실행함. 제외 경로는 덮어쓰지도 지우지도 않음

```bash
cd /Users/a1000377/Desktop/Projects/onestorecorp
rsync -a --delete --exclude=/.claude-plugin/plugin.json --exclude=/README.md --exclude=/references/host.md --exclude=.DS_Store my-claude-plugin-market/pr-workflow/ onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-pr/
rsync -a --delete --exclude=/.claude-plugin/plugin.json --exclude=/README.md --exclude=/config.json --exclude=.DS_Store my-claude-plugin-market/plan-workflow/ onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-flow/
rsync -a --delete --exclude=/.claude-plugin/plugin.json --exclude=/README.md --exclude=/NOTICE --exclude=.DS_Store my-claude-plugin-market/better-communication/ onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-comms/
```

3. **고유 파일 갱신**: 각 사내 `plugin.json`의 version을 올림
4. **README 미러링 절**: 각 사내 README에 `## 미러링` 절을 추가함. 형식은 agent-wiki README의 `| 구분 | 파일 | 원본 버전을 올릴 때 |` 표이고, 해당 rsync 한 줄과 "고유 절차 파일은 원본의 장 구성·키가 바뀌면 같은 구성으로 맞춤", "version은 원본과 같게" 규칙을 함께 적음
5. **lint 절 이동**: devcenter-pr README에 `## 체크리스트 관리` 절을 두고, 현재 사내 `typescript-react.md`의 `lint 설정 중복 제외 항목` 절을 그대로 옮김
6. **devcenter-flow README**: 기록 경로가 `config.json` 값이라는 문장을 추가함
7. **미러링 방식 근거**: 스크립트를 만들지 않고 README의 rsync 한 줄(⑥)로 처리함. agent-wiki도 수동 미러링으로 운영 중이고, 검증은 `diff -rq`로 충분함

## 커밋 분해

브랜치는 개인판 `feat/plugin-mirror-structure`(slug `feat-plugin-mirror-structure`)이고, 사내판은 `master`에 직접 커밋함.

| # | 범위 | 검증 |
|---|---|---|
| 1 | 개인 better-communication: reminder 중립화, 4.1.0 | `bash better-communication/hooks/user_prompt_submit.sh \| python3 -m json.tool`이 exit 0이고, 아래 금지어 grep의 better-communication 출력이 없음 |
| 2 | 개인 plan-workflow: `config.json`, 훅, 규약·참조·스킬, README, 3.2.0 | 아래 훅 스모크 결과 개인판 기대값 충족, `bash plan-workflow/hooks/post_exit_plan.sh \| python3 -m json.tool`이 exit 0, `claude plugin validate plan-workflow` exit 0, 금지어 grep 출력 없음 |
| 3 | 개인 pr-workflow: `host.md` 분리, 공통 본문, Layer 2, README, 3.1.0 | `claude plugin validate pr-workflow` exit 0, 금지어 grep 출력 없음, `grep -rnE "스페이스\|!대조함\|lint 설정 중복" pr-workflow` 출력 없음, `grep -rn "host.md" pr-workflow/skills pr-workflow/references/pr-protocol.md`에서 create·review·fix·pr-protocol 각 1건 이상 |
| 4 | 개인 marketplace.json 4.4.0 | `claude plugin validate .` exit 0 |
| 5 | 사내판 3종 미러링(사내 레포 `master`): 고유 파일, rsync, plugin.json·marketplace.json 버전, README | 아래 `diff -rq` 기대 출력과 일치, 버전 스크립트 4행 모두 `True`, 훅 스모크 결과 사내판 기대값 충족, 사내 레포 루트에서 `claude plugin validate .` exit 0 |
| 6 | 개인 feedback.md 최종 보충 | `git status --short`에 출력 없음 |

### 검증 명령

금지어 grep(개인판 루트, 출력 없음이 통과):

```bash
cd /Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market
grep -rniE "pr-workflow|plan-workflow|better-communication|devcenter|bitbucket|onestore|\.ai-docs|jira|DEFECT-|gh (pr|api|auth)|glab" pr-workflow plan-workflow better-communication --exclude=README.md --exclude=plugin.json --exclude=host.md --exclude=config.json --exclude=.DS_Store
```

훅 스모크(한 번의 Bash 호출로 실행):

```bash
cd /Users/a1000377/Desktop/Projects/onestorecorp
for root in my-claude-plugin-market/plan-workflow onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-flow; do
  for br in feat/x main; do
    t=$(mktemp -d); git -C "$t" init -q; git -C "$t" checkout -q -b "$br"
    echo "== $root $br"
    CLAUDE_PLUGIN_ROOT="$PWD/$root" CLAUDE_PROJECT_DIR="$t" bash "$root/hooks/session_start.sh" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])' \
      | grep -nE ":execute|기록 폴더|이슈 키|\{PLUGIN_NAME\}|\{WORKSPACE_ROOT\}"
    rm -rf "$t"
  done
done
```

- **개인판 기대값**: `/plan-workflow:execute`가 있고, `feat/x`에서 기록 폴더가 `.ai-docs/workspace/feat-x/`이며, `main`에서 `이슈 키` 줄이 있고, `{PLUGIN_NAME}`·`{WORKSPACE_ROOT}` 줄은 없음
- **사내판 기대값**: `/devcenter-flow:execute`가 있고 기록 폴더가 `.devcenter/workspace/progress/feat-x/`이며, 나머지 조건은 개인판과 같음

`diff -rq` 기대 출력:

```bash
cd /Users/a1000377/Desktop/Projects/onestorecorp
diff -rq -x .DS_Store my-claude-plugin-market/pr-workflow onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-pr
diff -rq -x .DS_Store my-claude-plugin-market/plan-workflow onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-flow
diff -rq -x .DS_Store my-claude-plugin-market/better-communication onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-comms
```

- **pr**: `.claude-plugin/plugin.json`, `README.md`, `references/host.md`의 differ 3줄만 출력
- **flow**: `.claude-plugin/plugin.json`, `README.md`, `config.json`의 differ 3줄만 출력
- **comms**: `.claude-plugin/plugin.json`, `README.md`의 differ 2줄과 `Only in …/devcenter-comms: NOTICE` 1줄만 출력

버전 스크립트(4행 모두 `True`가 통과):

```bash
python3 - <<'PY'
import json
P = "/Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market"
I = "/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace"
pairs = {"pr-workflow": "devcenter-pr", "plan-workflow": "devcenter-flow", "better-communication": "devcenter-comms", "agent-wiki": "agent-wiki"}
entries = {p["name"]: p.get("version") for p in json.load(open(f"{I}/.claude-plugin/marketplace.json"))["plugins"]}
for a, b in pairs.items():
    va = json.load(open(f"{P}/{a}/.claude-plugin/plugin.json"))["version"]
    vb = json.load(open(f"{I}/plugins/{b}/.claude-plugin/plugin.json"))["version"]
    print(a, va, b, vb, entries[b], va == vb == entries[b])
PY
```

## 특이 사항

- **agent-wiki 잔여**: agent-wiki는 변경하지 않음. 다만 개인판 공통 파일 `agent-wiki/skills/add/SKILL.md` 24행 예시에 사내 경로 `.devcenter/workspace/progress/*/feedback.md`가 남아 있음. 고치려면 agent-wiki 버전도 함께 올려야 하므로 후속 작업으로 둠
- **위키 갱신**: 위키 사본은 직접 수정하지 않음. 머지 후 `/agent-wiki:add`로 `internal-plugin-mirror` 문서(현재 agent-wiki만 다룸)를 4종 플러그인의 고유 파일 목록으로 확장하고, `plugin-authoring` 문서의 적용 대상도 보강하도록 제안함
- **NOTICE**: 개인판 better-communication은 사용자 결정에 따라 NOTICE 없이 유지함
- **의도적 단순화**: 미러링은 README의 rsync 한 줄과 `diff -rq` 확인으로 수동 수행하며 스크립트·CI는 두지 않음. 미러링 누락이 반복되면 사내판 레포에 검증 스크립트를 도입함
- **명령 조립 한계**: pr-workflow는 훅이 없어 스킬 본문이 "이 스킬을 부른 이름의 콜론 앞부분"으로 안내 명령을 조립함. 잘못 조립해도 안내 문구만 틀리고 동작에는 영향이 없음
- **버전 건너뜀**: 개인판 버전이 1.x에서 3.x·4.x로 건너뜀
- **재미러링**: 개인판 PR 리뷰로 공통 본문이 바뀌면 사내판 rsync를 다시 실행하고 미러링 커밋을 새로 남김
- **외부 쓰기 확인**: 개인판 push·PR 생성과 사내판 `master` push는 실행 시 사용자 확인 후 진행함. 사내판 push에는 미푸시 커밋 `7ce5de2`가 함께 올라감
- **팀원 반영**: 사내 마켓플레이스는 autoUpdate가 기본 꺼져 있어, 팀원은 `/plugin marketplace update onestore-devcenter`를 실행해야 새 버전을 받음
