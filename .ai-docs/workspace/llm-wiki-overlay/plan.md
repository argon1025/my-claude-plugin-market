# llm-wiki 변형 분리 구조 전환 v5.7.0

## 의도

- **왜**: 회사판(devcenter-llm-wiki)이 개인판 4.0.0을 파일째 복사해 수정한 사본이라, 개인판 버전업 때마다 16개 파일에 흩어진 이격을 손으로 찾아 다시 적용해야 함
- **누가**: 두 플러그인을 관리하는 사용자가 개인판 릴리스 뒤 회사판을 sync할 때마다 겪음
- **완료**: 개인판 안의 이격 지점이 분리 파일과 치환 규칙으로만 모이고, 병합 스크립트가 '개인판 + 오버레이'로 변형 플러그인을 생성하며, 개인판 동작과 세션 주입 토큰은 현행과 같음. 회사 오버레이 작성과 회사판 sync는 다음 작업이고, 오버레이는 회사 레포에 둠(개인 레포가 공개이기 때문)

## 배경

- **기준본**: 회사판 4.0.0은 개인 레포 커밋 `fd3664f`(llm-wiki v4.0.0)와 같은 시점이며, 회사 전용 이격은 `git archive fd3664f llm-wiki`와 `onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-llm-wiki`의 diff로 추출됨
- **공개 레포**: `argon1025/my-claude-plugin-market`은 PUBLIC이라 사내 URL(`bitbucket.onestorecorp.com` 등)·사내 호스트를 개인판과 이 레포의 어떤 파일에도 넣지 않음
- **현행 동기화**: `llm-wiki/hooks/session_start.py` `sync()`는 startup·resume에서 `FETCH_HEAD`가 10분(`LLM_WIKI_SYNC_MINUTES`)보다 오래됐을 때만 `pull --ff-only`를 걸고 3초 기다림, clear·compact·fork는 pull하지 않음, 세션 도중 자동 갱신 없음
- **현행 게시**: init·register·add·audit은 끝에 `git -C {WIKI_ROOT} pull --rebase && git push`로 `main` 직접 push, update만 `wiki-update/*` 브랜치 + `gh pr create`
- **단일 경로 소스**: 위키 루트는 `llm-wiki/scripts/graph.py:31` `DEFAULT_WIKI` 한 곳에서 정해지고 훅·update.py가 이를 가져다 씀
- **환경변수 미사용**: `LLM_WIKI_SYNC_MINUTES`는 사용자 settings 어디에도 설정되어 있지 않음
- **실행 비트**: `llm-wiki/hooks/session_start.py`는 `hooks.json`이 직접 실행하므로 `-rwxr-xr-x` 권한이 필요함

### 이격 목록과 판정 (회사 4.0.0 vs 개인 4.0.0, 버전 차이 제외)

| # | 이격 | 판정 | 분리 수단 |
|---|---|---|---|
| 1 | 플러그인 식별(name·description·author·keywords), README 설치 안내 | 유지 | 오버레이 파일 교체(`plugin.json`은 얕은 병합) |
| 2 | 스킬 네임스페이스 `/llm-wiki:` → `/devcenter-llm-wiki:` | 유지 | `overlay.json` 치환 |
| 3 | 위키 루트 환경변수·기본 경로(`LLM_WIKI_ROOT`·`~/.ai-docs/wiki`) | 유지(병행 설치 조건) | `overlay.json` 치환 |
| 4 | 쓰기 게시 절차(회사: 쓰기 전부 브랜치 + onestore MCP PR·`master`·직접 push 금지·MCP 부재 시 수동 URL) | 유지 | `references/publish.md` 파일 교체 |
| 5 | 위키 저장소 고정(clone URL 고정, init 질문 생략) | 유지 | `publish.md` 머리 `저장소` 불릿 |
| 6 | 훅 자동 복제(락·스테이징·실패 게이트) | 제거 | 회사 사용자는 init 1회 실행 |
| 7 | 훅 잔여 브랜치 감지·머지 대기 PR 건수 헤더 | 제거 | `publish.md` 1장 점검으로 대체 |
| 8 | 노드 `project` 필드·Bitbucket 프로젝트 키 파생 | 제거 | 개인판 5.x에서 폐지됨, `https://{remote}.git`이 Bitbucket에서도 동작 |
| 9 | 포크 `/~` 검사·포크 정본 MCP 조회 | `/~`는 개인판 흡수, MCP 조회 제거 | `graph.py` check·register 문구 |
| 10 | 기본 브랜치 초안값 `develop`, 사내 문구·예시 도메인, 규약 제목, VPN 안내, `graph.html` 표기 | 제거 | 개인판 중립 문구로 통일 |

## 확정 결정 (사용자 확인 2026-09-29)

- **의도**: 위 3문장 그대로
- **자동 복제**: 제거에 동의, 대신 세션을 시작할 때마다 pull
- **분리 방식**: 분리 파일 교체 — 스킬 5종의 저장소 절차를 `references/publish.md` 한 파일로 모으고 회사는 이 파일을 통째로 교체
- **정리 항목**: 표의 7·9·10을 권장대로 일괄 처리
- **동기화 주기**: 10분 조건과 `LLM_WIKI_SYNC_MINUTES`를 없애고 startup·resume마다 pull(clear·compact·fork는 현행대로 pull 없음, 3초 대기와 늦을 때 이전 사본 주입은 유지)
- **스크립트 위치**: 병합 스크립트는 개인 레포 루트 `tools/overlay.py`(사내 데이터 없음), 오버레이 데이터는 회사 레포

## 선행 읽기

- `llm-wiki/skills/update/SKILL.md` 1·7장: 옮길 `gh`·`main`·stash 문장의 원문
- `onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-llm-wiki/references/publish.md`: 같은 이름 파일의 회사판 구성(시작·브랜치·PR·종료) — 개인판 절 구성이 이것과 대응하도록 맞춤, 사내 URL은 옮기지 않음

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/references/publish.md` | 신설 — 저장소·기준 브랜치·커밋 링크 머리 불릿과 1 시작·2 브랜치·3 게시·4 종료 | ② 회사판 `publish.md` 구성 재사용, 내용은 기존 스킬 문장 이동 |
| `llm-wiki/skills/{init,register,add,audit,update}/SKILL.md` | 인라인 `pull`·`push`·`gh`·`switch main`·stash 문장을 `publish.md` 장 참조로 교체 | ② 기존 문장 이동 |
| `llm-wiki/templates/update-pr.md` | 커밋 링크를 `publish.md` 꼴로, `main`을 기준 브랜치로 | ② |
| `llm-wiki/hooks/session_start.py` | `sync()`의 10분 조건·`LLM_WIKI_SYNC_MINUTES`·`import time` 제거 | ① 조건 삭제 |
| `llm-wiki/scripts/graph.py` | `check_repo` remote 검사에 `/~` 개인 네임스페이스 에러 1분기 | ⑥ |
| `llm-wiki/references/doc-contract.md` | 9장 remote 불릿에 `/~` 개인 네임스페이스 금지 명시 | ⑥ |
| `tools/overlay.py` | 신설 — base 복사 + 교체 파일 + 치환 + 드리프트 검사 + 원자 교체 | ⑦ |
| `llm-wiki/README.md` | 동기화 문장 갱신, `## 변형 배포` 절 신설 | ② |
| `llm-wiki/.claude-plugin/plugin.json` | version `5.7.0` | ⑥ |

### llm-wiki/references/publish.md

아래 내용을 그대로 씀. 절 제목 4개는 스킬이 참조하고 `tools/overlay.py`가 교체 파일과 대조하는 계약이라 문구까지 고정함.

````markdown
# 위키 저장소 절차

쓰기 스킬(init·register·add·audit·update)이 위키 사본을 다루는 시작과 끝입니다. 변형 배포는 이 파일을 통째로 바꾸므로 `##` 절 제목은 스킬이 참조하는 계약이며 바꾸지 않습니다.

- **저장소**: 고정하지 않음 — init이 clone URL 또는 새로 만들기를 물음
- **기준 브랜치**: `main`
- **커밋 링크**: `https://{remote}/commit/{sha}` — `remote`는 registry 노드 값

## 1. 시작

- **동기화**: `git -C {WIKI_ROOT} switch main && git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단(팀원 커밋과 갈라진 상태에서 편집 금지)
- **열린 update PR**: update이고 `--dry-run`이 아니면 `WIKI_ROOT`에서 `gh pr list --state open --json url,headRefName` — `wiki-update/` 브랜치 PR이 있으면 그 링크를 보고하고 중단(머지 전 재실행은 같은 머지를 두 번 추출함), 명령이 실패하면(GitHub 원격 없음·미인증) 오류 한 줄을 보고하고 중단

## 2. 브랜치

- **update**: 추적 파일을 처음 고치기 전에 `git -C {WIKI_ROOT} switch -c wiki-update/{YYYYMMDD-HHMM}`
- **그 외**: 브랜치 없이 `main`에서 편집·커밋

## 3. 게시

- **update**: `git -C {WIKI_ROOT} push -u origin {branch}` 후 `WIKI_ROOT`에서 `gh pr create --base main --head {branch} --title "update: {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장" --body-file {본문}` — 실패하면 단계·브랜치 이름·오류 한 줄 보고
- **긴 본문**: 본문이 60,000바이트를 넘으면 `추출 사실` 절을 떼어 본문에 "사실 원장은 첫 코멘트" 한 줄을 두고, PR 생성 뒤 뗀 절을 `gh pr comment {url} --body-file`로 게시
- **그 외**: `git -C {WIKI_ROOT} pull --rebase && git -C {WIKI_ROOT} push` — 실패는 로컬 커밋 상태와 함께 보고
- **변경 0건**: 커밋이 없으면 게시하지 않고, 브랜치를 만들었으면 `git -C {WIKI_ROOT} switch main && git -C {WIKI_ROOT} branch -D {branch}`

## 4. 종료

- **복귀**: 브랜치를 만든 실행은 성공·실패와 무관하게 어느 단계에서 끝나든 미커밋 편집을 `git -C {WIKI_ROOT} stash -u`로 치우고 `git -C {WIKI_ROOT} switch main` — 세션 주입과 다른 쓰기 스킬이 미승인 편집을 읽지 않게 함
- **보고**: push한 스킬은 "다음 세션 목록에 반영", update는 PR 링크와 "머지 후 다음 세션에 반영"
````

### llm-wiki/skills/*/SKILL.md

- **공통 도입문**: 각 스킬 첫 문단의 규약 경로 문장에 "저장소 절차는 `${CLAUDE_PLUGIN_ROOT}/references/publish.md`(시작 전에 Read)"를 덧붙임
- **init**: 1장 `registry.json 있음`의 `git pull --ff-only`를 `publish.md` 1장으로, 2장 질문 앞에 "`publish.md` 저장소 불릿에 clone URL이 있으면 묻지 않고 그 URL로 clone"을 두고, `git init -b main`은 `-b {기준 브랜치}`로, 3장 골격 첫 줄에 "`publish.md` 2장 뒤 아래 파일을 씀", 3장 `원격`은 "새로 만든 저장소는 URL을 받았으면 `git remote add origin {URL}`과 `git push -u origin {기준 브랜치}`, clone한 저장소는 `publish.md` 3·4장"
- **register**: 1장 `위키`의 pull을 `publish.md` 1장으로, 1장 정본 remote 2번을 "없으면 `origin` — upstream 없이 owner가 개인 계정이거나 경로에 개인 네임스페이스(`/~`)가 있어 포크인지 불명확하면 여기서 확정하지 않고 `포크 의심`으로 표시만 함", `기존 등록`의 "커밋·push 없이"를 "커밋·게시 없이", 4장 첫 줄에 "편집 전 `publish.md` 2장", 5장 제목을 `검사·커밋·게시`로 바꾸고 push 불릿을 "**게시**: `publish.md` 3·4장"
- **add**: 1장 `저장소 상태`의 pull을 `publish.md` 1장으로, 5장 `초안` 뒤에 "**브랜치**: 승인 뒤 `publish.md` 2장", push 불릿을 "**게시**: `publish.md` 3·4장", 6장 `반영 시점`을 "`publish.md` 4장 보고"
- **audit**: 1장 `동기화`를 `publish.md` 1장으로, 3장 `0행` 뒤에 "**브랜치**: 적용할 행이 있으면 `publish.md` 2장", 5장 제목을 `검증·커밋·게시`로 바꾸고 push 불릿을 "**게시**: `publish.md` 3·4장"
- **update**: 도입문의 "`wiki-update/*` 브랜치 PR … `main`으로 돌아옵니다" 두 문장을 "반영은 PR 머지로 승인되며 동기화·브랜치·PR·복귀는 `publish.md`를 따릅니다"로, 1장 `열린 PR`·`동기화` 두 불릿을 "**저장소**: `publish.md` 1장 — 열린 update PR 확인 포함"으로, 1장 `작업 브랜치`를 "종료 코드 0이고 `--dry-run`이 아니면 `publish.md` 2장"으로, 7장 `빈 실행`·`push·PR`·`긴 본문`·`복귀`를 "**게시**: `{스크래치}/pr.md`를 본문으로 `publish.md` 3·4장" 한 불릿으로 합치고 `본문`·`터미널`은 유지
- **결과 조건**: 스킬 본문에 `pull --rebase`·`gh pr`·`switch main`·`--base main`이 남지 않고, `git push`는 init의 새 저장소 첫 push 한 줄만 남음 — 원격 추적이 없어 `publish.md` 3장 `pull --rebase`가 실패하는 유일한 경로라 init에 둠

### llm-wiki/templates/update-pr.md

- **레포 채우는 법**: "`https://{registry.json remote}/commit/{sha}` 링크"를 "`publish.md` 커밋 링크"로
- **예시 행**: `[c61a8ab](https://github.com/{owner}/pigeon-trade/commit/{sha})`를 `[c61a8ab]({커밋 링크})`로
- **전체 거절**: "커서가 `main`에 반영되지 않아"를 "커서가 기준 브랜치에 반영되지 않아"로

### llm-wiki/hooks/session_start.py

- **sync()**: `git_dir`·`minutes`·`fetched` 계산과 10분 비교를 지우고 `source`가 startup·resume이 아니거나 `origin`이 없으면 빈 문자열, 그 밖에는 항상 `pull --ff-only`를 3초 기다리는 현행 Popen 부분만 남김
- **docstring**: "마지막 fetch가 주기보다 오래됐으면"을 "startup·resume마다"로
- **import**: 쓰이지 않게 되는 `import time` 제거
- **불변**: 주입 블록 구성·문구는 바꾸지 않음 — 세션 주입 토큰 동일 조건

### llm-wiki/scripts/graph.py

- **check_repo**: `"://" in remote` 분기 다음에 `elif remote and "/~" in remote:` 분기를 두고 `f"{label}: remote {remote}가 개인 네임스페이스 — 정본만 적음"` 에러를 냄

### tools/overlay.py

⑦ 판정 근거: `cp`·`sed`로는 치환 적중 수 검사, `plugin.json` 얕은 병합, 절 제목 대조, 실패 시 출력 불변을 BSD·GNU 공통으로 보장할 수 없어 표준 라이브러리만 쓰는 Python 한 파일로 둠.

- **사용법**: `python3 tools/overlay.py --base {개인판 플러그인 폴더} --overlay {오버레이 폴더} --out {출력 플러그인 폴더}`
- **오버레이 구성**: `overlay.json`(`{"replace": {"원문": "대체문"}}`, 다른 최상위 키는 에러)과 base와 같은 상대 경로의 교체 파일
- **수집 제외**: `__pycache__/`, `*.pyc`, `.DS_Store`
- **교체 파일**: base에 같은 경로가 없으면 에러 — 개인판에서 파일 이름이 바뀐 드리프트를 잡음
- **plugin.json**: `.claude-plugin/plugin.json`만 base JSON 위에 오버레이 JSON을 얕게 병합 — `version`은 오버레이가 지정하지 않으면 base를 따름
- **절 제목 계약**: `README.md`를 뺀 `.md` 교체 파일은 `## `로 시작하는 줄 목록이 base와 같아야 하며 다르면 두 목록을 보이고 에러
- **치환 대상**: base에서 온 파일 중 UTF-8로 읽히는 파일에만 적용하고 교체 파일·병합한 `plugin.json`에는 적용하지 않음 — 교체 파일은 이미 변형 표기라 `LLM_WIKI_`가 `DEVCENTER_LLM_WIKI_` 안에서 다시 치환되는 이중 치환을 막음
- **치환 방식**: 긴 키 우선 정렬한 `re.escape` 교대 패턴 한 번으로 치환해 연쇄 치환을 막고 키별 적중 수를 셈, 적중 0건 키가 있으면 에러 — 개인판 문구 변경 드리프트를 잡음
- **바이너리**: UTF-8로 읽히지 않는 파일은 바이트 그대로 복사
- **권한**: 모든 파일에 `shutil.copymode`로 base(교체 파일은 오버레이) 권한 유지 — 훅 실행 비트
- **출력 안전**: `--out`이 base·오버레이와 같거나 서로 포함 관계면 거부, `--out`이 있는데 `.claude-plugin/plugin.json`이 없으면 거부
- **원자 교체**: `--out` 부모에 `tempfile.mkdtemp`로 만든 임시 폴더에 전부 생성하고 검사를 통과한 뒤에만 기존 `--out`을 지우고 `os.replace` — 에러 시 임시 폴더만 지우고 `--out`은 그대로, base에 없는 기존 출력 파일(예: 이전 버전의 `survey.py`)은 이 교체로 사라짐
- **출력·종료 코드**: 성공 시 파일 수·교체 파일 목록·키별 적중 수를 출력하고 0, 에러는 모두 모아 stderr에 출력하고 1

### llm-wiki/README.md

- **동기화 불릿**: "startup·resume에서 마지막 fetch가 10분(`LLM_WIKI_SYNC_MINUTES`)을 넘었을 때"를 "startup·resume마다"로, 쓰기 스킬 절차는 "`references/publish.md`(시작에 동기화, 끝에 push 또는 update PR)"로
- **`## 변형 배포` 절 신설(`## 한계` 앞)**: 분리 지점은 저장소 절차 `references/publish.md` 한 파일과 스킬 네임스페이스·환경변수·위키 기본 경로 문자열이며, `tools/overlay.py` 사용법과 실패 조건 3종(치환 적중 0건, base에 없는 교체 파일, `publish.md` 절 제목 불일치)을 불릿 2~3개로 적음

## 커밋 분해

작업 브랜치는 `main`에서 만든 `feat/llm-wiki-overlay`이며, 명령은 레포 루트에서 실행하고 `{S}`는 세션 스크래치 디렉터리임.

| # | 범위 | 검증 |
|---|---|---|
| 0 | 착수 전 훅 기준 출력 저장(커밋 없음) | 아래 `검증 0` — 출력 파일 3개가 비어 있지 않음 |
| 1 | `refactor(llm-wiki): 저장소 절차를 references/publish.md로 분리` — publish.md 신설, 스킬 5종, update-pr.md | 아래 `검증 1` — 첫 grep 0줄, 둘째 grep은 init의 새 저장소 첫 push 1줄뿐, 스킬 5개 모두 `publish.md` 2회 이상, 절 제목 4줄, validate 통과(기존 hooks.json 따옴표 경고 1건은 범위 밖) |
| 2 | `feat(llm-wiki): 세션 시작마다 위키 pull, 개인 네임스페이스 remote 검사` — session_start.py, graph.py, doc-contract.md 9장 | 아래 `검증 2` — diff 3건 빈 출력, FETCH_HEAD 경과 10초 이하, `~me` 노드에서만 `개인 네임스페이스` 출력, 잔여 grep 0줄 |
| 3 | `feat: 변형 플러그인 병합 스크립트 tools/overlay.py` | 아래 `검증 3` — 성공 실행 조건 전부 참, 실패 5종 모두 종료 코드 1이고 출력 해시 불변, stale 파일 제거 |
| 4 | `docs(llm-wiki): README 변형 배포·동기화 갱신, 버전 5.7.0` | 아래 `검증 4` — version 1줄, 잔여 grep 0줄, 절 1줄, validate 통과 |

### 검증 0

```bash
S={S}; mkdir -p $S/reg && git -C $S/reg init -q && git -C $S/reg remote add origin https://github.com/argon1025/pigeon-trade
for p in reg:$S/reg unreg:$PWD nogit:/tmp; do
  echo '{"source":"clear"}' | CLAUDE_PROJECT_DIR=${p#*:} python3 llm-wiki/hooks/session_start.py > $S/hook-before-${p%%:*}.txt
done
wc -c $S/hook-before-*.txt
```

### 검증 1

```bash
grep -rnE 'pull --rebase|gh (pr|api)|switch main|--base main' llm-wiki/skills llm-wiki/templates
grep -rn 'git push' llm-wiki/skills llm-wiki/templates
grep -c 'publish.md' llm-wiki/skills/*/SKILL.md
grep -c '^## ' llm-wiki/references/publish.md
claude plugin validate llm-wiki
```

### 검증 2

```bash
S={S}
for p in reg:$S/reg unreg:$PWD nogit:/tmp; do
  echo '{"source":"clear"}' | CLAUDE_PROJECT_DIR=${p#*:} python3 llm-wiki/hooks/session_start.py | diff $S/hook-before-${p%%:*}.txt -
done
F=~/.ai-docs/wiki/.git/FETCH_HEAD; touch -t $(date -v-1M +%Y%m%d%H%M.%S) $F
echo '{"source":"startup"}' | python3 llm-wiki/hooks/session_start.py >/dev/null
echo $(( $(date +%s) - $(stat -f %m $F) ))   # 10 이하 — 구 코드는 1분 전 fetch라 pull하지 않아 60 이상
mkdir -p $S/w && echo '{"deps": {}}' > $S/w/deps.json
for r in '~me' me; do
  printf '{"domains":{"acme-x":{"description":"d","repos":{"x":{"remote":"github.com/%s/x","defaultBranch":"main","status":"active","stack":["Go"],"summary":"s","responsibilities":["x 관리"],"hosts":{}}}}}}' "$r" > $S/w/registry.json
  python3 llm-wiki/scripts/graph.py check --wiki $S/w | grep -c '개인 네임스페이스'   # ~me 1 이상, me 0
done
grep -n 'SYNC_MINUTES\|import time' llm-wiki/hooks/session_start.py
```

### 검증 3

스크래치 오버레이 `{S}/ov`를 만듦: `overlay.json`은 `{"replace": {"/llm-wiki:": "/acme-llm-wiki:", "LLM_WIKI_": "ACME_LLM_WIKI_", "~/.ai-docs/wiki": "~/.acme/wiki"}}`, `.claude-plugin/plugin.json`은 `{"name": "acme-llm-wiki"}`, `references/publish.md`는 개인판을 복사해 본문 한 줄만 바꾼 것, `README.md`는 임의 한 줄.

```bash
S={S}; O=$S/out
python3 tools/overlay.py --base llm-wiki --overlay $S/ov --out $O; echo "exit=$?"            # 0
grep -rn '/llm-wiki:' $O | wc -l                                                              # 0
python3 -c "import json;a=json.load(open('$O/.claude-plugin/plugin.json'));b=json.load(open('llm-wiki/.claude-plugin/plugin.json'));print(a['name'], a['version']==b['version'])"   # acme-llm-wiki True
test -x $O/hooks/session_start.py && echo exec-ok
find $O -name __pycache__ | wc -l                                                             # 0
echo '{"source":"clear"}' | ACME_LLM_WIKI_ROOT=~/.ai-docs/wiki CLAUDE_PROJECT_DIR=$S/reg python3 $O/hooks/session_start.py | grep -c '/acme-llm-wiki:'   # 1 이상
H=$(find $O -type f | sort | xargs shasum | shasum)
```

실패 5종은 하나씩 적용했다가 되돌리며 각각 `exit=1`이고 실행 뒤 `find $O -type f | sort | xargs shasum | shasum`이 `$H`와 같아야 함: ① `replace`에 `"NO_SUCH_TOKEN": "x"` 추가 ② `$S/ov/references/nope.md` 생성 ③ `$S/ov/references/publish.md`의 `## 3. 게시`를 `## 3. PR`로 변경 ④ `--out llm-wiki` ⑤ `--out $S/plain`(plugin.json 없는 기존 폴더). 끝으로 `touch $O/stale.txt` 뒤 성공 명령을 다시 실행하면 `test -e $O/stale.txt`가 실패함.

### 검증 4

```bash
grep -n '"version": "5.7.0"' llm-wiki/.claude-plugin/plugin.json
grep -n 'SYNC_MINUTES\|10분' llm-wiki/README.md
grep -n '^## 변형 배포' llm-wiki/README.md
claude plugin validate .
```

## 특이 사항

- **범위 밖**: 회사 오버레이 작성, 회사판 5.7.0 sync, 회사 레포 marketplace.json 갱신, 다른 플러그인 쌍(pr-workflow↔devcenter-pr 등)의 분리, `hooks.json` 따옴표 경고
- **동시 시작 한계**: 10분 조건을 없애 여러 세션이 동시에 시작하면 pull이 겹쳐 한쪽이 `위키 동기화 실패` 알림을 낼 수 있음 — 사본은 다른 쪽 pull로 최신이 되며, 알림이 잦으면 짧은 주기 조건을 되살리는 것이 업그레이드 조건
- **세션 도중 갱신 없음**: pull 시점은 startup·resume과 쓰기 스킬 시작뿐이라 긴 세션 중 팀원 머지는 다음 세션에 보임
- **토큰 영향**: 세션 주입은 불변(커밋 2의 hook diff로 확인), 쓰기 스킬 실행마다 `publish.md` Read 1회(약 2KB)가 늘고 스킬 본문의 인라인 절차 문장은 줄어듦
- **후속 작업(회사판 sync)**: 회사 레포에 `overlays/llm-wiki/`(`overlay.json`·`.claude-plugin/plugin.json`·`README.md`·`references/publish.md`)를 두고 `tools/overlay.py`로 `plugins/devcenter-llm-wiki`를 생성함. 회사 `publish.md`는 절 제목을 `## 1. 시작`·`## 2. 브랜치`·`## 3. 게시`·`## 4. 종료`로 재구성하고 `## 금지` 절 내용은 이 4개 절 안 불릿으로 옮겨야 함. 회사 위키 `registry.json`의 노드 `project` 키는 5.x `graph.py check`에서 허용되지 않는 키이므로 제거 마이그레이션이 필요함. 자동 복제 제거로 회사 사용자는 첫 세션에 init을 한 번 실행하며, init은 `publish.md` 저장소 불릿의 고정 URL을 묻지 않고 clone함

## Re-plan 2026-09-29 — 빈 원격 clone에서 pull --rebase 실패

- **계기**: 빈 원격을 clone한 위키에서 첫 커밋 뒤 `git pull --rebase`는 `no such ref was fetched`로 실패하고 `git push`는 성공함(git 2.39.5 재현) — init이 골격을 쓰는 주 경로라 계획의 "clone한 저장소는 `publish.md` 3·4장"으로는 게시가 실패함
- **변경**: init 3장 `원격` 불릿을 "원격에 기준 브랜치가 없으면(새로 만든 저장소·빈 원격 clone) URL이 있을 때 `git remote add origin {URL}` 뒤 `git push -u origin {기준 브랜치}`, 그 밖의 clone은 `publish.md` 3·4장"으로 씀
- **불변**: `publish.md` 계약과 커밋 1 검증(`git push`는 init 첫 push 1줄) 그대로

## Re-plan 2026-09-29 — 변형 차이를 파일 교체만으로

- **계기**: 사용자가 "애초에 특정 문서 내용만 변경해서 유지하면 되도록 설계를 했던건데"라며 `tools/overlay.py`의 필요성을 물음 — `publish.md` 밖에 박힌 스킬 접두(`/llm-wiki:` 12개 파일 38회)와 위키 경로(`LLM_WIKI_ROOT`·`~/.ai-docs/wiki`) 때문에 치환 스크립트가 필요했던 것이 설계 결함임
- **변경**: 훅·`graph.py`·`update.py`는 스킬 접두를 `plugin.json` name에서(`graph.SKILL_PREFIX`), 위키 경로를 `publish.md` `사본` 불릿에서 읽고, 규약은 `{SKILL_PREFIX}` 자리표시, 스킬·템플릿 본문은 네임스페이스 없이 스킬 이름으로 가리키며, `LLM_WIKI_ROOT` 환경변수 지원과 `tools/overlay.py`를 삭제함
- **변형 절차**: 이 폴더를 `rsync -a --delete --exclude=__pycache__`로 복사한 뒤 `publish.md`·`plugin.json`·`README.md` 세 파일을 덮어씀 — 드리프트 자동 검사는 없음
- **검증**: 세션 주입 3종 diff 없음, 원본 대비 스크립트 출력은 앞선 정리의 문구 2건 외 동일, 픽스처 훅 4건은 `사본` 불릿으로 경로를 준 복사본에서 원본과 동일, 이름·`사본`만 바꾼 복사본의 훅이 `/acme-llm-wiki:`와 바꾼 경로를 출력

## Re-plan 2026-09-29 — 위키 경로를 config.json으로

- **계기**: 사용자가 "md 파일 파싱해서 사용할 이유가 있나 싶음 각 쓰임새에 따라 레퍼런스 파일을 분리해서 관리해야하는게 아닌지"라며 `publish.md` `사본` 불릿 파싱을 물음
- **변경**: 코드가 읽는 위키 경로는 플러그인 루트 `config.json`의 `wikiRoot`로 옮기고 `publish.md` `사본` 불릿을 삭제함 — `publish.md`는 에이전트가 읽는 절차만, 스킬 접두는 이름의 두 번째 출처를 만들지 않도록 `plugin.json` name 파생을 유지
- **변형 교체 파일**: `references/publish.md`·`config.json`·`.claude-plugin/plugin.json`·`README.md` 4종
