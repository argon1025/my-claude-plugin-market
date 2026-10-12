# agent-wiki 세션 시작 위키 로드 상태 알림

## 의도

- **왜**: agent-wiki 세션 시작 훅은 위키 로드 결과(정상·미등록·위키 없음)를 에이전트 컨텍스트(`additionalContext`)에만 넣고 예외·생성기 실패·원격 최신화 실패는 출력 없이 끝내므로, 사용자는 위키 없이 답하는 세션인지 모른 채 작업을 진행함
- **누가**: agent-wiki를 켠 레포(개인판·사내판)에서 세션을 시작·재개·`/clear`·compact하는 사용자
- **완료**: 훅이 에이전트 턴 없이 위키 로드 상태를 고정 템플릿 알림(`systemMessage`)으로 사용자 화면에 띄우고, 개인판 agent-wiki와 사내판 미러에 반영되면 끝

## 배경

- **알림 수단**: Claude Code 2.1.296에서 SessionStart 훅이 한 JSON에 `systemMessage`와 `hookSpecificOutput.additionalContext`를 함께 내면 둘 다 처리되고, `systemMessage`는 모델 컨텍스트에 들어가지 않음(임시 플러그인 `claude -p --plugin-dir` 실험으로 확인). `systemMessage`도 별도로 10,000자 한도를 가짐
- **미확인**: 인터랙티브 CLI가 `systemMessage`의 줄바꿈을 그대로 렌더링하는지는 문서에 없음
- **동기화 일시 원천**: 위키 사본의 `.git/FETCH_HEAD` 수정 시각은 `sync_wiki.py`의 `git fetch`가 성공할 때마다 새 커밋이 없어도 갱신됨(2026-10-12 관찰). `git clone` 직후에는 이 파일이 없을 수 있음
- **현재 훅 흐름**: `agent-wiki/hooks/session_start.py`는 origin 판정 → (startup·resume·clear이고 `{baseRoot}/.git`이 있으면) `sync_wiki.py`를 최대 3초 대기 → registry 확인 → 색인 파일 쓰기 → 생성기 3종(`generate_wiki_rules.py`·`generate_repository_map.py`·`generate_document_list.py`) 출력 결합 순서이며, `sync_wiki.py`의 stdout(`ok` 또는 `fail {git 오류 한 줄}`)을 DEVNULL로 버리고 `generate()`는 실패·타임아웃을 빈 문자열로 돌려줌
- **사내판 미러**: 로컬 체크아웃 `~/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace`(master, origin과 일치)의 `plugins/agent-wiki`는 개인판과 `README.md`·`config.json`·`references/publish.md` 3파일만 다름. 두 README의 `## 세션 주입` 문단은 현재 같은 문장임
- **버전 현황**: 개인판 agent-wiki `plugin.json` 0.9.1, 개인판 `marketplace.json` `metadata.version` 4.6.0(플러그인 항목에 version 없음), 사내판 `marketplace.json` 최상위 `version` 5.3.0·agent-wiki 항목 0.9.1·`plugins/agent-wiki/.claude-plugin/plugin.json` 0.9.1

## 확정 결정 (사용자 확인 2026-10-12)

- **수단**: 세션 시작 알림(`systemMessage`)만 넣고 상태표시줄 연동과 에이전트 고지는 하지 않음
- **표시 상태**: 정상 로드를 포함한 전 상태를 표시함 — 알림이 없으면 훅이 돌지 않았다는 신호가 됨
- **표시 시점**: 훅이 도는 모든 시점(startup·resume·clear·compact)
- **고정 템플릿**: 첫 줄은 상태별 고정 문장, 그 아래에 해당 경고만 `- ` 줄로 붙임
- **미적용 문구**: "위키 플러그인을 비활성화합니다" 대신 "위키를 적용하지 않습니다"를 쓰고, 위키 없음은 "위키 초기 구성을 진행하지 않았습니다 … 먼저 /agent-wiki:init … 위키 초기 세팅을 진행하세요" 형태로 안내함
- **3초 초과**: 별도 지연 경고를 두지 않고 최신화 실패로 통합해 "3초 초과, 이전 사본으로 로드함"으로 표시함
- **일시 형식**: `10월 12일 10:11`
- **문구 확정**: `## 외부 계약` 절의 첫 줄·경고 줄 문구를 사용자 노출 문구 전부로 확정함
- **유지**: `additionalContext` 주입 문구는 바꾸지 않고, git 밖·origin 없는 폴더는 지금처럼 아무것도 출력하지 않음

## 외부 계약

훅 stdout JSON(키는 값이 있을 때만 넣음):

```json
{"systemMessage": "<알림>", "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<주입>"}}
```

알림 문구(사용자 노출 문구 전부, 이 문자열 외에 만들지 않음):

| 상태 | 첫 줄 |
| --- | --- |
| 정상 로드 | `{domain}/{slug} 프로젝트 위키가 로드되었습니다. (도메인 문서 {n}건 · 프로젝트 전용 문서 {m}건 · 위키 동기화 {M}월 {D}일 {HH:MM})` |
| 정상 로드, FETCH_HEAD 없음 | 위 문장의 괄호 끝 항목을 `위키 동기화 기록 없음`으로 씀 |
| 주입 블록 3종 모두 실패 | `{domain}/{slug} 프로젝트 위키를 로드하지 못했습니다.` |
| 미등록 레포 | `알 수 없는 프로젝트({slug})입니다. 위키를 적용하지 않습니다. 프로젝트는 /agent-wiki:register를 통해 등록하세요` |
| 위키 없음 | `위키 초기 구성을 진행하지 않았습니다. 위키를 적용하지 않습니다. 먼저 /agent-wiki:init을 실행해 위키 초기 세팅을 진행하세요` |
| 예외 | `위키를 로드하지 못했습니다.` |

| 경고 줄 | 조건 |
| --- | --- |
| `- 위키 최신화 실패 : {sync_wiki.py 출력에서 fail 뒤 git 오류 한 줄}` | 동기화가 3초 안에 비0으로 끝남 |
| `- 위키 최신화 실패 : 3초 초과, 이전 사본으로 로드함` | 동기화가 3초 안에 끝나지 않음 |
| `- 위키 세션훅 주입 한도 초과 상태({n:,}자 / 10,000자), 문서를 정리하세요` | 결합한 주입 문자열 길이 10,000자 초과 |
| `- 위키 작동 실패 : {실패 항목을 ·로 이음} 생성 실패` | 항목명과 나열 순서는 `위키 규칙`·`레포 지도`·`문서 목록`(주입 생성기)·`색인 파일`(--full 생성기 실패 또는 색인 쓰기 OSError) |
| `- 위키 작동 실패 : {예외 클래스명}: {메시지 첫 줄, 200자 이내}` | 예외 상태에서만 |

- **경고 순서**: 최신화 실패 → 주입 한도 초과 → 작동 실패
- **경고 적용**: 최신화 실패는 정상·블록 전부 실패·미등록 상태에 붙고(동기화 뒤 판정이므로), 위키 없음 상태에는 동기화가 돌지 않아 붙지 않음
- **문서 수**: 도메인 문서는 `knowledge/{domain}/*.md` 파일 수, 프로젝트 전용 문서는 `knowledge/{domain}/{slug}/*.md` 파일 수(없으면 0건)

## 선행 읽기

- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/session-start-hook.md` — 훅의 origin 선판정·3초 대기·주입 한도 규칙
- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/plugin-authoring.md` — 버전 올림 규칙
- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/internal-plugin-mirror.md` — 사내판 미러링 규칙(고유 3파일)
- `.ai-docs/workspace/wiki-load-status/feedback.md` — 이 작업의 확인된 의도·제약

## 작업

| 파일 | 변경 | 사다리 |
| --- | --- | --- |
| `agent-wiki/hooks/session_start.py` | `main()`이 `(주입, 알림)`을 돌려주고 출력부가 두 키를 함께 냄, 동기화 결과·생성기 실패·주입 길이·문서 수·FETCH_HEAD 시각으로 알림 조립 | ⑦ 훅만이 상태를 알고 Claude Code에 상태 표시 기본 기능이 없음, 기존 함수 수정으로 처리 |
| `agent-wiki/README.md` | `## 세션 주입` 문단 끝에 알림 문장 추가 | ⑥ |
| `agent-wiki/.claude-plugin/plugin.json` | version 0.9.1 → 0.10.0 | ⑥ |
| `.claude-plugin/marketplace.json` | `metadata.version` 4.6.0 → 4.7.0 | ⑥ |
| 사내 `plugins/agent-wiki/hooks/session_start.py` | 개인판 파일 복사 | ① 복사 |
| 사내 `plugins/agent-wiki/README.md` | 개인판과 같은 문장만 추가(사내 고유 파일) | ⑥ |
| 사내 `plugins/agent-wiki/.claude-plugin/plugin.json`, 사내 `.claude-plugin/marketplace.json` | 0.10.0, 최상위 5.3.0 → 5.4.0, agent-wiki 항목 0.10.0 | ⑥ |

### agent-wiki/hooks/session_start.py

- **파일 머리 주석**: "어떤 실패에서도 출력 없이 종료 코드 0으로 끝낸다"를 "어떤 실패에서도 종료 코드 0으로 끝내고, 로드 상태와 실패는 사용자 알림(systemMessage)으로 알린다"로 바꿈
- **`sync_wiki`**: `stdout=subprocess.PIPE, text=True`로 바꾸고 `communicate(timeout=3)`로 기다려, 성공이면 `None`, 비0이면 출력에서 `fail ` 접두를 뗀 한 줄(비면 `exit {코드}`), `TimeoutExpired`면 `3초 초과, 이전 사본으로 로드함`을 돌려줌. 타임아웃 뒤 자식은 죽이지 않음(현 동작 유지) — 부모 종료 뒤 자식의 마지막 `print`가 닫힌 파이프에 쓰여 실패해도 git 작업은 이미 끝난 시점이라 영향 없음
- **`generate`**: 실패·타임아웃이면 `None`, 성공이면 strip한 stdout을 돌려줌 — 정상 빈 출력과 실패를 구분하기 위함
- **`main`**: 반환을 `(text, message)` 튜플로 바꿈. git 밖·origin 없음은 `("", "")`. 위키 없음·미등록은 기존 주입 한 줄과 외부 계약 절의 첫 줄을 돌려줌. 정상 흐름은 `--full` 생성기 중 `None`이 있거나 `write_index`가 `OSError`면 `색인 파일`을 실패 항목에 넣고, 주입 생성기 3종을 `위키 규칙`·`레포 지도`·`문서 목록` 이름과 짝지어 `None`인 이름을 실패 항목에 넣음. 결합 주입이 비면 "로드하지 못했습니다" 첫 줄을 씀
- **알림 조립**: 문서 수는 `sum(f.is_file() for f in folder.glob("*.md"))`(폴더 없으면 0), 동기화 일시는 `datetime.fromtimestamp((base / ".git" / "FETCH_HEAD").stat().st_mtime)`을 `f"{t.month}월 {t.day}일 {t:%H:%M}"`로 쓰며 `OSError`면 `위키 동기화 기록 없음`. 경고는 외부 계약 절의 순서로 `- ` 줄을 붙여 `\n`으로 이음
- **`__main__`**: 예외면 `text=""`, `message="위키를 로드하지 못했습니다.\n- 위키 작동 실패 : {type(e).__name__}: {첫 줄[:200]}"`. 출력 JSON은 `message`가 있으면 `systemMessage`, `text`가 있으면 `hookSpecificOutput`을 넣고 둘 다 없으면 출력하지 않음
- **줄바꿈 대체**: 커밋 1 검증 V0에서 인터랙티브 CLI가 줄바꿈을 렌더링하지 않으면 경고 줄 구분자를 `\n- `에서 ` · `로 바꾸고 이 사실을 `feedback.md`에 `correction`으로 남김

### agent-wiki/README.md

- `## 세션 주입` 문단 끝에 다음 문장을 덧붙임: "세션마다 위키 로드 상태(로드 여부, 도메인·프로젝트 전용 문서 수, 위키 동기화 일시, 최신화 실패·주입 한도 초과·작동 실패 경고)를 사용자 화면 알림으로 띄우며, 이 알림은 에이전트 컨텍스트에 들어가지 않습니다."

## 커밋 분해

브랜치는 `wiki-load-status`(기록 폴더 slug와 같게)로 main에서 만듦. 검증 스크립트는 zsh 제약 때문에 scratchpad의 bash 파일로 만들어 `bash {파일}`로 실행하고, 위키 사본 변형은 `cp -R ~/.agent-wiki {scratch}/wiki`와 `config.json`만 바꾼 플러그인 복사본(`cp -R agent-wiki {scratch}/plugin`)에서 함.

| # | 범위 | 검증 |
| --- | --- | --- |
| 1 | `agent-wiki/hooks/session_start.py` | V0·V1 전 항목 통과 |
| 2 | `agent-wiki/README.md`, `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `python3 -m json.tool`이 두 JSON을 오류 없이 출력, `grep -n '"version"' agent-wiki/.claude-plugin/plugin.json`이 0.10.0, `metadata.version`이 4.7.0 |
| 3 | 사내 레포 미러 커밋(push는 실행 시점에 사용자 확인 후) | `diff -rq {사내}/plugins/agent-wiki agent-wiki` 출력이 `README.md`·`config.json`·`references/publish.md` 세 줄뿐, 사내 README `## 세션 주입` 문단이 개인판과 같음, 사내 marketplace 최상위 5.4.0·agent-wiki 항목 0.10.0, V2 통과 |

- **V0 줄바꿈 렌더링**: scratchpad 임시 플러그인(`sysmsg-test`)의 훅을 두 줄 `systemMessage`(첫 줄 + `- ` 경고 줄)로 바꾸고 사용자에게 `claude --plugin-dir {sysmsg-test 경로}`로 세션을 열어 두 줄이 따로 보이는지 확인받음. 결과에 따라 `### agent-wiki/hooks/session_start.py`의 줄바꿈 대체 규칙 적용
- **V1 훅 단독 실행**: 각 케이스에서 `echo '{"source":"…"}' | CLAUDE_PROJECT_DIR=… python3 {플러그인}/hooks/session_start.py` 출력 JSON을 `python3 -c`로 파싱해 확인
  - 정상: 이 레포, startup → `systemMessage` 첫 줄이 `personal-claude-tooling/my-claude-plugin-market 프로젝트 위키가 로드되었습니다. (도메인 문서 `로 시작하고 경고 줄 없음, `additionalContext`가 main 브랜치 훅 출력의 `additionalContext`와 바이트 단위로 같음
  - compact: `{"source":"compact"}` → 같은 첫 줄, FETCH_HEAD 시각이 바뀌지 않음
  - 미등록: origin이 `https://example.com/x/foo-api.git`인 임시 git 레포 → `알 수 없는 프로젝트(foo-api)입니다. …` 
  - 위키 없음: `wiki.baseRoot`를 없는 경로로 둔 플러그인 복사본 → `위키 초기 구성을 진행하지 않았습니다. …`
  - 최신화 실패: 위키 사본 복사본 + `wiki.remote`를 `https://invalid.invalid/x.git`로 둔 플러그인 복사본 → `- 위키 최신화 실패 : fatal: …` 줄
  - 3초 초과: 연결을 받고 응답하지 않는 로컬 소켓(`python3 -c` 백그라운드, 127.0.0.1:8765)을 `wiki.remote`로 둠 → `- 위키 최신화 실패 : 3초 초과, 이전 사본으로 로드함` 줄, 훅 전체 실행 시간 3~5초
  - 주입 한도 초과: 위키 사본 복사본의 이 레포 전용 폴더에 긴 description 문서를 넣어 주입을 10,000자 넘김 → `- 위키 세션훅 주입 한도 초과 상태(…자 / 10,000자), 문서를 정리하세요` 줄
  - 생성기 실패: 플러그인 복사본의 `scripts/generate_document_list.py` 첫 줄 뒤에 `raise SystemExit(1)` → `- 위키 작동 실패 : 문서 목록·색인 파일 생성 실패` 줄
  - 예외: 플러그인 복사본의 `config.json`을 깨진 JSON으로 → `systemMessage`가 `위키를 로드하지 못했습니다.\n- 위키 작동 실패 : JSONDecodeError: …`, `hookSpecificOutput` 없음
  - git 밖: `CLAUDE_PROJECT_DIR=/tmp` → stdout 비어 있음
- **V2 사내 미러**: 사내 `plugins/agent-wiki/hooks/session_start.py`를 사내 위키에 등록된 레포 로컬 체크아웃(`~/Desktop/Projects/onestorecorp/` 아래)으로 `CLAUDE_PROJECT_DIR`를 두고 `compact`로 실행해 `systemMessage` 첫 줄이 `{domain}/{slug} 프로젝트 위키가 로드되었습니다.`로 시작함

## 특이 사항

- **범위 밖**: 상태표시줄 연동(플러그인은 메인 statusLine을 설정할 수 없음), 에이전트 고지, agent-wiki가 꺼졌거나 설치되지 않은 레포 감지(훅이 돌지 않아 알릴 주체가 없고, 다른 플러그인에 넣으면 플러그인 간 직접 지목 금지 규칙과 충돌함), 원격 최신화 실패를 에이전트 컨텍스트에도 알리는 것
- **의도적 단순화**: 동기화 일시는 별도 상태 파일 없이 FETCH_HEAD 수정 시각을 씀 — 위키 사본에서 누군가 직접 `git fetch`하면 그 시각이 표시되며, 별도 기록이 필요해지면 `sync_wiki.py`가 성공 시각을 `.local/`에 쓰는 방식으로 올림
- **문서 수 중복**: 문서 수 계산은 `generate_document_list.py`의 `doc_rows`와 같은 glob 규칙을 훅에 한 줄로 다시 씀 — 생성기 간 의존을 만들지 않는 기존 원칙(스크립트 하나 책임 하나) 우선
- **후속 작업**: 머지 뒤 위키 `session-start-hook` 문서에 알림 규칙(전 상태 표시·모델 컨텍스트 미포함·FETCH_HEAD 일시)을 `/agent-wiki:add`로 반영 제안
