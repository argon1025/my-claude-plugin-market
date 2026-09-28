# llm-wiki 축 2 — 세션 주입 구성 개선 v5.5.0

## 의도

- **왜**: 세션 주입의 레포 지도가 다른 도메인 레포 전수·clone 패턴·owner·커서 신호·도메인 전체 간선까지 실어 팀 규모에서 커지고, 미등록 레포에도 규약 전문(1,783자)이 들어가며, 규약은 상대 레포를 "새 계약이 필요할 때"만 보라고 해 원인 추적과 상대 레포 수정 경로가 없음
- **누가**: MSA 여러 레포를 오가는 팀원의 에이전트가 모든 세션 시작 때 겪음 — 선행 레포 작업(외부 연동 클래스를 다른 프로젝트에 먼저 반영), 프론트에서 백엔드 API 문제인지 직접 추적, 리뷰 시 의존 파악
- **완료**: 등록 레포 세션은 현재 도메인 레포 전수와 현재 레포와의 의존 힌트를 한 블록으로 받고, 규약이 상대 레포 읽기(미러)와 수정(작업 사본) 경로를 안내하며, 미등록·git 밖 세션은 규약 없이 약 360자 블록만 받고, 커서 신호가 사라짐

## 배경

- **의존은 하한**: `deps.json`은 register·update가 상대를 특정하지 못한 의존을 `상대 미정`으로 보고만 하고 간선으로 만들지 않아 전수가 아님(`references/doc-contract.md` 10장) — 그래서 레포 지도는 레포 전수가 주이고 의존은 행에 붙는 힌트임
- **미러는 읽기 전용**: `update.py` `ensure_mirror`가 `+refs/heads/*:refs/heads/*` refspec과 `fetch --prune`으로 로컬 브랜치를 덮고 지우므로 편집용 브랜치·worktree를 만들 수 없으나, push된 모든 브랜치가 들어 있어 `git -C {미러} grep {브랜치}`로 기능 브랜치도 조회됨
- **로컬 경로 비저장**: `.local/paths.json`은 worktree 경로가 낡는 문제로 폐지됨 — 작업 사본 위치는 저장하지 않고 세션마다 `--git-common-dir`에서 계산함 (worktree `~/orca/workspaces/pigeon-trade/issue-24`의 common dir은 `~/Desktop/Projects/pigeon-trade/.git`)
- **권한**: Claude Code 기본 권한 모드에서 작업 디렉터리 밖 편집은 확인이 뜨고 에이전트는 디렉터리를 추가할 수 없어 사용자가 `/add-dir`을 실행해야 함(https://code.claude.com/docs/en/permissions.md#working-directories)
- **실측**: 시제품 기준 주입 전체 pigeon-trade 5,156 → 약 4,900자, 미등록 1,783 → 약 360자, 팀 규모 합성 그래프(도메인 4·레포 44·간선 21) 규약+지도 약 4,000 → 약 2,400자
- **호출처**: `render_session`은 훅만 부르고, 삭제 대상 함수(`map_block`·`domain_heading`·`remote_pattern`·`project_host`·`project_owner`·`other_edge_rows`)는 `graph.py` 안에서만 쓰이며 `view.py`·`update.py`·`survey.py`·`catalog.py`는 부르지 않음

## 확정 결정 (사용자 확인 2026-09-29)

- **상황별 분기**: 위키 없음은 init 안내 한 줄 유지, 미등록·git 밖은 규약 없이 위키 경로·도메인·register 안내·"스킬로만 고침"을 담은 한 블록, 등록 레포는 규약 → 동기화 알림 → 레포 지도 → 문서 목록
- **레포 지도 범위**: 현재 도메인 전 레포(책임 문장)와 현재 레포와 간선이 있는 다른 도메인 레포(소관 한 줄)를 행으로 두고, 나머지 도메인은 `다른 도메인: {이름}({설명}) · …` 한 줄
- **의존은 힌트**: 의존 관점으로 묶지 않고 레포 행 아래 `현재 레포가 의존|현재 레포에 의존 {kind}: {계약}` 줄로 붙이며, 경유는 `현재 레포에 의존 {kind} (경유 {lib})`
- **형식**: 표가 아니라 중첩 목록, 계약 식별자는 현재 레포와 이어진 간선만 유지, `upstream`·`downstream` 용어는 쓰지 않음
- **삭제**: 커서 신호(`커서 없음` 포함), clone 패턴, 도메인 owner 머리글, 예외 remote, `도메인의 다른 의존` 블록, 다른 도메인 레포 목록 — `graph.py repo`·`map` 출력은 유지
- **규약 레포 지도 절**: 작업 대상·의존 줄 힌트·상대 레포 코드(선행 작업·원인 추적·변경 파급)·상대 레포 수정(`{REPOS_DIR}/{slug}` 작업 사본, 없으면 위치 질문 뒤 clone, 작업 디렉터리 밖은 `/add-dir` 안내)·추가 조회 5줄이며, 모델 기본 동작(선대응 보고, 레포별 계획 순서, remote 대조, 미커밋 변경 확인)은 넣지 않음
- **범위 밖**: 문서 목록(축 1), 예산·축약(축 3), 규약의 다른 문장(축 4), `--wiki` 인자 생략·훅 Python 단일화(축 5), 루트 `llm-wiki-review.md` 수정
- **버전**: 위키 데이터 형식 불변이라 5.5.0

## 외부 계약

- **훅 출력**: `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}`, 어떤 실패에도 종료 코드 0 — 0이 아니면 주입이 사라짐
- **규약 자리표시자**: 훅이 `{WIKI_ROOT}`·`{GRAPH_PY}`·`{UPDATE_PY}`를 치환하며 이번에 `{REPOS_DIR}`를 더함

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `llm-wiki/scripts/graph.py` | `render_session` 재작성, `domain_line` 추출, `via_rows`를 튜플 반환 `via_pairs`로, `edge_groups` 2값 반환, 6개 함수 삭제, `render` CLI 인자 필수, 모듈 docstring 갱신 | ② 기존 파생 함수 재구성 |
| `llm-wiki/hooks/session_start.sh` | 미등록·git 밖 분기 블록, 커서 계산 삭제, `{REPOS_DIR}` 치환, 상단 주석 갱신 | ② 기존 heredoc 수정, `{REPOS_DIR}`는 ⑥ |
| `llm-wiki/rules/agent-guide.md` | 아래 전문으로 교체 | ② |
| `llm-wiki/references/doc-contract.md` | 9장 `project`·`remote`·`status` 불릿, 10장 도입 문장·`경유 파생` 불릿 | ② |
| `llm-wiki/README.md` | 동작 방식의 SessionStart·그래프 파생·주입 범위·레포 판정 불릿 갱신, 커서 신호 불릿 삭제 | ② |
| `llm-wiki/.claude-plugin/plugin.json` | version 5.5.0, description의 주입 표현 | ② |
| `.claude-plugin/marketplace.json` | llm-wiki description의 주입 표현(metadata.version 3.1.0은 5.x 관례대로 유지) | ② |

### graph.py

- **`domain_line(registry, exclude="")`**: `sorted(registry["domains"])`에서 `exclude`를 빼고 `{name}({description})`(설명 없으면 `{name}`)을 ` · `로 이은 문자열 — `map_block`의 도메인 목록 분기를 추출한 것이며 `render_session`의 `다른 도메인:` 줄과 훅의 미등록 블록이 함께 씀
- **`via_pairs(edges, domain, slug, incoming) -> list[tuple[str, str, str]]`**: 기존 `via_rows`의 파생 로직을 그대로 두고 `(origin, via, kind)` 정렬 목록을 반환, `edge_blocks`가 `- {kind} {label_for(origin)} (경유 {label_for(via)})`로 포맷 — 파생 규칙 한 곳 유지
- **`edge_groups`**: `(outgoing, incoming)`만 반환하고 `others` 분기 삭제, `render_repo`의 `outgoing, incoming, _`를 두 값으로
- **`render_session(registry, edges, domain, slug) -> str`**: `domain`이 비면 빈 문자열, 아니면 아래 순서
  - 머리글 `# 레포 지도 — {domain}({description}) · 현재 {slug}` (설명 없으면 `({description})` 생략)
  - 현재 도메인 레포를 `domain_repos` 순서로 `- {slug}[ (현재)][ (휴면)] — {책임 문장 ' · ' 결합, 없으면 summary}` (텍스트 없으면 ` — ` 생략)
  - 각 행 아래 힌트 줄을 나가는 간선 → 들어오는 간선 → 경유 순으로 `  - 현재 레포가 의존 {kind}: {계약 ' · ' 결합}`, `  - 현재 레포에 의존 {kind}: …`, `  - 현재 레포에 의존 {kind} (경유 {label_for(via)})` — 계약이 없으면 `: …` 생략
  - 이어서 힌트가 있는 다른 도메인 끝점을 정렬해 `- {domain}/{slug}[ (휴면)] — {summary}` 행과 힌트 줄
  - 마지막에 다른 도메인이 있으면 `다른 도메인: {domain_line(registry, exclude=domain)}`
- **삭제**: `map_block`·`domain_heading`·`remote_pattern`·`project_host`·`project_owner`·`other_edge_rows` — `owner_label`·`domain_projects`·`access_block`·`responsibility_rows`는 `render_map`이 쓰므로 유지
- **CLI**: `render`의 `--domain`·`--slug`를 `required=True`, help를 "훅이 주입하는 레포 지도 블록을 그대로 낸다"로
- **docstring**: 모듈 머리의 "레포 지도(도메인별 레포와 책임·소관, owner)와 좌표 패턴(clone URL의 공통 규칙과 예외)" 서술을 "레포 지도(현재 도메인 레포의 책임과 현재 레포와의 의존 힌트)"로, `edge_blocks` docstring의 "render_session·render_repo가 함께 쓰므로"를 `render_repo` 기준으로

### session_start.sh

- **미등록·git 밖**: heredoc에서 `slug, domain = graph.resolve_repo(...)` 뒤 `if not domain:`이면 규약 없이 아래 블록(동기화 알림이 있으면 앞에 한 줄)만 출력하고 끝냄 — 첫 줄은 `slug`가 있으면 `# 위키 {wiki} — 미등록 레포 {slug}: 레포 지도·문서 목록 주입 없음`, 없으면 `# 위키 {wiki} — git 레포 밖: 레포 지도·문서 목록 주입 없음`, 도메인이 없으면 `없음`

```
# 위키 {wiki} — 미등록 레포 {slug}: 레포 지도·문서 목록 주입 없음
- **도메인**: {graph.domain_line(registry)}
- **등록**: `/llm-wiki:register`, 도메인 지도는 `python3 {graph_py} map --domain {domain} --wiki {wiki}`
- **직접 수정 금지**: 위키는 `/llm-wiki:` 스킬로만 고침
```

- **커서 삭제**: `# 위키가 이 레포를 얼마나 따라왔는지…` 블록 전체와 `subprocess` import, 기존 `# 미등록 레포 … 주입됨` 헤더 줄 삭제
- **`{REPOS_DIR}`**: `Path(common_dir).name == ".git"`이면 `Path(common_dir).parent.parent`, 아니면 `Path(toplevel).parent` — worktree에서 열어도 본 저장소의 상위 폴더가 나오며 guide 치환에 추가
- **등록 레포 조립**: `[guide, sync_note(있으면), graph.render_session(...), 문서 목록들]` 순서와 `SOFT_BUDGET` 권고는 유지
- **상단 주석**: 주입 순서 서술을 "규약 → 동기화 알림 → 레포 지도(현재 도메인 레포와 현재 레포 의존 힌트) → 목록, 미등록·git 밖은 규약 없이 짧은 블록"으로

### agent-guide.md 전문

```markdown
# 위키 규약 (세션 전체 적용)

`{WIKI_ROOT}`의 문서와 아래 레포 지도는 레포 밖에 공유할 사실과 코드에 없는 사실의 정본입니다. 사용자가 세션에서 다르게 지시하면 그 지시가 우선합니다.

## 레포 지도

- **작업 대상**: 요청의 업무 낱말이 걸리는 책임의 레포가 수정·검토 대상이며 `(휴면)`은 수정하지 않되 파급 확인에 포함
- **의존 줄**: 등록된 간선에서 나온 힌트이며 전수가 아님 — 줄이 없어도 책임 문장이 작업과 겹치는 레포는 코드로 확인
- **상대 레포 코드**: 필요한 계약이 상대 레포에 있는지(선행 작업), 동작 이상이 상대 레포에서 오는지(원인 추적), 현재 레포 공개 계약을 어디서 쓰는지(변경 파급)는 추측하지 않고 상대 레포 코드로 판단 — `python3 {UPDATE_PY} mirror --repo {slug} --wiki {WIKI_ROOT}` 출력의 `{미러}@{브랜치}`에서 `git -C {미러} grep|show {브랜치}`, push된 다른 브랜치도 이름으로 조회
- **상대 레포 수정**: 미러는 읽기 전용이라 `{REPOS_DIR}/{slug}` 작업 사본에서 고치며, 없으면 사용자에게 위치를 묻고 없다면 그 자리에 clone, 작업 디렉터리 밖이면 사용자에게 `/add-dir {경로}` 실행을 안내
- **추가 조회**: 상대 레포의 저장소·스택·호스트·다음 의존은 `python3 {GRAPH_PY} repo {slug} --wiki {WIKI_ROOT}`, 다른 도메인 레포는 `python3 {GRAPH_PY} map --domain {domain} --wiki {WIKI_ROOT}`

## 문서 목록

설명이 요청과 맞는 문서는 코드 전에 열고, 걸리지 않으면 `grep -ril '{업무 낱말 또는 식별자}' {WIKI_ROOT}/knowledge/{domain}`으로 도메인 전체(다른 레포 폴더 포함)를 찾아 걸린 문서를 열며 그래도 없으면 열지 않음. 도메인 루트를 먼저, 레포 문서는 그 위에서 좁힌 부분만

## 규칙

- **문서 우선**: 사전 지식과 문서가 어긋나면 문서를 믿되, 사용자가 바뀐 이유를 밝히면 그 설명이 이김 — 이유 없는 이견은 모순 보고로
- **모순 보고**: 문서끼리 또는 문서와 코드가 어긋나면 임의로 고르지 않고 두 값을 병기해 알림
- **직접 수정 금지**: 위키는 `/llm-wiki:` 스킬로만 고침
- **기록 제안**: 정책·결정·함정처럼 레포 밖이 알아야 하거나 코드에 없는 사실이 확정되면 근거와 함께 작업 끝에 `/llm-wiki:add`를 제안하며 임의로 기록하지 않음
```

### 문서·메타

- **doc-contract 9장**: `project` 불릿의 "도메인 머리글·접근 좌표의 owner와 clone 패턴(`{host}/{owner}/{slug}`)이 여기서 파생됨"을 "`graph.py map` 접근 좌표의 owner가 여기서 파생됨"으로, `remote` 불릿의 "clone 패턴과 다를 때만 지도 행에 나감"을 "미러와 작업 사본 clone이 `https://{remote}.git`을 씀"으로, `status` 불릿의 "지도에 `(휴면)`으로 이름만 실리되"를 "지도 행에 `(휴면)`이 붙되"로
- **doc-contract 10장**: 도입의 "훅이 현재 레포 기준 선행 조건(나가는 간선)과 파급 대상(들어오는 간선)을 나눠 주입합니다"를 "훅이 현재 레포와 이어진 간선을 레포 지도의 상대 레포 행 아래 의존 힌트로 주입합니다"로, `경유 파생` 불릿의 "주입·`repo`의 `이 레포에 의존`은"을 "주입의 `현재 레포에 의존` 힌트와 `repo`의 `이 레포에 의존`은"으로 — 장 번호·제목은 스킬 sed 범위가 쓰므로 바꾸지 않음
- **README 동작 방식**: SessionStart 불릿의 주입 순서를 훅 상단 주석과 같게, 그래프 파생 불릿에서 owner·좌표 패턴 서술 삭제, 주입 범위 불릿을 확정 결정의 레포 지도 범위·의존 힌트·계약 유지·`{REPOS_DIR}/{slug}` 작업 사본 안내로 재작성하고 `graph.py render` 설명을 "레포 지도 블록"으로, 레포 판정 불릿의 "미등록이면 규약·등록 안내·도메인 목록만 주입"을 "미등록·git 밖이면 규약 없이 위키 경로·도메인·등록 안내 블록만 주입"으로, 커서 신호 불릿 삭제
- **description**: plugin.json·marketplace.json의 "그래프 파생 주입(레포 지도·현재 레포 기준 의존 3묶음)"을 "그래프 파생 주입(현재 도메인 레포 지도·현재 레포 의존 힌트)"으로

## 커밋 분해

브랜치 `feat/llm-wiki-session-slim` (main에서 분기).

| # | 범위 | 검증 |
|---|---|---|
| 0 | `docs(plan): llm-wiki 세션 주입 구성 계획 스냅샷` — `.ai-docs/workspace/llm-wiki-session-slim/plan.md`·`feedback.md` | `git show --stat HEAD`에 두 파일만 |
| 1 | `feat(llm-wiki): 레포 지도를 현재 도메인 레포 행과 의존 힌트로` — graph.py | 아래 픽스처 `render` 출력이 기대 출력과 `diff` 무차이, `python3 llm-wiki/scripts/graph.py render --domain personal-stock-trading --slug pigeon-trade-dashboard --wiki ~/.ai-docs/wiki`에 `(현재)`·`현재 레포가 의존 http: GET /api/*` 포함, `graph.py repo pigeon-trade`·`map --domain personal-stock-trading`·`check`·`view.py --no-open --out "$TMPDIR/g.html"` 종료 코드 0, `grep -rnE 'map_block|domain_heading|remote_pattern|project_host|project_owner|other_edge_rows|via_rows' llm-wiki` 0건 |
| 2 | `feat(llm-wiki): 미등록 분기·작업 사본 안내·커서 신호 삭제` — session_start.sh, agent-guide.md | `bash -n` 통과, 아래 훅 실행 5건이 조건 충족, 깨진 `registry.json`을 가진 임시 위키(`LLM_WIKI_ROOT`)에서도 종료 코드 0 |
| 3 | `docs(llm-wiki): 주입 구성 변경 반영, 버전 5.5.0` — doc-contract.md, README.md, plugin.json, marketplace.json | `grep -n -e '커서 신호' -e 'clone 패턴' -e '좌표 패턴' -e '의존 3묶음' llm-wiki/README.md llm-wiki/references/doc-contract.md llm-wiki/.claude-plugin/plugin.json .claude-plugin/marketplace.json` 0건, `python3 -m json.tool` 두 JSON 통과, plugin.json version `5.5.0` |

### 커밋 1 픽스처

`$TMPDIR/wiki-fixture`에 `registry.json`(`{"domains": {...}}` 중첩 꼴, 노드는 `status`·`summary`·`responsibilities`만 채움)과 `deps.json`을 만듦.

- **도메인**: `ex-shop`(쇼핑 레포 모음) — `shop-api`(주문 API 제공 / 주문 백엔드), `shop-fe`(주문 화면 제공), `shop-lib`(주문 클라이언트 제공), `shop-old`(구 주문 화면 제공, `dormant`) · `ex-pay`(결제 레포 모음) — `pay-api`(결제 승인 API 제공 / 결제 백엔드), `pay-batch`(정산 배치)
- **간선**: `shop-lib → shop-api http ["GET /orders* — 주문 조회"]`, `shop-fe → shop-lib library ["com.ex:shop-lib — 주문 클라이언트"]`, `shop-api → ex-pay/pay-api http ["POST /pay* — 결제 승인"]`, `shop-old → shop-api http ["GET /orders* — 구 주문"]` (끝점은 `{도메인}/{slug}`)
- **명령**: `python3 llm-wiki/scripts/graph.py render --domain ex-shop --slug shop-api --wiki "$TMPDIR/wiki-fixture"`

```
# 레포 지도 — ex-shop(쇼핑 레포 모음) · 현재 shop-api
- shop-api (현재) — 주문 API 제공
- shop-fe — 주문 화면 제공
  - 현재 레포에 의존 http (경유 shop-lib)
- shop-lib — 주문 클라이언트 제공
  - 현재 레포에 의존 http: GET /orders* — 주문 조회
- shop-old (휴면) — 구 주문 화면 제공
  - 현재 레포에 의존 http: GET /orders* — 구 주문
- ex-pay/pay-api — 결제 백엔드
  - 현재 레포가 의존 http: POST /pay* — 결제 승인
다른 도메인: ex-pay(결제 레포 모음)
```

### 커밋 2 훅 실행

`echo '{"source":"clear"}' | CLAUDE_PLUGIN_ROOT={레포}/llm-wiki CLAUDE_PROJECT_DIR={디렉터리} bash llm-wiki/hooks/session_start.sh`의 `additionalContext` 기준.

- **pigeon-trade**(`~/Desktop/Projects/pigeon-trade`): `# 위키 규약`으로 시작, `커서`·`clone`·`{REPOS_DIR}` 문자열 없음, `/Users/rok/Desktop/Projects/{slug}` 포함, `현재 레포에 의존 http` 포함, 길이 5,156 미만
- **pigeon-trade-dashboard**: `현재 레포가 의존 http` 포함, `커서` 없음
- **worktree**: `git -C ~/Desktop/Projects/pigeon-trade worktree list --porcelain`의 두 번째 `worktree` 경로(현재 `~/orca/workspaces/pigeon-trade/api-mcp`)에서 실행해 `/Users/rok/Desktop/Projects/{slug}` 포함 — 연결 worktree가 없으면 `git -C ~/Desktop/Projects/pigeon-trade worktree add --detach "$TMPDIR/pt-wt"`로 만들어 검증한 뒤 `worktree remove "$TMPDIR/pt-wt"`
- **미등록**(이 레포): `# 위키 규약` 없음, `미등록 레포 my-claude-plugin-market` 포함, 길이 500 미만
- **git 밖**(`$TMPDIR`): `git 레포 밖` 포함, 길이 500 미만

## 특이 사항

- **다중 홉**: fe → bff → 서비스 같은 2홉 추적은 규약의 `graph.py repo` 안내에 의존 — 실사용에서 다음 홉을 반복해 놓치면 관계 레포 행에 그 레포의 다음 의존 이름을 붙이는 확장 검토
- **작업 사본 위치**: 도메인별로 다른 폴더에 레포를 두는 사용자는 `{REPOS_DIR}/{slug}`에서 찾지 못해 위치 질문으로 넘어가며, submodule처럼 common dir 이름이 `.git`이 아닌 경우는 toplevel 상위 폴더를 씀
- **미러 읽기 권한**: 기본 권한 모드의 팀원은 `git -C {미러}` 실행마다 확인을 받음 — 기존 동작이며 허용 규칙 안내는 별도 검토
- **남은 중복**: 명령마다 붙는 `--wiki {WIKI_ROOT}`(규약 3회)는 축 5에서 `DEFAULT_WIKI`를 훅과 맞춘 뒤 제거
- **후속**: 축 1(문서 접근)·3(예산)·4(규약 문장)·5(코드 구조)는 별도 계획

## Re-plan 2026-09-29 — 라인별 필요성 검토 재작성

- **계기**: 사용자 지시 "에이전트는 기존 항목을 유지하면서 최소한의 수정을 진행하는 경향이 있음 라인별로 꼭 필요한가를 검토해보고 효율적인 구조로 재작성, 삭제 정리 검토 진행"
- **범위**: 이 브랜치의 세션 주입 경로(규약·훅·레포 지도 렌더·관련 CLI와 문서) — 문서 목록 방식(축 1)·예산 `SOFT_BUDGET`(축 3)·스킬 본문은 그대로
- **판정 기준**: 모델 기본 동작이거나 주입 내용·다른 줄에서 드러나는 줄은 삭제하고, 에이전트가 도출할 수 없는 사실(경로·명령·데이터 한계·위키 규칙)만 유지

| 대상 | 삭제 | 재작성 |
|---|---|---|
| 규약 | 사용자 지시 우선, `##` 소제목 3개, 세 쓰임 열거, clone·`/add-dir` 절차, 열람 순서, "그래도 없으면 열지 않음", 이유를 밝힌 사용자 설명 우선, 기록 예시·"임의로 기록하지 않음", 명령마다 붙던 `--wiki` | 평면 불릿 7개, 정본 문장에 문서 우선 흡수, 모순 보고에 요청 포함, grep 경로는 훅이 `{DOMAIN_DIR}`로 치환 |
| 레포 지도 | 머리글의 도메인 설명과 `· 현재 {slug}`(행의 `(현재)`와 중복), 도메인 없음 분기(훅이 먼저 거름) | 현재 도메인 행과 힌트 끝점 행을 한 루프로 |
| 미등록 블록 | "레포 지도·문서 목록 주입 없음", git 밖의 등록 안내, 도메인이 없을 때의 도메인 줄 | 3줄 |
| 훅 | bash 래퍼(인자 6개 전달, stdin 파싱용 python 호출, JSON 출력 두 벌), `TOPLEVEL` 조회와 폴백 | `hooks/session_start.py` 한 파일, `{REPOS_DIR}`는 common dir 상위 두 단계 — submodule·bare는 없는 경로가 나와 규약의 위치 질문으로 넘어감 |
| graph.py | `render` 서브커맨드(훅 실행으로 같은 확인 가능), 호출처 하나뿐인 `edge_blocks`·`access_block`·`domain_projects`·`domain_label`, `text_list`의 미사용 `limit`, `repo` 머리글 건수와 `(경유 N건 포함)` | `DEFAULT_WIKI`를 빈 환경 변수에도 기본 경로로, `repo`가 `{domain}/{slug}`도 받음 |
| update.py | — | `DEFAULT_WIKI` 같은 정렬, `mirror --repo`가 `{domain}/{slug}`도 받음 |

| # | 범위 | 검증 |
|---|---|---|
| 4 | `docs(plan): 라인별 필요성 검토 재계획` — 이 절 | — |
| 5 | `refactor(llm-wiki): 레포 지도 렌더·그래프 CLI 불필요 코드 삭제` — graph.py, update.py | 픽스처 `render_session` 출력이 아래 기대 출력과 무차이, `repo`·`map`·`check`·`view.py` 종료 코드 0, `repo ex-pay/pay-api`·`mirror --repo personal-stock-trading/pigeon-trade`가 slug와 같은 결과 |
| 6 | `refactor(llm-wiki): SessionStart 훅 Python 단일화와 규약 재작성` — session_start.py, hooks.json, agent-guide.md | 기존 훅 실행 5건 조건(`clone` 조건은 제외), 위키 없음·깨진 JSON에서 종료 코드 0, 픽스처 레포 세션의 레포 지도가 기대 출력과 무차이, `LLM_WIKI_ROOT=""`에서 기본 위키 사용 |
| 7 | `docs(llm-wiki): 재작성 반영` — README.md, doc-contract.md, feedback.md | `grep -rn 'session_start.sh\|graph.py render' llm-wiki` 0건 |

```
# 레포 지도 — ex-shop
- shop-api (현재) — 주문 API 제공
- shop-fe — 주문 화면 제공
  - 현재 레포에 의존 http (경유 shop-lib)
- shop-lib — 주문 클라이언트 제공
  - 현재 레포에 의존 http: GET /orders* — 주문 조회
- shop-old (휴면) — 구 주문 화면 제공
  - 현재 레포에 의존 http: GET /orders* — 구 주문
- ex-pay/pay-api — 결제 백엔드
  - 현재 레포가 의존 http: POST /pay* — 결제 승인
다른 도메인: ex-pay(결제 레포 모음)
```
