# agent-wiki 비대상 세션 도메인 개요 주입과 로드 알림 단순화

## 의도

- **왜**: agent-wiki를 user 스코프로 전역 설치하는 사용자가 늘었지만 세션 시작 훅은 git 밖 폴더·origin 없는 레포에서 알림·주입 없이 끝나고 미등록 레포에는 등록 안내 한 줄만 주입하므로, 사용자는 위키 상태를 모르고 에이전트는 위키가 있다는 사실 자체를 모름
- **누가**: 위키 대상 레포 밖(문서 폴더, 홈, 미등록 레포 등)에서 세션을 여는 개발자와 기획자
- **완료**: 모든 세션이 등록 로드·비대상 개요 로드·실패 세 가지 중 하나의 알림을 띄우고, 비대상 세션은 도메인 개요를 주입받아 관련 질문에 위키 문서로 답할 수 있으면 끝

## 배경

- **현재 흐름**: `agent-wiki/hooks/session_start.py`의 `main()`은 origin 판정(없으면 `("", "")` 반환) → startup·resume·clear이고 `{baseRoot}/.git`이 있으면 `sync_wiki()` 최대 3초 → `registry.json` 없으면 위키 없음 → 도메인 조회 실패면 미등록 → 등록 레포 색인 쓰기·생성기 3종 결합 순서이며, 실패 첫 줄이 상태마다 다름(위키 없음·미등록·`{key} 프로젝트 위키를 로드하지 못했습니다.`·예외 `위키를 로드하지 못했습니다.`)
- **재사용 함수**: 같은 파일의 `source()`·`sync_wiki()`·`generate()`(실패·타임아웃이면 `None`)·`write_index()`·`notice(first, warnings)`·`synced_at(base)`를 그대로 씀
- **도메인 행 형식**: `agent-wiki/scripts/generate_document_list.py`의 다른 도메인 블록이 registry `domains`에서 `- {d} — {description}`(description 없으면 `- {d}`)로 씀
- **add 스킬**: `/agent-wiki:add`는 현재 레포 origin이 registry에 없으면 도메인을 AskUserQuestion으로 고르므로 비대상 세션에서도 쓸 수 있음
- **표시 이름 식**: `str("~" / project.relative_to(Path.home()))`가 홈은 `~`, 홈 아래는 `~/Documents/기획서`로 만들고, 홈 밖이면 `ValueError`이므로 절대 경로를 씀(Python 3.14.4에서 확인)
- **행동 문서**: 훅 동작을 서술하는 레포 내 문서는 `agent-wiki/README.md` 41행 `## 세션 주입` 문단뿐임
- **버전 현황**: `agent-wiki/.claude-plugin/plugin.json` 0.10.0, `.claude-plugin/marketplace.json` `metadata.version` 4.7.0

## 확정 결정 (사용자 확인 2026-10-14)

- **비대상 통합**: git 밖 폴더·origin 없는 레포·미등록 레포를 한 비대상 템플릿으로 합쳐 알림과 도메인 개요를 주입하며, `/agent-wiki:register` 안내는 origin이 있는 미등록 레포 알림에만 불릿 한 줄로 붙임
- **개요 범위**: 도메인 이름·description과 문서 폴더 경로만 주입하고 레포 summary는 넣지 않음
- **문서 탐색**: 색인 파일을 만들지 않고, 에이전트가 질문이 올 때 해당 도메인 문서 폴더를 `^description:`으로 grep하며 레포 책임은 `registry.json`에서 읽음
- **생성기 배치**: 신규 생성기 `generate_domain_overview.py` 하나가 비대상 주입 전체를 출력하고 기존 생성기 3종은 바꾸지 않음
- **최신화 범위**: 비대상 세션에서도 위키 최신화(최대 3초 대기)를 수행함
- **알림 첫 줄 3종**: 등록 로드·비대상 개요 로드·`위키 로드에 실패했습니다.`만 두고, 실패 원인과 조치는 모두 그 아래 불릿으로 붙임
- **실패 판정**: 주입할 내용이 없으면 실패이며 실패 시 주입하지 않음(위키 없음 때의 `# 위키 없음` 한 줄 주입도 제거), 최신화 실패·한도 초과·일부 생성 실패처럼 주입이 남으면 로드 첫 줄에 경고 불릿을 붙임
- **명령 표기**: 알림 불릿의 명령은 `'/agent-wiki:init'`처럼 작은따옴표로 감쌈
- **범위 밖**: 사내판 미러링은 별도 이슈로 진행함

## 외부 계약

훅 stdout JSON(키는 값이 있을 때만 넣음, 기존과 같음):

```json
{"systemMessage": "<알림>", "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<주입>"}}
```

알림 첫 줄(사용자 노출 문구 전부, 이 문자열 외에 만들지 않음):

| 상태 | 첫 줄 |
| --- | --- |
| 등록 레포 로드 | `{domain}/{slug} 프로젝트 위키가 로드되었습니다. (도메인 문서 {n}건 · 프로젝트 전용 문서 {m}건 · {동기화})` (기존과 같음) |
| 비대상 개요 로드 | `현재 프로젝트({label})는 위키 대상이 아닙니다. 도메인 개요만 로드되었습니다. (도메인 {k}개 · {동기화})` |
| 실패 | `위키 로드에 실패했습니다.` |

- **`{동기화}`**: 기존 `synced_at(base)` 출력(`위키 동기화 {M}월 {D}일 {HH:MM}` 또는 `위키 동기화 기록 없음`)
- **`{label}`**: origin이 있으면 slug, 없으면 `배경`의 표시 이름 식 결과
- **`{k}`**: registry `domains` 키 개수

불릿(`- ` 접두, `\n`으로 이음, 아래 순서):

| 불릿 | 조건 |
| --- | --- |
| `위키 최신화 실패 : {sync_wiki 결과}` | 동기화 실패·3초 초과(기존과 같음), 모든 상태 |
| `'/agent-wiki:init'을 실행해 위키 초기 세팅을 진행하세요` | `registry.json` 없음, 실패 |
| `위키에 등록된 도메인이 없습니다. 위키 대상 레포라면 '/agent-wiki:register'로 등록하세요` | registry `domains`가 빔, 실패 |
| `위키 세션훅 주입 한도 초과 상태({n:,}자 / 10,000자), 문서를 정리하세요` | 결합 주입 10,000자 초과, 등록·비대상 공통 |
| `위키 작동 실패 : {항목을 ·로 이음} 생성 실패` | 등록은 `위키 규칙`·`레포 지도`·`문서 목록`·`색인 파일`, 비대상은 `도메인 개요` |
| `위키 대상 레포라면 '/agent-wiki:register'로 등록하세요` | 비대상이고 origin 있음(로드·실패 모두) |
| `위키 작동 실패 : {예외 클래스명}: {메시지 첫 줄 200자 이내}` | 훅 예외, 실패 |

비대상 주입(`generate_domain_overview.py` 출력, `{base}`는 펼친 baseRoot 절대 경로):

```
# 위키 — 대상 외 프로젝트({label})

현재 프로젝트는 위키에 등록된 레포가 아니므로 이 프로젝트 전용 문서는 없습니다. 사용자가 아래 도메인의 서비스·기능·정책을 물으면 위키 문서를 근거로 답하고, 질문이 아래 도메인과 무관하면 위키를 읽지 않습니다.

- 질문에 맞는 도메인을 고른 뒤 그 도메인 문서 폴더를 하위 폴더까지 `^description:`으로 grep해 문서별 용도를 보고 맞는 문서를 읽으세요. 레포별 책임이 필요하면 `{base}/registry.json`에서 그 도메인의 `repos`를 봅니다.
- 문서끼리 다르면 한쪽을 고르지 말고 두 값을 함께 알리세요.
- 위키 폴더는 세션 시작마다 원격 기준으로 초기화되므로 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리고 `/agent-wiki:add`로 반영을 제안하세요.

## 도메인

`{base}/knowledge/{domain}/` — 도메인 공유 문서, 하위 `{slug}/` 폴더는 레포 전용 문서

- {domain} — {description}
```

## 선행 읽기

- `/Users/rok/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/session-start-hook.md` — 훅 규칙·함정(3초 대기, 주입 한도, 알림 구분자)
- `/Users/rok/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/plugin-authoring.md` — 버전 올림 규칙
- `.ai-docs/workspace/agent-wiki-non-target-session/feedback.md` — 이 작업의 확인된 의도·결정

## 작업

| 파일 | 변경 | 사다리 |
| --- | --- | --- |
| `agent-wiki/scripts/generate_domain_overview.py` | 신규, 비대상 주입 출력 | ⑦ 주입 블록마다 생성기를 두는 기존 구조이고 등록 레포 생성기 3종은 레포 키를 전제로 함 |
| `agent-wiki/hooks/session_start.py` | 흐름 재배치, 비대상 분기, 실패 첫 줄 통일 | 기존 함수 수정 |
| `agent-wiki/README.md` | `## 세션 주입` 문단 갱신 | ⑥ |
| `agent-wiki/.claude-plugin/plugin.json` | version 0.10.0 → 0.11.0 | ⑥ |
| `.claude-plugin/marketplace.json` | `metadata.version` 4.7.0 → 4.8.0 | ⑥ |

### agent-wiki/scripts/generate_domain_overview.py

- **머리 주석**: 기존 생성기처럼 2줄 — "위키 대상이 아닌 세션의 주입 블록(대상 아님 고지, 위키 문서 사용 규칙, 도메인 목록)을 출력한다." / "인자는 baseRoot와 현재 프로젝트 표시 이름이며 registry.json의 도메인 description만 읽는다."
- **사용법**: `generate_domain_overview.py <baseRoot> <label>`, 인자 수가 다르면 `raise SystemExit("usage: …")`
- **출력**: `외부 계약` 절의 비대상 주입을 모듈 상수 템플릿 하나로 두고 `{label}`·`{base}`·도메인 행을 채워 print, 도메인 행 형식은 `generate_document_list.py`의 다른 도메인 행과 같음(import하지 않고 한 줄로 씀 — 생성기 간 의존을 만들지 않는 기존 원칙)

### agent-wiki/hooks/session_start.py

- **상수**: `FAIL = "위키 로드에 실패했습니다."`, `REGISTER = "위키 대상 레포라면 '/agent-wiki:register'로 등록하세요"`
- **`origin_slug(project)`**: 기존 `main()` 안의 `git remote get-url origin` 호출과 slug 추출을 옮기고, 실패나 빈 출력이면 `None`
- **`label(project)`**: `배경`의 표시 이름 식
- **`main()` 순서**: ① config·경로, `project = Path(CLAUDE_PROJECT_DIR 또는 cwd)` ② 동기화(조건 기존과 같음)와 최신화 경고 ③ `registry.json` 없으면 `("", notice(FAIL, [*warnings, init 불릿]))` ④ `domains`가 비면 `("", notice(FAIL, [*warnings, 도메인 없음 불릿]))` ⑤ `slug = origin_slug(project)`, 도메인 조회 ⑥ 등록이면 기존 색인 쓰기·생성기 3종 `blocks`와 문서 수 첫 줄, 비대상이면 `blocks = {"도메인 개요": generate("generate_domain_overview.py", base, label)}`와 비대상 첫 줄 ⑦ 공통 꼬리 — 결합 `text`, 한도 초과 불릿, `None` 블록 이름(등록은 뒤에 `색인 파일`)으로 작동 실패 불릿, 비대상이고 slug가 있으면 `REGISTER` 불릿, `text`가 비면 `("", notice(FAIL, warnings))` 아니면 `(text, notice(first, warnings))`
- **삭제**: origin 없음 조기 반환 `("", "")`, 위키 없음·미등록·`{key} 프로젝트 위키를 로드하지 못했습니다.`의 상태별 첫 줄과 위키 없음·미등록 주입 한 줄
- **`__main__`**: 예외 첫 줄을 `FAIL`로 바꾸고 불릿은 기존 형식 유지
- **머리 주석**: "현재 레포의 위키 주입 텍스트를 출력한다"를 등록 레포면 레포 주입, 아니면 도메인 개요 주입을 출력한다는 문장으로 바꿈

### agent-wiki/README.md

- 41행 문단의 "위키가 없거나 미등록 레포면 안내 한 줄만 주입하고, git 원격이 없는 폴더에는 주입하지 않습니다."를 "등록되지 않은 레포·git 원격이 없는 레포·git 밖 폴더에서는 위키 대상이 아님을 알리고 도메인 목록과 문서 폴더 경로만 주입해, 관련 질문이 오면 에이전트가 위키 문서를 찾아 답하게 합니다."로 바꿈
- "세션 시작·재개·`/clear` 때는 로컬 위키를 먼저 최신화하며"에 "위치와 관계없이"를 넣음
- 알림 문장의 괄호를 "(등록 레포 로드·도메인 개요 로드·로드 실패 중 하나와 문서 수, 위키 동기화 일시, 최신화 실패·주입 한도 초과·작동 실패 경고, 실패 원인)"으로 바꿈

## 커밋 분해

브랜치는 `agent-wiki-non-target-session`(기록 폴더 slug와 같게)으로 main에서 만듦. 검증 스크립트는 scratchpad의 bash 파일로 만들어 `bash {파일}`로 실행하고, 위키 변형은 `cp -R ~/.agent-wiki {scratch}/wiki`와 `config.json`의 `wiki.baseRoot`(필요하면 `wiki.remote`)만 바꾼 플러그인 복사본(`cp -R agent-wiki {scratch}/plugin`)에서 함. 구현 전에 main의 훅으로 이 레포를 `{"source":"compact"}`로 실행한 출력을 `{scratch}/before.json`에 저장함.

| # | 범위 | 검증 |
| --- | --- | --- |
| 1 | `agent-wiki/scripts/generate_domain_overview.py`, `agent-wiki/hooks/session_start.py` | V1 전 항목 통과 |
| 2 | `agent-wiki/README.md`, `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `python3 -m json.tool`이 두 JSON을 오류 없이 출력, plugin.json version 0.11.0, `metadata.version` 4.8.0, `grep -n "주입하지 않습니다" agent-wiki/README.md` 출력 없음 |

- **V1 훅 단독 실행**: 각 케이스에서 `echo '{"source":"…"}' | CLAUDE_PROJECT_DIR=… python3 {플러그인}/hooks/session_start.py` 출력 JSON을 `python3 -c`로 파싱해 확인
  - 등록: 이 레포, compact → `additionalContext`가 `{scratch}/before.json`과 같고, `systemMessage`는 `위키 동기화` 앞까지 같음(그 사이 다른 세션의 동기화로 시각만 달라질 수 있음)
  - 미등록: origin이 `https://example.com/x/foo-api.git`인 임시 git 레포, compact → 첫 줄 `현재 프로젝트(foo-api)는 위키 대상이 아닙니다. 도메인 개요만 로드되었습니다. (도메인 3개 · 위키 동기화 `, 마지막 줄 `- 위키 대상 레포라면 '/agent-wiki:register'로 등록하세요`, `additionalContext`가 `# 위키 — 대상 외 프로젝트(foo-api)`로 시작하고 registry 도메인 3개 행을 모두 포함
  - origin 없는 git 레포: 임시 `git init` 레포, compact → 첫 줄 괄호 안이 그 절대 경로, 불릿 없음, `additionalContext` 있음
  - 홈: `CLAUDE_PROJECT_DIR=$HOME`, compact → 첫 줄 `현재 프로젝트(~)는 위키 대상이 아닙니다.`로 시작
  - 비대상 최신화: git 밖 임시 폴더, startup → `~/.agent-wiki/.git/FETCH_HEAD` 수정 시각이 실행 전보다 뒤이고 비대상 첫 줄
  - 최신화 실패: 위키 복사본 + `wiki.remote`를 `https://invalid.invalid/x.git`로 둔 플러그인 복사본, git 밖 임시 폴더, startup → 비대상 첫 줄 아래 `- 위키 최신화 실패 : fatal: …`
  - 위키 없음: `wiki.baseRoot`를 없는 경로로 둔 플러그인 복사본 → `systemMessage`가 정확히 `위키 로드에 실패했습니다.\n- '/agent-wiki:init'을 실행해 위키 초기 세팅을 진행하세요`, `hookSpecificOutput` 없음
  - 도메인 0개: `registry.json`을 `{"domains": {}}`로 바꾼 위키 복사본, compact → `위키 로드에 실패했습니다.\n- 위키에 등록된 도메인이 없습니다. 위키 대상 레포라면 '/agent-wiki:register'로 등록하세요`, `hookSpecificOutput` 없음
  - 개요 생성 실패: 플러그인 복사본의 `generate_domain_overview.py` 첫 줄 뒤에 `raise SystemExit(1)`, 미등록 임시 레포 → `위키 로드에 실패했습니다.\n- 위키 작동 실패 : 도메인 개요 생성 실패\n- 위키 대상 레포라면 '/agent-wiki:register'로 등록하세요`, `hookSpecificOutput` 없음
  - 등록 생성 전체 실패: 플러그인 복사본의 생성기 3종 첫 줄 뒤에 `raise SystemExit(1)`, 이 레포 → `위키 로드에 실패했습니다.\n- 위키 작동 실패 : 위키 규칙·레포 지도·문서 목록·색인 파일 생성 실패`
  - 예외: 플러그인 복사본의 `config.json`을 깨진 JSON으로 → `위키 로드에 실패했습니다.\n- 위키 작동 실패 : JSONDecodeError: …`, `hookSpecificOutput` 없음

## 특이 사항

- **범위 밖**: 사내판 미러링(별도 이슈), 등록 레포 주입 내용, user·project 스코프 중복 설치 정리(project 스코프 설치본이 있으면 그 훅만 실행되며 사용자가 `/plugin`으로 제거함), python3 미설치처럼 훅 프로세스가 뜨지 못하는 경우의 표시
- **트레이드오프**: 위키와 무관한 모든 세션의 시작·재개·`/clear`가 최대 3초 늦어질 수 있음
- **의도적 단순화**: 비대상 세션의 문서 탐색은 색인 파일 없이 문서 frontmatter grep에 맡김 — 도메인 description만으로 도메인 선택이 어렵다는 사례가 쌓이면 도메인 행에 레포 이름을 더하거나 도메인 색인 파일 생성으로 올림
- **후속 작업**: 머지 뒤 위키 `session-start-hook` 문서의 "origin 판정을 위키 동기화보다 먼저 함", "알림은 git 밖·origin 없는 폴더를 뺀 전 상태를 표시", "git 밖이거나 origin 없는 폴더의 세션에서는 위키 사본도 최신화되지 않음" 3건을 `/agent-wiki:update`로 갱신
