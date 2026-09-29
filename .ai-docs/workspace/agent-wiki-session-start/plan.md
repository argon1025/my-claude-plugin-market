# agent-wiki 세션 주입과 읽기 전용 위키·워크스페이스 전환

## 의도

- **왜**: agent-wiki에는 세션 주입이 없어 에이전트가 위키를 모르고, init·register는 위키 트리·워크스페이스 상태(다른 브랜치·미커밋 변경·로컬 커밋)마다 보고·확인 분기를 두어 복잡함
- **누가**: MSA 환경에서 매 세션 개발·코드 리뷰하는 에이전트와, 플러그인을 고치는 관리자가 겪음
- **완료**: 등록 레포 세션에 `## 외부 계약`의 주입 텍스트가 들어가고, `wiki.baseRoot`·`workspace.root`는 어디서도 쓰지 않는 읽기 전용 사본(항상 원격 기준 브랜치로 강제 정리)이며, register·init의 위키 쓰기는 `mktemp -d` 임시 clone에서 끝남

## 배경

- **선행 결과물**: PR #26(`887f389`)으로 agent-wiki `0.2.0`(init·register 스킬, `scripts/sync_register_repositories.py`·`verify_register_file.py`·`write_skeleton.sh`)이 main에 머지됨, marketplace metadata version `3.3.0`
- **현행 정책**: init 1절·register 1절은 `fetch`·`status --short --branch` 후 AskUserQuestion(`변경 버리고 진행`·`중단`)으로 확인받아 `checkout -f -B`·`clean -fd`로 정리하고, `sync_register_repositories.py`는 기존 clone 변경을 `dirty`로 보고하며 `--force`일 때만 정리함 — 이번 작업에서 모두 폐지
- **데이터 계약**: registry.json 노드 7키(`remote`·`defaultBranch`·`status`·`stack`·`summary`·`responsibilities`·`hosts`), deps.json `deps["{domain}/{slug}"] = [{"to", "desc"}]`(그룹 키가 from), 문서 `knowledge/{domain}/`·`knowledge/{domain}/{slug}/`, 문서 frontmatter에 `description:` 한 줄 — 하위 호환 없음
- **slug 판정**: 현재 레포 `git remote get-url origin` 마지막 경로에서 `.git`을 뺀 소문자, 포크 판별·upstream 우선·remote 정규화 없음
- **훅 제약**: `additionalContext`는 약 10,000자에서 경고 없이 잘리고, 종료 코드가 0이 아니면 주입이 사라지며, SessionStart stdin JSON의 `source`는 `startup`·`resume`·`clear`·`compact`
- **공유 트리**: llm-wiki는 `~/.llm-wiki`에서 쓰기 작업(update의 `wiki-update/` 브랜치 등)을 하므로 agent-wiki는 별도 경로로 분리함
- **참고 구현**: llm-wiki `hooks/session_start.py`의 `Popen` + `wait(timeout=3)` 패턴(늦으면 git이 뒤에서 마저 돎)만 동작 사실로 참고하고 코드·문구는 재활용하지 않음

## 확정 결정 (사용자 확인 2026-09-29)

- **읽기 전용**: "config 에 정의된 워크스페이스, 위키는 수정을 금지하고 오직 읽기전용으로만 쓰고 수정해야하면 알아서 다른곳에 클론해서 쓰거나 로컬 내 폴더 찾아서 쓰라는 정책으로 일괄 통일" — 두 폴더는 항상 `fetch`·`checkout -f -B {branch} origin/{branch}`·`clean -fd`로 강제 정리하고 확인 질문을 두지 않음
- **쓰기 위치**: register·init의 위키 쓰기는 `mktemp -d` 임시 clone에서 수정·커밋·push한 뒤 `baseRoot`를 강제 정리함
- **경로**: `wiki.baseRoot` 기본값 `~/.agent-wiki`, `workspace.root` 기본값 `~/.agent-wiki-workspace`
- **범위**: 읽기 전용 전환(init·register·동기화 스크립트)과 세션 훅을 한 계획에서 진행하며 전환을 먼저 커밋함
- **훅 동기화**: startup·resume에서만 위키 트리를 강제 정리하고 최대 3초 기다린 뒤 주입, 늦으면 정리는 뒤에서 마저 돌고 이번 주입은 이전 사본, clear·compact는 재주입만 — "해당 레포 기반으로 변경작업 안할예정임 복사본 생성 예정"
- **알림 없음**: 동기화 지연·실패·변경 폐기는 알리지 않고, 위키 부재·미등록 레포에만 한 줄, git 밖(origin 없음)은 주입 없음
- **구조**: "각각 generate_repository_map.py 처럼 텍스트 생성기 만들어서 세션훅헤서 전부 실행하여 텍스트 합치는 구조 ... 나중에 수정, 제외하기 용이하도록"
- **관점**: 매 세션 MSA 환경에서 개발·코드 리뷰하는 에이전트 입장에서 씀
- **레포 지도**: 제목 `{domain} 도메인의 전체 레포지토리`, 같은 도메인 레포 전수와 각 행 responsibilities, 간선 블록·`desc` 없이 이름 옆 `현재`·`현재 레포가 의존`·`현재 레포에 의존` 표식, 표식이 붙는 다른 도메인 레포는 `{domain}/{slug}` 행 추가 — "표식은 참고용임으로 책임으로 의존성 의심이 된다면 코드를 직접 확인하라"
- **다른 레포 코드**: 동기화 명령은 안내하지 않음 — "에이전트가 필요하면 클론하는거고 아니면 로컬 레포 찾아서 쓰는거고 이걸너무 제한 안했으면함"
- **문서 목록**: `도메인 공유 문서`(`knowledge/{domain}/` 바로 아래)·`{slug} 전용 문서`(`knowledge/{domain}/{slug}/`)·`다른 도메인 문서`(도메인 — description), 경로는 제목 아래 줄에 `{name}.md` 꼴, 행은 `이름 — description`, type 표기 없음
- **규칙**: 문서 먼저 찾기·grep 최후, 모순 병기, "위키는 직접 고치지 말고 고쳐야 할 내용이 있으면 사용자에게 알린다"
- **공존·분량**: llm-wiki 훅 감지·분기 없음, 10,000자 상한 처리 없음
- **기록 위치**: 브랜치 `feat/agent-wiki-session-start`(main에서 분기), 기록 `.ai-docs/workspace/agent-wiki-session-start/`

## 외부 계약

### 주입 텍스트 (등록 레포)

블록은 아래 순서로 빈 줄 하나를 사이에 두고 합치며, `{baseRoot}`·`{workspace.root}`는 `~`를 확장한 절대 경로임.

```
# 위키 — {domain}/{slug}

이 레포는 MSA 환경의 한 서비스입니다. 개발·코드 리뷰 전에 아래 문서와 레포 목록으로 요청과 관련된 사실과 영향 범위를 확인하세요.

- 사용자 요청에 맞는 문서를 아래 목록에서 먼저 찾아 읽으세요. 목록에서 찾을 수 없으면 마지막으로 문서 폴더를 grep해 본문까지 찾습니다.
- 문서끼리 또는 문서와 코드가 다르면 한쪽을 고르지 말고 두 값을 함께 알리세요.
- 위키는 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리세요.

## {domain} 도메인의 전체 레포지토리

`{workspace.root}/{slug}`

작업 전 영향도·의존성·선행 작업 파악이 필요하면 해당 레포 코드를 직접 확인하세요. 의존 표식은 참고용이므로 책임만으로도 의존이 의심되면 코드로 확인합니다. 위 경로는 읽기 전용 사본이므로, 없거나 수정이 필요하면 로컬 체크아웃을 찾거나 `{baseRoot}/registry.json`의 remote를 다른 곳에 clone해 쓰세요.

- {slug} (현재) — {responsibilities를 " · "로 연결}
- {slug} (현재 레포에 의존) — …
- {다른도메인}/{slug} (현재 레포가 의존) — …

## 도메인 공유 문서

`{baseRoot}/knowledge/{domain}/{name}.md`

- {name} — {description}

## {slug} 전용 문서

`{baseRoot}/knowledge/{domain}/{slug}/{name}.md`

- {name} — {description}

## 다른 도메인 문서

`{baseRoot}/knowledge/{domain}/`

- {다른도메인} — {도메인 description}
```

- **첫 줄 `{slug}`**: 두 번째 블록 제목 아래 줄의 `{slug}`는 치환하지 않는 리터럴이고, 마지막 블록의 `{domain}`도 리터럴임
- **표식**: 한 행에 여러 개면 `(현재, 현재 레포에 의존)`처럼 쉼표로 잇고, 표식이 없으면 괄호를 생략함
- **행 내용**: responsibilities가 비면 summary를 씀
- **빈 블록**: 문서가 0건인 문서 블록과 다른 도메인이 없는 `다른 도메인 문서` 블록은 제목째 생략하며, description이 없는 문서는 `- {name}`만 씀
- **정렬**: 레포는 registry 순서, 표식이 붙는 다른 도메인 레포는 그 뒤에 `{domain}/{slug}` 사전순, 문서는 파일명 사전순

### 예외 주입

```
# 위키 없음 — `/agent-wiki:init` 실행
# 위키 — 미등록 레포 {slug}, 등록은 `/agent-wiki:register`
```

- **위키 없음**: `{baseRoot}/registry.json`이 없을 때
- **미등록**: origin slug가 registry 어느 도메인에도 없을 때
- **주입 없음**: origin이 없거나 git 밖, config·stdin·registry 파싱 실패 등 그 밖의 모든 실패(출력 없이 종료 코드 0)

### 훅 출력

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "{텍스트}"}}
```

## 선행 읽기

- `.ai-docs/workspace/share-context-init/feedback.md` — 스킬 문체(절 제목·한 줄 조건·명령 코드 블록·예외 한 줄, 굵은 라벨 불릿 금지), 용어 "위키", README·plugin.json에 진행 상황 금지, 공개 저장소 규칙
- `.ai-docs/workspace/agent-wiki-session-start/feedback.md` — 이번 작업에서 확정된 의도와 폐기된 정책 목록

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/config.json` | `wiki.baseRoot` `~/.agent-wiki`, `workspace.root` `~/.agent-wiki-workspace` | ② 기존 키 값만 변경 |
| `agent-wiki/scripts/sync_wiki.py` | 신규 — 위키 트리 강제 정리 | ⑦ 에이전트 없는 훅이 호출해야 하므로 스킬 본문의 git 명령으로는 불가, init·register도 같은 명령으로 호출 |
| `agent-wiki/scripts/sync_register_repositories.py` | `dirty` 판정·`--force` 제거, 항상 강제 정리 | ② 기존 파일 축소 |
| `agent-wiki/skills/init/SKILL.md` | 확인 질문 제거, 빈 원격 골격은 임시 clone에서, 위키 트리는 `sync_wiki.py` | ② |
| `agent-wiki/skills/register/SKILL.md` | 1절 `sync_wiki.py`, 3절 `dirty` 문단 제거, 6절 임시 clone 기록 | ② |
| `agent-wiki/scripts/generate_wiki_rules.py` | 신규 — 도입부·규칙 블록 | ⑦ 사용자가 블록별 생성기 구조를 지정, 정적 텍스트지만 제목의 `{domain}/{slug}` 치환 필요 |
| `agent-wiki/scripts/generate_repository_map.py` | 신규 — 레포 지도 블록 | ⑦ registry·deps JSON 순회와 표식 계산은 표준 라이브러리 스크립트가 최소 |
| `agent-wiki/scripts/generate_document_list.py` | 신규 — 문서 목록 3블록 | ⑦ frontmatter description 추출은 에이전트 없는 경로라 스크립트 필요 |
| `agent-wiki/hooks/session_start.py` | 신규 — 동기화 호출, slug·도메인 판정, 예외 한 줄, 생성기 결합, JSON 출력 | ⑦ SessionStart 훅 진입점은 플랫폼상 명령이 필요 |
| `agent-wiki/hooks/hooks.json` | 신규 — SessionStart 명령 1개 | ④ 플랫폼 기본 기능 |
| `agent-wiki/.claude-plugin/plugin.json` | version `0.2.0`에서 `0.3.0` | ② |
| `agent-wiki/README.md` | 설정 기본값, 위키 구조 경로, 읽기 전용 정책 한 줄, 세션 주입 절, 일괄 최신화 절의 `dirty`·`--force` 문장 제거 | ② |
| `.claude-plugin/marketplace.json` | metadata version `3.3.0`에서 `3.4.0` | ② |

모든 스크립트는 python3 표준 라이브러리만 쓰고, 머리 주석은 역할·책임 경계 3줄 이내이며, git은 `GIT_TERMINAL_PROMPT=0` 환경으로 실행함.

### scripts/sync_wiki.py

- **인자**: `sync_wiki.py {baseRoot} {remote} {baseBranch}`, `~` 확장
- **동작**: 폴더가 없으면 `git clone {remote} {baseRoot}`, 있으면 `git remote get-url origin`이 `remote`와 다를 때 `fail origin {실제값}`으로 끝냄, 이어서 `fetch origin {baseBranch}`·`checkout -f -B {baseBranch} origin/{baseBranch}`·`clean -fd`
- **출력**: 성공 `ok`·종료 코드 0, 실패 `fail {git 출력의 error:·fatal: 줄 우선, 없으면 마지막 줄}`·종료 코드 1
- **분량**: 40줄 이내

### scripts/sync_register_repositories.py

- **변경**: `sync()`에서 `force`·`fresh`·`dirty` 판정과 `--force` 인자를 없애고 clone(없을 때)·fetch·`checkout -f -B`·`clean -fd`만 수행, 머리 주석에서 dirty 문장 제거
- **유지**: 인자(`registry root [slugs] --current SLUG REMOTE BRANCH`), `ok`·`fail` 출력, 미등록 slug `fail`, 종료 코드 규칙

### skills/init/SKILL.md

- **도입**: `wiki` 값 사용, `GIT_TERMINAL_PROMPT=0`, "`baseRoot`는 읽기 전용 사본이며 쓰기는 임시 clone에서 함" 한 문장
- **1. 빈 원격 확인**: `git ls-remote --heads {remote} {baseBranch}` 출력이 비면 2절, 있으면 3절
- **2. 골격 생성**: `mktemp -d` 결과를 `{tmp}`로 쓰고 `git clone {remote} {tmp}`·`bash ${CLAUDE_PLUGIN_ROOT}/scripts/write_skeleton.sh {tmp}`·`git -C {tmp} add -A`·`commit -m "chore(init): 위키 골격"`·`branch -M {baseBranch}`·`push -u origin {baseBranch}`·`rm -rf {tmp}`, 예외 `write_skeleton.sh` 종료 코드 1이면 중단 후 보고
- **3. 위키 동기화**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_wiki.py {baseRoot} {remote} {baseBranch}`, 예외 `fail origin`이면 다른 저장소이므로 중단 후 보고
- **4. 실패 처리**: 인증·네트워크 오류면 사용자가 `! git ls-remote {remote}`로 인증을 마친 뒤 다시 실행하도록 안내, 그 밖의 실패는 원인만 보고
- **5. 보고**: 위키 경로, 수행 결과, `git -C {baseRoot} log -1 --oneline`
- **제거**: `status --short --branch`, AskUserQuestion, `baseRoot`에서의 commit·push

### skills/register/SKILL.md

- **1. 위키 최신화**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_wiki.py {baseRoot} {remote} {baseBranch}`, 예외 `fail`이거나 `{baseRoot}/registry.json`이 없으면 `/agent-wiki:init` 안내 후 중단
- **2·4·5·7절**: 변경 없음
- **3. 레포 준비**: 명령 유지, `dirty` 줄·`--force` 재실행 문단을 삭제하고 "레포마다 `ok`·`fail` 한 줄"로 바꿈
- **6. 기록**: `mktemp -d` 결과를 `{tmp}`로 쓰고 아래 순서로 실행하며, registry.json·deps.json Edit 규칙(7키, 블록 통째 교체, 간선 없으면 키 삭제, 신규 도메인 생성, 서식 유지)은 `{tmp}`의 파일에 적용

  ```
  git clone -b {baseBranch} {remote} {tmp}
  mkdir -p {tmp}/knowledge/{domain}/{slug}
  [ -n "$(ls -A {tmp}/knowledge/{domain}/{slug})" ] || touch {tmp}/knowledge/{domain}/{slug}/.gitkeep
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_register_file.py {tmp} {domain}/{slug}
  git -C {tmp} add registry.json deps.json knowledge/{domain}/{slug}
  git -C {tmp} diff --cached --quiet
  git -C {tmp} commit -m "chore(register): {slug} → {domain}"
  git -C {tmp} push origin {baseBranch}
  rm -rf {tmp}
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_wiki.py {baseRoot} {remote} {baseBranch}
  ```

  예외는 검증 종료 코드 1이면 출력대로 고쳐 재검증, `diff --cached --quiet` 종료 코드 0이면 commit·push를 건너뛰고 `변경 없음`, push 거절이면 `git -C {tmp} pull --rebase origin {baseBranch}` 후 한 번 더 push, rebase 충돌이나 두 번째 거절이면 `rebase --abort` 후 `{tmp}` 경로와 원인을 보고하고 중단
- **제거**: 1절 `status --short --branch`·AskUserQuestion, 3절 `dirty` 확인, 6절 "남은 로컬 커밋은 다음 실행의 1절에서 확인받아 정리" 문장
- **분량**: 코드 블록 포함 120줄 이내 유지

### scripts/generate_wiki_rules.py

- **인자**: `{domain}/{slug}`
- **출력**: `## 외부 계약`의 첫 블록(제목·도입 문장·규칙 3줄) 그대로 stdout
- **분량**: 25줄 이내

### scripts/generate_repository_map.py

- **인자**: `{baseRoot} {workspace.root} {domain}/{slug}`
- **입력**: `{baseRoot}/registry.json`, `{baseRoot}/deps.json`(없거나 깨지면 표식 없이 진행)
- **표식 계산**: `deps[{domain}/{slug}]`의 `to`는 `현재 레포가 의존`, 다른 그룹 키 중 `to`가 `{domain}/{slug}`인 것은 `현재 레포에 의존` — 그룹 키와 `to`만 읽으므로 `desc`·구형 `kind`·`contracts`는 무시
- **다른 도메인 행**: 표식이 붙은 끝점 중 다른 도메인 레포만 `{domain}/{slug}` 라벨로 추가, registry에 없는 끝점은 생략
- **출력**: `## 외부 계약`의 둘째 블록
- **분량**: 50줄 이내

### scripts/generate_document_list.py

- **인자**: `{baseRoot} {domain}/{slug}`
- **description 추출**: 파일 첫 줄이 `---`인 frontmatter 안의 `description:` 줄 값(앞뒤 공백 제거), 없으면 이름만
- **범위**: `knowledge/{domain}/*.md`(하위 폴더 제외), `knowledge/{domain}/{slug}/*.md`, registry의 다른 도메인 `description`
- **출력**: `## 외부 계약`의 셋째~다섯째 블록, 빈 블록 생략
- **분량**: 50줄 이내

### hooks/session_start.py

- **입력**: stdin JSON의 `source`(없거나 파싱 실패면 `startup`), 프로젝트 경로는 `CLAUDE_PROJECT_DIR` 환경 변수, 없으면 현재 디렉터리
- **설정**: 스크립트 위치 기준 `../config.json`에서 `wiki`·`workspace.root`를 읽고 `~` 확장
- **동기화**: `source`가 `startup`·`resume`이고 `{baseRoot}/.git`이 있을 때만 `sync_wiki.py`를 `Popen(start_new_session=True, stdout·stderr DEVNULL)`으로 실행해 `wait(timeout=3)`, 시간 초과는 무시 — `baseRoot`가 없으면 clone하지 않음(설치는 init의 일)
- **판정**: `git -C {project} remote get-url origin`(timeout 5초) 실패면 출력 없음, slug는 마지막 경로에서 `.git`을 뺀 소문자, registry 도메인마다 `repos`에서 slug를 찾음
- **결합**: `generate_wiki_rules.py`·`generate_repository_map.py`·`generate_document_list.py`를 순서대로 `subprocess.run([sys.executable, …], timeout=5)`, 종료 코드 0이고 출력이 있는 블록만 빈 줄 하나로 합침
- **종료**: `main()` 전체를 `try/except Exception`으로 감싸 어떤 실패에서도 종료 코드 0, 주입 텍스트가 비면 아무것도 출력하지 않음
- **분량**: 70줄 이내, 머리 주석 3줄 이내

### hooks/hooks.json

```json
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py\""}]}]}}
```

- **matcher 없음**: 모든 source에서 실행하고 동기화 여부는 스크립트가 판정

### README.md

- **설정 표**: `wiki.baseRoot` `~/.agent-wiki`, `workspace.root` `~/.agent-wiki-workspace`
- **정책 한 줄**: "`wiki.baseRoot`·`workspace.root`는 읽기 전용 사본이며 실행 때마다 원격 기준 브랜치로 덮어씁니다"
- **세션 주입 절**: 등록 레포에서 세션을 열면 위키 규칙·도메인 레포 지도·문서 목록이 주입되고, startup·resume에서 위키를 최신화함(최대 3초 대기)
- **위키 구조**: 트리 머리 경로를 `~/.agent-wiki/`로
- **일괄 최신화 절**: 명령 경로를 새 기본값으로, `dirty`·`--force` 문장 삭제
- **금지**: 진행 상황·예정 기능·사내 URL

## 커밋 분해

승인 직후 `git switch main && git pull --ff-only && git switch -c feat/agent-wiki-session-start` 후 `plan.md`·`feedback.md` 스냅샷을 한 커밋으로 남김. 검증 픽스처는 스크래치 `{S}`에 두고, 플러그인 사본은 `cp -R agent-wiki {S}/plugin` 후 `{S}/plugin/config.json`을 `baseRoot={S}/wiki`·`remote={S}/wiki.git`·`workspace.root={S}/ws`로 바꿔 씀(저장소의 config.json은 건드리지 않음).

| # | 범위 | 검증 |
|---|---|---|
| 1 | `scripts/sync_wiki.py`, `scripts/sync_register_repositories.py` — `refactor(agent-wiki): 위키·워크스페이스 강제 동기화 스크립트` | `git init --bare {S}/wiki.git`에 `main` 커밋 1건을 넣고 ① `sync_wiki.py {S}/wiki {S}/wiki.git main` 첫 실행: `ok`, 종료 코드 0, clone 생성 ② `{S}/wiki`에 파일 수정·미추적 파일·로컬 커밋·`git switch -c x`를 만든 뒤 재실행: `ok`, `git -C {S}/wiki status --short --branch` 출력이 `## main...origin/main` 한 줄 ③ remote 인자를 다른 경로로 주면 `fail origin …`, 종료 코드 1 ④ `sync_register_repositories.py` 기존 clone에 같은 변경을 만든 뒤 실행: `ok` 줄, `dirty` 출력 없음, 원격 신규 커밋 반영 ⑤ `grep -n "force\|dirty" agent-wiki/scripts/sync_register_repositories.py` 출력 없음, `python3 -m py_compile` 두 파일 종료 코드 0, 줄 수 40·70 이내 |
| 2 | `config.json`, `skills/init/SKILL.md`, `skills/register/SKILL.md` — `feat(agent-wiki): 위키·워크스페이스 읽기 전용 전환` | `python3 -m json.tool agent-wiki/config.json` 종료 코드 0, `grep -rnE "AskUserQuestion\(\`변경|dirty|--force|status --short" agent-wiki/skills` 출력 없음, `grep -rn "git -C {baseRoot} \(commit\|push\|add\)" agent-wiki/skills` 출력 없음, `wc -l agent-wiki/skills/register/SKILL.md` 120 이하, `claude plugin validate ./agent-wiki` 에러 0 |
| 3 | `scripts/generate_wiki_rules.py`, `scripts/generate_repository_map.py`, `scripts/generate_document_list.py` — `feat(agent-wiki): 세션 주입 텍스트 생성기` | 픽스처 위키(도메인 `d1-a`에 레포 `a`·`b`, 도메인 `d2-b`에 레포 `c`, deps `d1-a/b → d1-a/a`·`d1-a/a → d2-b/c`, `knowledge/d1-a/` 문서 2건(하나는 description 없음), `knowledge/d1-a/a/` 문서 1건)로 ① rules `d1-a/a`: 첫 줄 `# 위키 — d1-a/a` ② map `d1-a/a`: `- a (현재) —`, `- b (현재 레포에 의존) —`, `- d2-b/c (현재 레포가 의존) —` 행 존재, 제목 아래 줄 `` `{S}/ws/{slug}` `` ③ map에서 deps.json 삭제 후에도 종료 코드 0, 표식 없음 ④ docs `d1-a/a`: `## 도메인 공유 문서`·`## a 전용 문서`·`## 다른 도메인 문서` 순서, description 없는 문서는 `- {name}`만, `- d2-b — …` 행 ⑤ docs `d1-a/b`: `## b 전용 문서` 블록 없음 ⑥ 세 파일 `py_compile` 종료 코드 0, 줄 수 25·50·50 이내 |
| 4 | `hooks/hooks.json`, `hooks/session_start.py` — `feat(agent-wiki): SessionStart 위키 주입 훅` | 3의 픽스처를 `{S}/wiki.git`에 push해 두고, origin이 `https://example.com/org/A.git`인 `{S}/proj`에서 `echo '{"source":"startup"}' \| CLAUDE_PROJECT_DIR={S}/proj python3 {S}/plugin/hooks/session_start.py`: ① 종료 코드 0, stdout JSON의 `additionalContext`가 `# 위키 — d1-a/a`로 시작하고 `## 외부 계약`의 블록 제목 5종 포함 ② `{S}/wiki`에 로컬 변경·다른 브랜치를 만든 뒤 startup 실행: 실행 후 `## main...origin/main` ③ 원격에 커밋 추가 후 `source: compact` 실행: `{S}/wiki` HEAD 변화 없음 ④ origin을 `…/zzz.git`로 바꾸면 `# 위키 — 미등록 레포 zzz, 등록은 \`/agent-wiki:register\`` ⑤ origin 제거 시 stdout 빈 문자열, 종료 코드 0 ⑥ `{S}/wiki` 삭제 시 `# 위키 없음 — \`/agent-wiki:init\` 실행`, clone되지 않음 ⑦ config.json을 깨뜨리면 stdout 빈 문자열, 종료 코드 0 ⑧ `{S}/wiki` origin을 응답 없는 `https://10.255.255.1/x.git`로 바꾸고 `time`으로 startup 실행: 4초 미만, 주입 정상 ⑨ `claude plugin validate ./agent-wiki` 에러 0 |
| 5 | `plugin.json`, `README.md`, `.claude-plugin/marketplace.json` — `feat: agent-wiki 세션 주입과 읽기 전용 위키 v0.3.0` | `python3 -m json.tool .claude-plugin/marketplace.json` 종료 코드 0, `claude plugin validate .` 에러 0, `grep -nE "예정\|이관\|진행 중\|dirty\|--force\|llm-wiki-workspace\|~/.llm-wiki" agent-wiki/README.md` 출력 없음 |
| 6 | 수동 E2E(커밋 없음) | 빈 `git init --bare {S}/e2e.git`과 사본 config(`baseRoot={S}/e2e-wiki`·`remote={S}/e2e.git`·`workspace.root={S}/e2e-ws`)로 `claude -p --plugin-dir {S}/plugin`에서 ① `/agent-wiki:init`: 원격 `git log`에 `chore(init): 위키 골격`, `{S}/e2e-wiki` 상태 `## main...origin/main` ② 픽스처 레포(origin을 로컬 bare 경로로 둔 체크아웃 2개)에서 `--append-system-prompt "AskUserQuestion을 쓸 수 없으면 알아서(초안 채택)로 간주"`로 `/agent-wiki:register`: 원격에 `chore(register): {slug} → {domain}`, `{S}/e2e-wiki` 상태 깨끗, `ls -d ${TMPDIR}tmp.*` 결과에 register가 만든 임시 clone이 남지 않음 ③ 등록 레포 체크아웃에서 `claude -p --plugin-dir {S}/plugin "주입된 위키 첫 줄을 그대로 출력"` 응답이 `# 위키 — {domain}/{slug}` |

## 특이 사항

- **범위 밖**: update·add·audit 이관, llm-wiki 제거, 구형 데이터(scheme 없는 remote, `kind`·`contracts` 간선) 전환, `write_skeleton.sh`의 `.local/` `.gitignore` 항목
- **기존 사용자 경로**: 기본값이 `~/.agent-wiki`로 바뀌므로 기존 `~/.llm-wiki`·`~/.llm-wiki-workspace`는 agent-wiki가 더 이상 쓰지 않으며, 첫 세션은 `위키 없음` 한 줄이 주입되고 `/agent-wiki:init` 한 번으로 해소됨
- **의도적 단순화 1**: 동기화가 3초를 넘기면 git이 뒤에서 checkout을 이어가는 동안 생성기가 반쯤 바뀐 트리를 읽을 수 있음 — 다음 세션에서 바로잡히며, 잘못된 주입이 반복 보고되면 동기화를 임시 경로에 받은 뒤 교체하는 방식으로 바꿈
- **의도적 단순화 2**: 강제 정리는 `baseRoot`·`workspace.root`에서 사용자가 만든 변경을 확인 없이 버림 — README 정책 한 줄과 주입 문구로 읽기 전용임을 알리는 것으로 갈음함
- **의도적 단순화 3**: 로컬 체크아웃은 작업 브랜치 상태일 수 있어 기본 브랜치 코드와 다를 수 있으나, 에이전트의 선택을 제한하지 않기 위해 주입 규칙을 두지 않음
- **분량**: 현재 공개 위키 기준 주입은 약 4,000자이며 10,000자 상한 처리는 두지 않음 — 도메인 문서가 늘어 잘림이 확인되면 생성기 단위로 줄이는 방안을 검토함
- **구형 remote**: scheme 없는 노드는 워크스페이스 clone이 실패하므로 register 간선 탐색에서 빠지는 기존 한계가 그대로 남음
- **승인 후 기록**: `.ai-docs/workspace/agent-wiki-session-start/plan.md`에 이 계획을 쓰고, 이미 기록된 `feedback.md`에 `constraint` "Bash 도구 호출 사이에 셸 변수가 유지되지 않으므로 SKILL.md는 `mktemp -d` 결과를 `{tmp}` 자리표시자로 옮겨 쓰게 함"을 덧붙여 한 커밋으로 남김
