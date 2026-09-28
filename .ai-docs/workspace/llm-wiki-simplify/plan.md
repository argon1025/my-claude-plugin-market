# llm-wiki 단순화 — 기본 도구 중심 규약과 스크립트 정리 v5.6.0

## 의도

- **왜**: 세션 규약이 다른 레포 코드 읽기와 추가 조회를 자체 스크립트(`update.py mirror`·`graph.py repo`·`graph.py map`)와 bare 미러 `git -C` 절차로 안내해 에이전트가 Read·Grep·Glob을 쓰지 못하고 매 세션 설명 토큰을 쓰며, 실사용에서 조회 명령 0회·`/llm-wiki:add` 제안 62회 중 실행 3회로 규약 일부가 실효가 없고, 주입 용량 권고 기준(약 14,400자)이 Claude Code 절단 한도(10,000자)보다 커서 문서 목록이 경고 없이 잘릴 수 있음
- **누가**: 등록 레포에서 세션을 여는 모든 에이전트(매 세션 주입)와 register·update·audit를 실행하는 담당자
- **완료**: 규약이 스크립트 명령 없이 에이전트 기본 도구(파일 읽기·grep·git clone·fetch)만 안내하고, update는 위키 전용 일반 clone의 `origin/{기본 브랜치}`를 읽으며, `mirror`·`repo`·`map` 명령과 `survey.py`·`project` 키·update 조정 인자 3종이 사라지고, 주입이 9,000자를 넘으면 맨 앞에 권고가 붙는 llm-wiki 5.6.0이 릴리스됨

## 배경

- **주입 실측(5.5.0, pigeon-trade)**: 전체 4,366자 — 규약 1,078자, 레포 지도 372자, 도메인 문서 목록 17건 1,156자, 레포 문서 목록 25건 1,748자
- **세션 기록(pigeon 계열 83개, 2026-09-24~28)**: 6개 세션이 `update.py mirror` 6회 뒤 미러에 `git -C` grep·show·ls-tree·branch·for-each-ref 약 16회, `graph.py repo`·`map` 개발 세션 실행 0회, 위키 문서 경로 직접 읽기 약 190회·위키 grep 9회, `/llm-wiki:add` 제안 62회·실행 3회, update 19회(실행당 머지 0~4건), register 3회
- **feedback.md 경로**: pigeon-trade는 `.ai-docs/workspace/*/feedback.md`·`plan.md` 38개 파일을 커밋하므로 그 사실은 머지 diff로 update 추출에 이미 들어감
- **호출처**: `survey.py`는 register SKILL.md 2.5장 ①과 README 한 줄에서만 참조되고, `graph.py schema --for survey`는 이름만 같은 별개 기능임. `project` 키는 `graph.py` `render_map`·`check_repo`와 `view.py`·`templates/graph.html` 표시에서만 쓰임. `check_repo`의 `domains` 인자와 `catalog.py` CLI `--label`은 어디서도 쓰지 않음
- **작업 사본 위치**: 훅은 `{REPOS_DIR}`를 `Path(common_dir).parent.parent`로 계산하며 worktree(`~/orca/workspaces/pigeon-trade/*`)에서도 `~/Desktop/Projects`가 나옴
- **검토 문서**: 저장소 루트 `llm-wiki-simplify-review.md`(미추적)에 축별 검토 전문이 있음

## 확정 결정 (사용자 확인 2026-09-29)

- **목표**: 단순한 구조, 에이전트가 이미 아는 방법 위주(새 스크립트·프로세스는 다시 설명해야 해서 토큰 낭비), 토큰 절약
- **다른 레포 코드**: 사용자 프로젝트 폴더(`{REPOS_DIR}/{slug}`)에 사본이 있으면 그것을, 없으면 `{WIKI_ROOT}/.local/repos/{slug}`에 일반 clone해 자유롭게 읽고 고치며 기준은 fetch한 기본 브랜치 — update는 위키 전용 clone만 읽고 `update.py mirror`·bare 미러는 삭제
- **조회 명령**: `graph.py repo`·`map` 삭제, 규약 머리 문장에 정본 파일(`knowledge/`·`registry.json`·`deps.json`) 명시
- **project 키**: 이번에 삭제 — register owner 질문·check 검사·doc-contract·view.py 표시와 registry.json 노드 2개 정리
- **규약 문구**: `/llm-wiki:add` 제안 줄 삭제, 문서 열람 줄 축약, 목록 머리글의 토큰 어림을 문서 경로 패턴으로 교체
- **용량 한도**: 토큰 어림 대신 글자 수로 비교
- **스킬 절차**: `survey.py`와 register 인벤토리 대조 삭제, update `--batch-merges`·`--batch-bytes`·`--baseline-days` 삭제(묶음 상한 상수 유지, 소급은 `--range`) — 스킬 공통 절차·`graph.py schema`·`view.py`는 유지
- **적용 단위**: 5.6.0 한 릴리스, 축 단위 커밋으로 한 PR, 기존 `.local/mirrors/` 정리 포함

## 외부 계약

- **훅 출력**: `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}`, 어떤 실패에도 종료 코드 0
- **additionalContext 한도**: 필드당 10,000자, 넘으면 앞 2,000자 미리보기와 파일 경로만 남기고 경고 없음(https://github.com/anthropics/claude-code/issues/94358, 공식 문서 미기재)
- **일반 clone ref**: `git clone`은 fetch refspec `+refs/heads/*:refs/remotes/origin/*`을 두므로 `git fetch --prune origin` 뒤 `origin/{브랜치}`가 원격 최신이고, 로컬 브랜치·작업 트리는 fetch가 건드리지 않음
- **clone 주소**: registry `remote`(scheme 없는 정규화 꼴)로 `https://{remote}.git` — SSH 전용 비공개 레포는 `url."git@github.com:".insteadOf`로 우회(기존과 같음)

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/rules/agent-guide.md` | 전문 교체(아래) | ② 기존 파일 재작성 |
| `llm-wiki/hooks/session_start.py` | `{GRAPH_PY}`·`{UPDATE_PY}` 치환 삭제, 미등록 블록 재작성, 용량 권고 글자 수 기준 | ② 기존 분기 수정 |
| `llm-wiki/scripts/update.py` | bare 미러를 일반 clone으로, `mirror` 서브커맨드·조정 인자 3종·`baseline_before`·자체 `load_json` 삭제 | ② `ensure_mirror` 수정 |
| `llm-wiki/scripts/graph.py` | `repo`·`map`과 전용 함수, `project` 검사, `check_repo` 미사용 인자 삭제 | ① 삭제 |
| `llm-wiki/scripts/catalog.py` | 목록 머리글 경로화, `estimate_tokens`·`CHARS_PER_TOKEN`·CLI `--label` 삭제 | ② 수정 |
| `llm-wiki/scripts/survey.py` | 파일 삭제 | ① 삭제 |
| `llm-wiki/scripts/view.py`·`llm-wiki/templates/graph.html` | `project` 필드·표시 줄 삭제 | ① 삭제 |
| `llm-wiki/skills/register/SKILL.md` | 인벤토리 대조·미러·owner·project 서술 삭제 | ① 삭제 |
| `llm-wiki/skills/audit/SKILL.md` | 미러 출력 수집을 git clone·fetch 한 줄로 | ② 수정 |
| `llm-wiki/skills/update/SKILL.md` | 인자 3종·미러 표현 삭제 | ① 삭제 |
| `llm-wiki/skills/add/SKILL.md` | 5장 "프로젝트" 낱말 삭제 | ① 삭제 |
| `llm-wiki/references/doc-contract.md` | 8·9·10장의 project·미러·`repo` 서술 정리 | ② 수정 |
| `llm-wiki/README.md` | 동작 방식·위키 구조·무인 갱신·register 행 갱신 | ② 수정 |
| `llm-wiki/.claude-plugin/plugin.json` | `version` `5.6.0` — description은 삭제 기능을 언급하지 않아 유지 | ② 수정 |

### agent-guide.md 전문

훅이 `{WIKI_ROOT}`·`{REPOS_DIR}`·`{DOMAIN_DIR}`만 치환하고 `{slug}`·`{remote}`는 그대로 남음.

```markdown
# 위키 규약 (세션 전체 적용)

`{WIKI_ROOT}`의 문서(`knowledge/`)·레포 노드(`registry.json`)·의존 간선(`deps.json`)은 레포 밖에 공유할 사실과 코드에 없는 사실의 정본이며, 아래 레포 지도와 문서 목록은 그 요약임

- **레포 지도**: `(휴면)`은 고치지 않되 파급 확인에 포함하고, 의존 줄은 등록된 간선만 담은 힌트라 줄이 없어도 책임이 겹치는 레포는 코드로 확인
- **다른 레포 코드**: 계약·동작·사용처는 추측하지 않고 코드로 확인 — `{REPOS_DIR}/{slug}`가 있으면 그 사본을, 없으면 `{WIKI_ROOT}/.local/repos/{slug}`에 clone(`https://{remote}.git`)해 자유롭게 읽고 고치며, 기준은 fetch한 기본 브랜치
- **문서 열람**: 설명이 요청과 맞는 문서는 코드보다 먼저 열고, 목록에 없으면 `{DOMAIN_DIR}` 전체(다른 레포 폴더 포함)를 grep
- **모순 보고**: 문서끼리, 문서와 코드, 문서와 이유 없이 다른 요청은 고르지 않고 두 값을 병기해 알림
- **수정**: 위키는 `/llm-wiki:` 스킬로만 고침
```

### session_start.py

- **치환**: `{WIKI_ROOT}`·`{REPOS_DIR}`·`{DOMAIN_DIR}` 3개만 남기고 `graph_py` 변수 삭제
- **미등록·git 밖 블록**: 도메인 줄을 `- **도메인**: {domains} — 노드·간선은 {wiki}/registry.json·deps.json, 문서는 {wiki}/knowledge/{domain}`(경로는 백틱)으로 바꾸고 나머지 두 줄 유지
- **용량 권고**: `SOFT_BUDGET`을 `WARN_CHARS = 9_000`으로 바꾸고 `len(context) > WARN_CHARS`이면 맨 앞에 `# 위키 주입 {n:,}자 — 10,000자를 넘으면 뒤가 잘리므로 /llm-wiki:audit 로 정리 권장` 한 줄을 붙임 — 9,000은 절단 한도 10,000자 전에 권고가 보이도록 둔 여유이며 상수 옆 주석에 한도와 이슈 링크를 적음
- **catalog 호출**: `catalog.estimate_tokens` 참조 삭제

### update.py

- **clone 경로**: `mirror_path`를 `clone_path(wiki, slug)` = `{wiki}/.local/repos/{slug}`로
- **ensure_clone**: 없으면 `git clone --quiet https://{remote}.git {path}`(실패 시 폴더 삭제 후 `clone 실패 — {첫 줄}`), 있으면 `git remote set-url origin {url}` 뒤 `git fetch --prune --quiet origin`(실패 시 `fetch 실패 — 기존 ref 기준` 노트) — 작업 트리·로컬 브랜치는 세션 에이전트 몫이라 보지 않고 `origin/*` ref만 읽는다는 docstring
- **ref**: `pending`의 head 판정과 `advance`의 조상 판정을 `origin/{defaultBranch}`로, 스킵 사유를 `대상 ref를 찾지 못함 (origin/{branch})`로
- **advance**: clone 폴더가 없으면 `# clone 없음 — {path}` 오류
- **삭제**: `MIRROR_REFSPEC`, `cmd_mirror`와 `mirror` 파서, `--baseline-days`·`baseline_before`(부트스트랩 커서는 항상 HEAD), `--batch-merges`·`--batch-bytes`(상수를 `BATCH_MERGES`·`BATCH_BYTES`로 개명하고 `batches(rows)`가 직접 씀), 자체 `load_json`(`import catalog` 후 `catalog.load_json`)
- **docstring**: 모듈 머리의 미러·`mirror` 서술을 "위키 전용 clone(`{wiki}/.local/repos/{slug}`)의 `origin/*` ref를 읽고, 세션 에이전트도 같은 폴더를 씀"으로, 상태 표 서술의 "미러 폴더"를 삭제

### graph.py

- **삭제 함수**: `render_repo`·`render_map`·`responsibility_rows`·`owner_label`·`edge_row`·`endpoint_domain`·`cmd_map`·`cmd_repo`와 두 서브커맨드 파서
- **project**: `REPO_KEYS`에서 제거, `PROJECT_RE`와 `check_repo`의 project 블록 삭제
- **미사용 인자**: `check_repo`의 `domains` 인자와 호출부 `names` 삭제
- **docstring**: 모듈 머리의 `repo`·`map` 출력 서술을 "세션 주입(render_session)만 파생을 쓰고, 스택·호스트·remote·전체 간선은 에이전트가 registry.json·deps.json을 직접 읽음"으로, `via_pairs`의 "`repo` 출력이 함께 쓴다" 문장 삭제

### catalog.py

- **머리글**: `build`가 `# {label} {n}건 — {root}/{{이름}}.md`를 내고 토큰 어림과 관련 주석 삭제 — 훅 기준 `# 도메인 personal-stock-trading 17건 — /Users/rok/.ai-docs/wiki/knowledge/personal-stock-trading/{이름}.md`
- **삭제**: `estimate_tokens`·`CHARS_PER_TOKEN`, CLI `--label`(목록 모드는 `DEFAULT_LABEL`)

### 스킬·문서

- **register**: 1장 기존 등록의 "5장 미러만 확보하고" 삭제, 2.5장 ① 인벤토리 대조 삭제와 ②~⑤ 번호 당김, 3장 owner 불릿 삭제와 조사 초안 표의 owner 삭제, 4장 "8키"를 "7키"로·도메인 이동의 `project` 문구 삭제, 5장 미러 불릿 삭제, 6장 상태 표의 미러 열·미러 서술 삭제와 조사 품질의 `미소비 N행` 삭제(`선언 위치 위반 N건`만)
- **audit**: 1장 레포 불릿을 "대상 도메인 레포마다 `{WIKI_ROOT}/.local/repos/{slug}`가 없으면 `git clone https://{remote}.git`, 있으면 `git -C {경로} fetch --prune`을 실행해 `{slug} {경로}@origin/{defaultBranch}`(실패는 `{slug} 없음 — {오류 첫 줄}`)를 같은 catalog.md에 이어 저장"으로, 2장 프롬프트의 `{브랜치}`는 목록 줄의 `origin/{기본 브랜치}`
- **update**: 인자 줄에서 3종 삭제, 1장 이월의 "미러 준비 실패"를 "clone 준비 실패"로
- **add**: 5장 노드·간선의 "호스트·프로젝트와"를 "호스트와"로
- **doc-contract**: 8장 편집 주체 add 행 "`summary`·`project` 교체"를 "`summary` 교체"로, 9장 JSON 예시의 `project` 줄·`project` 불릿 삭제와 remote 불릿 "미러 clone이"를 "update와 세션의 clone이"로, 10장 대상 판정 "(`update.py mirror --repo {slug}`가 낸 미러)"를 "(사용자 사본 또는 `{WIKI_ROOT}/.local/repos/{slug}` clone)"로·경유 파생의 "`repo`의 `이 레포에 의존`은" 삭제 — 장 번호·제목은 스킬 sed 범위가 쓰므로 유지
- **README**: register 행의 "인벤토리 대조"·"owner", 동작 방식 주입 범위의 작업 사본·`graph.py repo`·`map` 서술을 규약 요약으로, 소프트 예산을 "주입이 9,000자를 넘으면 10,000자 절단 전에 권고 한 줄", 위키 구조의 `project` 괄호와 `.local/mirrors/{slug}.git` 줄을 `.local/repos/{slug}  # 위키 전용 clone (미추적, update가 clone·fetch, 세션 에이전트도 사용)`으로, `survey.py` 문장 삭제, 무인 갱신 대상을 "위키 전용 clone의 `origin/{기본 브랜치}`"로

## 커밋 분해

브랜치 `feat/llm-wiki-simplify` (main에서 분기). 픽스처 위키 `W=$TMPDIR/wiki-copy`는 실제 위키를 건드리지 않도록 복사본을 쓰며, 명령은 커밋별 H3에 있음. 기준선은 현재 실제 위키에서 `graph.py check` 에러 0·`catalog.py --check` 에러 0임.

| # | 범위 | 검증 |
|---|---|---|
| 0 | `docs(plan): llm-wiki 단순화 계획 스냅샷` — `.ai-docs/workspace/llm-wiki-simplify/plan.md`·`feedback.md` | `git show --stat HEAD`에 두 파일만 |
| 1 | `feat(llm-wiki): 다른 레포 코드를 사용자 사본 또는 위키 clone으로` — update.py(clone·ref·`mirror` 삭제·`load_json`), agent-guide.md 다른 레포 코드 줄, 훅 `{UPDATE_PY}` 삭제, register 1·5·6장 미러, audit 1·2장, update SKILL 1장, doc-contract 9·10장 미러, README 미러 서술 | 커밋 1 검증 전부 통과 |
| 2 | `feat(llm-wiki): 조회 명령 repo·map과 project 키 삭제` — graph.py, view.py, graph.html, 훅 `{GRAPH_PY}`·미등록 블록, agent-guide.md 머리 문장·추가 조회 삭제, register 3·4장, add 5장, doc-contract 8·9·10장, README | 커밋 2 검증 전부 통과 |
| 3 | `feat(llm-wiki): 규약 문구·목록 머리글·주입 용량 한도 정리` — agent-guide.md 최종 전문, catalog.py, 훅 용량 권고, README 소프트 예산 | 커밋 3 검증 전부 통과 |
| 4 | `refactor(llm-wiki): register 인벤토리 대조와 update 조정 인자 삭제` — survey.py 삭제, register 2.5·6장, update.py 인자 3종·`baseline_before`·`batches`, update SKILL 인자 줄, README survey 문장 | 커밋 4 검증 전부 통과 |
| 5 | `docs(llm-wiki): 버전 5.6.0` — plugin.json | 커밋 5 검증 전부 통과 |

### 커밋 1 검증

```bash
W=$TMPDIR/wiki-copy; rm -rf "$W"; rsync -a --exclude .local ~/.ai-docs/wiki/ "$W/"
python3 llm-wiki/scripts/update.py pending --wiki "$W" --out "$TMPDIR/out" --repo pigeon-trade --range c61a8ab^1..c61a8ab
git -C "$W/.local/repos/pigeon-trade" rev-parse --is-bare-repository
python3 llm-wiki/scripts/update.py advance pigeon-trade c61a8ab --wiki "$W"
python3 llm-wiki/scripts/update.py mirror; echo "exit $?"
grep -rniE 'mirror|미러' llm-wiki
```

- **pending**: 종료 0, `pigeon-trade: 머지 1건 · 묶음 1개` 출력, `$TMPDIR/out/work.json`의 `repos.pigeon-trade.path`가 `$W/.local/repos/pigeon-trade`이고 `$TMPDIR/out/pigeon-trade/c61a8ab.diff` 존재
- **clone**: `false`
- **advance**: 종료 0, `pigeon-trade 커서 c61a8ab` 출력
- **mirror**: `exit 2`
- **잔여**: grep 0건

### 커밋 2 검증

```bash
python3 llm-wiki/scripts/graph.py check --wiki "$W"; echo "exit $?"
# 특이 사항의 이행 스크립트에서 W만 "$W"로 바꿔 registry.json 부분만 실행
python3 llm-wiki/scripts/graph.py check --wiki "$W"; echo "exit $?"
python3 llm-wiki/scripts/graph.py repo pigeon-trade; echo "exit $?"
python3 llm-wiki/scripts/view.py --wiki "$W" --no-open --out "$TMPDIR/g.html" && grep -c '"project"' "$TMPDIR/g.html"
grep -rnE "\"project\"|'project'|\`project\`|graph\.py.{0,2} (repo|map)|render_repo|render_map|owner_label|PROJECT_RE" llm-wiki
```

- **이행 전 check**: `허용되지 않는 키: project` 에러 2건, `exit 1`
- **이행 후 check**: 에러 0건, `exit 0`
- **repo**: `exit 2`
- **view**: 종료 0, 카운트 `0`
- **잔여**: grep 0건

### 커밋 3 검증

```bash
run() { echo '{"source":"clear"}' | CLAUDE_PROJECT_DIR="$1" python3 llm-wiki/hooks/session_start.py | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'; }
run ~/Desktop/Projects/pigeon-trade > "$TMPDIR/pt.md"
run "$PWD" > "$TMPDIR/unreg.md"
run "$TMPDIR" > "$TMPDIR/nogit.md"
for i in $(seq 1 200); do printf -- '---\ndescription: 더미 문서 %s번을 다룰 때\ntype: convention\n---\n\n# 더미 %s\n' "$i" "$i" > "$W/knowledge/personal-stock-trading/pigeon-trade/dummy-doc-$i.md"; done
echo '{"source":"clear"}' | LLM_WIKI_ROOT="$W" CLAUDE_PROJECT_DIR=~/Desktop/Projects/pigeon-trade python3 llm-wiki/hooks/session_start.py > "$TMPDIR/big.json"; echo "exit $?"
python3 llm-wiki/scripts/catalog.py --root ~/.ai-docs/wiki/knowledge/personal-stock-trading --shallow | head -1
grep -rnE 'estimate_tokens|CHARS_PER_TOKEN|SOFT_BUDGET|--label' llm-wiki
```

- **pigeon-trade**: `# 위키 규약`으로 시작, `/Users/rok/Desktop/Projects/{slug}`·`/Users/rok/.ai-docs/wiki/.local/repos/{slug}`·`registry.json` 포함, `python3`·`토큰`·`/llm-wiki:add` 없음, 길이 4,366자 미만
- **미등록**: `# 위키 규약`·`python3` 없음, `registry.json` 포함, 길이 500자 미만
- **git 밖**: `git 레포 밖` 포함, `python3` 없음
- **용량 권고**: `exit 0`, `big.json`의 `additionalContext`가 `# 위키 주입`으로 시작
- **catalog**: 첫 줄이 `# 위키 17건 — /Users/rok/.ai-docs/wiki/knowledge/personal-stock-trading/{이름}.md`
- **잔여**: grep 0건

### 커밋 4 검증

```bash
rm -rf "$TMPDIR/out"
python3 llm-wiki/scripts/update.py pending --wiki "$W" --out "$TMPDIR/out" --repo pigeon-trade --range c61a8ab^1..c61a8ab
python3 llm-wiki/scripts/update.py pending --wiki "$W" --out "$TMPDIR/o2" --baseline-days 3; echo "exit $?"
grep -rnE 'survey\.py|inventory|baseline|batch-merges|batch-bytes|미소비' llm-wiki
```

- **pending**: 종료 0, `머지 1건 · 묶음 1개`
- **제거 인자**: `exit 2`
- **잔여**: grep 0건

### 커밋 5 검증

```bash
python3 -m json.tool llm-wiki/.claude-plugin/plugin.json | grep '"version"'
python3 -m py_compile llm-wiki/scripts/*.py llm-wiki/hooks/session_start.py && echo ok
```

- **버전**: `"version": "5.6.0"`
- **컴파일**: `ok`, 생성된 `__pycache__`는 커밋하지 않음

## 특이 사항

- **머지 후 이행**: PR 머지와 `/plugin` 갱신(5.6.0) 직후 아래를 실행함 — 갱신 전에 실행하면 5.5.0 check가 `필수 키 없음: project`를, 갱신 후 미실행이면 5.6.0 check가 `허용되지 않는 키: project`를 내어 add·update·register가 멈추므로 두 단계를 붙여 실행하고, 첫 update는 `.local/repos/`에 레포를 새로 clone함

```bash
W=~/.ai-docs/wiki
python3 - "$W/registry.json" <<'EOF'
import json, sys
path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
for domain in data["domains"].values():
    for node in domain["repos"].values():
        node.pop("project", None)
open(path, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
EOF
python3 ~/.claude/plugins/cache/my-claude-plugin-market/llm-wiki/5.6.0/scripts/graph.py check --wiki "$W"
git -C "$W" commit -am "docs(graph): project 키 삭제" -m "사용자 확인" && git -C "$W" pull --rebase && git -C "$W" push
rm -rf "$W/.local/mirrors"
```

- **병렬 세션 공유**: 같은 머신의 병렬 세션이 `.local/repos/{slug}` 작업 트리 하나를 공유하므로 동시 수정은 에이전트가 worktree로 나눠야 함 — 충돌이 반복되면 규약에 worktree 사용을 명시하는 것이 업그레이드 조건
- **사용자 사본 신선도**: `{REPOS_DIR}/{slug}` 사본은 기능 브랜치나 미커밋 상태일 수 있어 규약이 "기준은 fetch한 기본 브랜치"만 안내하며, 사용자 작업 트리의 브랜치 전환 여부는 에이전트 판단에 맡김
- **다중 홉 추적**: `graph.py repo`가 사라져 fe → bff → 서비스 같은 2홉 추적은 에이전트가 `deps.json`을 직접 읽어 수행함
- **범위 밖**: `graph.py schema`·스킬 공통 절차(pull·check·push)·`view.py` 화면은 유지, `llm-wiki-simplify-review.md`는 미추적 검토 문서로 두고 커밋하지 않음
