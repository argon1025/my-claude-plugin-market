# llm-wiki 레포 읽기를 위키 전용 bare 미러로 전환 (v5.2.0)

## 의도

- **왜**: 레포 경로 기록(`{WIKI_ROOT}/.local/paths.json`)이 세션을 연 체크아웃을 따라가서, 워크트리를 지우면 `/llm-wiki:update`가 그 레포를 `로컬 경로 없음`으로 건너뜀
- **누가**: 워크트리를 자주 쓰는 사용자가 `/llm-wiki:update`·`/llm-wiki:audit`을 돌릴 때
- **완료**: 위키가 등록 레포마다 전용 bare 미러를 직접 clone·fetch해 읽고, `paths.json` 없이 update·audit·검토가 동작함

## 배경

- **경로 소비처**: `paths.json` 읽기는 `scripts/update.py`(pending 182, advance 297), `scripts/graph.py` `load_paths`(1034, `cmd_render`·`cmd_repo`가 호출), `scripts/view.py`(56, 106), `hooks/session_start.sh`(98~105 기록, 136 `render_session`에 전달) — 쓰기는 훅과 register 스킬 5장
- **git 연산**: update.py의 fetch·rev-parse·log·diff·show·merge-base·rev-list와 update·audit 스킬의 `git grep {rev}`·`git show {rev}:{경로}`는 전부 bare 저장소에서 동작함 — 작업 폴더가 필요한 곳은 에이전트가 타 레포 파일을 직접 여는 `rules/agent-guide.md:16`과 `references/doc-contract.md:166`뿐
- **bare 함정**: `git clone --bare`는 fetch refspec을 두지 않아 이후 `fetch origin`이 FETCH_HEAD만 갱신하고 브랜치 ref는 낡음. `--mirror`는 GitHub의 `refs/pull/*`까지 받아 무거움
- **`.local/`**: 위키 `.gitignore`가 `.local/` 한 줄이라 `.local/mirrors/`는 이미 미추적. `.local/graph.html`(view.py)이 같은 폴더를 쓰므로 폴더는 유지
- **훅 유지 부분**: `session_start.sh`의 `TOPLEVEL`은 커서 거리(`rev-list cursor..HEAD`, 121~131)에 쓰이므로 유지 — `paths.json` 관련은 96~105와 136의 인자뿐
- **테스트**: 플러그인에 테스트·픽스처·CHANGELOG 없음. 버전은 `llm-wiki/.claude-plugin/plugin.json`의 `version` 하나만 올림(직전 v5.1.0 관례)

## 확정 결정 (사용자 확인 2026-09-26)

- **미러 도입**: 위키 전용 사본을 따로 두고 `paths.json`은 유지하지 않음 — 작업 폴더 없는 bare 미러
- **타 레포 읽기 통일**: 개발 세션에서 에이전트가 다른 레포 코드를 읽을 때도 미러로 통일 — `update.py mirror`로 미러를 확보·fetch한 뒤 `git -C {미러} grep/show {브랜치}`로 읽음. `●` 표시와 `paths.json`을 완전히 제거하며, 기본 브랜치에 병합된 코드만 보이고 작업 중인 로컬 변경은 보이지 않음을 수용함

## 외부 계약

- **미러 경로**: `{WIKI_ROOT}/.local/mirrors/{slug}.git`
- **clone URL**: registry 노드 `remote`가 `://`를 포함하거나 `git@`로 시작하면 그대로, 아니면 `https://{remote}.git` — `graph.py map`의 `## 접근 좌표` 문구("clone은 각 레포 remote로 `https://{remote}.git`")와 같은 규칙
- **refspec**: `remote.origin.fetch = +refs/heads/*:refs/heads/*` — fetch는 `git fetch --prune --quiet origin`
- **대상 ref**: 미러에서는 `{defaultBranch}`(= `refs/heads/{defaultBranch}`)
- **`mirror` 출력**: 레포마다 한 줄, 성공은 `{slug} {미러 절대경로}@{브랜치}`, 실패는 `{slug} 없음 — {사유}`. fetch만 실패하면 성공 줄 끝에 ` · fetch 실패 — 미러 기존 ref 기준`

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `scripts/graph.py` | `mirror_path(wiki, slug)` 추가, `local_pattern`·`load_paths` 삭제, `map_block`·`render_session`·`render_repo`의 `paths` 인자를 `wiki` 경로로 교체 | `mirror_path` ⑥ 한 줄 |
| `scripts/update.py` | `ensure_mirror` 함수와 `mirror` 하위 명령 추가, `pending`·`advance`가 미러를 씀, `target_ref`·`SKIP_NO_PATH` 삭제 | ⑦ — 아래 근거 |
| `scripts/view.py` | `local` 필드와 `load_paths` 호출 삭제 | ① 제거 |
| `templates/graph.html` | `●` 범례(239)·표시(340, 398, 534)·`addKv('local', …)`(433) 삭제 | ① 제거 |
| `hooks/session_start.sh` | `paths.json` 기록(96~105) 삭제, 남은 `{WIKI_ROOT}/.local/paths.json`은 `unlink(missing_ok=True)`로 제거, `render_session`에 위키 경로 전달, agent-guide 치환에 `{UPDATE_PY}` 추가(90) | ① 제거·⑥ 한 줄 |
| `rules/agent-guide.md` | 7의 "`●`는 로컬 사본" 삭제, 16의 상대 레포 코드 조회를 미러 명령으로 교체 | 문서 |
| `references/doc-contract.md` | 166 대상 판정의 "`.local/paths.json` 경로, 없으면 `git clone --depth 1`"을 미러 조회로 교체 | 문서 |
| `skills/update/SKILL.md` | 1장 이월 사유의 `로컬 경로 없음`을 `미러 준비 실패`로 | 문서 |
| `skills/audit/SKILL.md` | 1장 `레포` 줄을 `update.py mirror --repo …` 출력으로 교체 | 문서 |
| `skills/register/SKILL.md` | 21·85·92의 `paths.json` 기록·열을 미러로 교체 | 문서 |
| `README.md` | 35·37·50·63의 로컬 경로·`●`·`paths.json` 서술 교체 | 문서 |
| `.claude-plugin/plugin.json` | `version` 5.1.0 → 5.2.0 | 문서 |

### scripts/update.py

- **`ensure_mirror(wiki, slug, info) -> tuple[str | None, str]`**: (미러 경로 또는 None, 사유·노트 문자열) 반환
  - `remote`가 비면 `(None, "remote 없음 — /llm-wiki:register")`
  - 미러가 없으면 `git clone --bare --quiet {url} {path}`(timeout 600, `git()`의 cwd는 `.local/mirrors`로 두고 필요 시 `mkdir(parents=True)`) — 실패하면 부분 폴더를 `shutil.rmtree`로 지우고 `(None, "미러 clone 실패 — {stderr 첫 줄}")`
  - 있든 새로 받았든 `git config remote.origin.url {url}`(register가 remote를 바꿔도 따라감)과 `git config remote.origin.fetch +refs/heads/*:refs/heads/*`를 매번 설정한 뒤 `fetch --prune --quiet origin` — 실패하면 `(path, "fetch 실패 — 미러 기존 ref 기준")`
  - ⑦ 근거: 미러 확보는 코드베이스·표준 라이브러리에 없고, 스킬·에이전트가 git 명령을 직접 조립하면 update·audit·세션마다 refspec과 URL 규칙이 갈라짐
- **`mirror` 하위 명령**: `update.py mirror [--repo SLUG ...] --wiki W` — `--repo`가 없으면 휴면이 아닌 전 등록 레포, 있으면 지목 레포(휴면 포함)에 `ensure_mirror` 후 외부 계약의 출력 형식으로 한 줄씩. 등록되지 않은 slug는 `{slug} 없음 — 등록되지 않은 레포`. 종료 코드 0
- **`pending`**: `paths.json` 로드를 삭제하고 레포마다 `ensure_mirror` — None이면 사유를 `work["skipped"]`에, 노트가 있으면 `notes`에. 대상 ref는 `branch` 그대로 쓰고 `rev-parse` 실패 사유 문구는 기존 `대상 ref를 찾지 못함 ({branch})` 유지. `work.json` `repos[slug].path`는 미러 경로
- **`advance`**: 미러가 없으면 `# 미러 없음 — update.py mirror --repo {slug} 먼저` stderr와 종료 코드 1 — 경로가 없을 때 검증 없이 짧은 sha를 쓰던 경로를 없앰. 있으면 fetch 없이 `merge-base --is-ancestor {sha} {branch}`·`rev-parse`
- **docstring**: 19~20의 "`.local/paths.json` 3파일"을 "registry.json·state/*.json 2파일과 미러 존재"로
- **pathspec**: `extract_diff`의 `-- .`이 bare 저장소에서 동작하지 않으면 `-- :/`로 바꿈(커밋 1 검증에서 판정)

### scripts/graph.py

- **`mirror_path(wiki, slug)`**: `Path(wiki) / ".local" / "mirrors" / f"{slug}.git"` — update.py·훅·render가 같은 경로 규칙을 씀
- **`map_block`**: 헤더 2행을 `# 미러 {wiki}/.local/mirrors/{slug}.git · clone https://{host}/{owner}/{slug}.git`로(host 없으면 미러 부분만). 행의 ` ●`와 ` · 로컬 {path}` 삭제, ` · remote …` 예외 행은 유지
- **`render_repo`**: `- 로컬:` 필드를 `- 미러: {경로}`(폴더가 있을 때) 또는 `- 미러: 없음 — update.py mirror --repo {slug}`로
- **CLI**: `cmd_render`·`cmd_repo`는 `load_paths` 대신 `wiki`를 넘김

### rules/agent-guide.md

- **16 교체 문장**: `**상대 레포 코드**: \`python3 {UPDATE_PY} mirror --repo {slug} --wiki {WIKI_ROOT}\`가 낸 \`{미러}@{브랜치}\`로 \`git -C {미러} grep {패턴} {브랜치}\`·\`git -C {미러} show {브랜치}:{경로}\` — 기본 브랜치에 병합된 코드만 보임`
- **7**: "`●`는 로컬 사본, " 구절만 삭제

### skills/register/SKILL.md

- **21 기존 등록**: "`.local/paths.json`만 갱신해 6장으로"를 "변경 없이 6장으로"로
- **85**: `paths.json` 항목을 `**미러**: \`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" mirror --repo {slug} --wiki {WIKI_ROOT}\` — 실패 줄은 6장 보고에 싣고 등록은 그대로 진행`으로
- **92 상태 표**: 입력을 `registry.json`·`state/*.json`과 `update.py mirror` 출력으로, 마지막 열 `로컬 경로`를 `미러`(`있음` 또는 실패 사유)로

### skills/audit/SKILL.md

- **13 레포 줄**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" mirror --repo {slug}... --wiki {WIKI_ROOT}` 출력을 그대로 `catalog.md`에 이어 저장 — 24의 `{경로}@{브랜치}`·`없음` 규칙과 형식이 같아 진단 프롬프트는 그대로 둠

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `scripts/update.py`(`ensure_mirror`·`mirror`·pending·advance), `scripts/graph.py`의 `mirror_path` 추가만 | ① `python3 scripts/update.py mirror --wiki ~/.ai-docs/wiki` 출력이 `pigeon-trade /Users/rok/.ai-docs/wiki/.local/mirrors/pigeon-trade.git@develop`과 `pigeon-trade-dashboard …@main` 두 줄이고 두 폴더가 생김 ② 재실행 시 같은 두 줄이 clone 없이 나옴 ③ `git -C ~/.ai-docs/wiki/.local/mirrors/pigeon-trade.git log -1 --format=%H develop`이 `git -C /Users/rok/Desktop/Projects/pigeon-trade rev-parse origin/develop`과 같음(로컬 사본 fetch 후) ④ `python3 scripts/update.py pending --wiki ~/.ai-docs/wiki --out {스크래치}/t --repo pigeon-trade --range {develop 최근 머지 sha}^1..{그 sha}` 종료 코드 0, 생성된 `.diff`가 비지 않고 `skipped`에 pigeon-trade 없음 ⑤ `python3 scripts/update.py pending --wiki ~/.ai-docs/wiki --out {스크래치}/t2 --repo pigeon-trade-dashboard` 출력에 `대상 ref를 찾지 못함 (main)` — registry 값이 `main`인 현재 데이터 기준 기대 결과 ⑥ `python3 scripts/update.py advance pigeon-trade deadbeef --wiki {위키 사본}`이 종료 코드 1 — 실제 위키 state를 건드리지 않도록 `cp -R ~/.ai-docs/wiki {스크래치}/wiki`로 만든 사본에서 실행 |
| 2 | `scripts/graph.py` 나머지, `scripts/view.py`, `templates/graph.html`, `hooks/session_start.sh` | ① `python3 scripts/graph.py render --domain personal-stock-trading --slug pigeon-trade --wiki ~/.ai-docs/wiki` 헤더 2행이 `# 미러 /Users/rok/.ai-docs/wiki/.local/mirrors/{slug}.git · clone https://github.com/argon1025/{slug}.git`이고 `●` 없음 ② `python3 scripts/graph.py repo pigeon-trade --wiki ~/.ai-docs/wiki`에 `- 미러: /Users/rok/.ai-docs/wiki/.local/mirrors/pigeon-trade.git` ③ `python3 scripts/view.py --wiki ~/.ai-docs/wiki --no-open` 종료 코드 0 ④ `hooks/hooks.json`의 명령대로 훅을 `/Users/rok/Desktop/Projects/pigeon-trade`를 프로젝트 디렉터리로 실행해 출력에 `●`·`로컬 사본` 없고 agent-guide의 `{UPDATE_PY}`가 절대 경로로 치환되며, 실행 뒤 `~/.ai-docs/wiki/.local/paths.json`이 없음 ⑤ `grep -n "paths" scripts/graph.py scripts/view.py hooks/session_start.sh` 결과 0줄(`unlink` 줄 제외) |
| 3 | `rules/agent-guide.md`, `references/doc-contract.md`, `skills/update`·`audit`·`register` SKILL.md, `README.md`, `plugin.json` 5.2.0 | ① `grep -rn "paths.json\|로컬 사본\|로컬 패턴\|로컬 경로 없음" llm-wiki` 결과가 훅의 `unlink` 줄만 ② `grep -rn "●" llm-wiki` 결과 0줄 ③ `python3 -c "import json;print(json.load(open('llm-wiki/.claude-plugin/plugin.json'))['version'])"` 출력 `5.2.0` ④ 수정한 SKILL.md·README의 명령 줄이 커밋 1의 `mirror` 하위 명령 인자(`--repo`·`--wiki`)와 일치 |

## 특이 사항

- **범위 밖**: `pigeon-trade-dashboard`의 registry `defaultBranch`가 `main`으로 잘못 기록된 데이터 문제는 이 변경과 별개로 그 레포에서 `/llm-wiki:register --resurvey`로 고침
- **의도적 단순화**: 미러는 원격 기본 브랜치만 반영하므로 push하지 않은 로컬 작업과 다른 브랜치 코드는 에이전트에게 보이지 않음 — 업그레이드 조건: 병합 전 브랜치를 타 레포 기준으로 대조해야 하는 요청이 반복될 때 `mirror --ref` 인자 도입
- **인증**: 비공개 레포 clone은 이 머신의 git 자격 증명(HTTPS credential helper)에 의존하며, 실패는 `미러 clone 실패` 사유로 update 보고·register 상태 표에 드러남
- **디스크**: 레포마다 전체 이력 한 벌을 둠 — `--filter=blob:none`은 `git grep {rev}`가 blob을 지연 다운로드해 느려지므로 쓰지 않음
- **후속 작업**: 없음

## Re-plan 2026-09-26 — 구현 후 필요성 점검에서 중복·일회성 코드 제거

- **미러 노출 단일화**: 지도 헤더의 `# 미러 …` 부분과 `graph.py repo`의 `- 미러:` 필드를 넣지 않음 — 미러 경로는 `update.py mirror` 출력으로만 얻으며, `graph.py`는 미러를 모르고 `render_session`·`render_repo`·`map_block`은 `wiki` 인자 없이 동작함. `mirror_path`는 `update.py` 안으로 옮김
- **훅 정리 삭제**: 남은 `.local/paths.json`의 `unlink`를 두지 않음 — 어디서도 읽지 않는 미추적 파일이라 남아도 영향 없음
- **work.json `ref` 삭제**: 미러에서는 `branch`와 같은 값이고 소비처 없음
- **register 상태 표**: 전 레포 clone·fetch를 부르는 `update.py mirror` 대신 `{WIKI_ROOT}/.local/mirrors/{slug}.git` 폴더 유무로 `있음`·`없음`
- **검증 기대값 변경**: 커밋 2 ①의 헤더 2행은 `# clone https://github.com/argon1025/{slug}.git`, ②의 `- 미러:` 줄은 없음, ⑤·커밋 3 ①의 `paths.json` 잔존 결과는 0줄
