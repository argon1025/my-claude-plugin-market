---
name: register
description: Use when the current git repo must be registered in the wiki, moved to another domain, re-surveyed, or its status inspected ("이 레포 위키에 등록", "레포 등록", "도메인 이동", "위키 상태", session header says 미등록 레포) — picks or creates the {조직}-{도메인} domain, surveys the repo once with a subagent and records the node (stack·summary·areas·hosts·status) in registry.json with its outgoing edges in deps.json, records the local path, commits and pushes, prints the repo status table. NOT for creating the wiki repo itself (that is /llm-wiki:init's job) and NOT for writing facts (that is /llm-wiki:add and /llm-wiki:update's job).
disable-model-invocation: true
---

현재 레포를 조사해 위키의 노드와 나가는 간선으로 기록합니다. 규격은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md` 9·10장이 정본이며, 이 스킬은 사실 문서를 쓰지 않습니다.

인자: `--status`(6장만), `--resurvey`(기존 등록 레포를 다시 조사), `--excluded {slug} --remote {URL} --reason {사유} [--branch {b}]`(체크아웃 밖 휴면 레포 등록).

## 1. 전제

- **위키**: `{WIKI_ROOT}/registry.json`이 없으면 `/llm-wiki:init` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only` — 충돌·분기는 멈추고 보고
- **레포**: 현재 디렉터리가 git 레포가 아니면 중단, `--status`만 있으면 6장으로
- **slug**: origin(없으면 upstream) URL의 마지막 경로 요소에서 `.git` 제거·소문자·비허용 문자 하이픈 치환, remote가 없으면 `git rev-parse --path-format=absolute --git-common-dir`의 부모 디렉터리명 — 다른 remote의 레포와 slug가 겹치면 `{domain}-{name}`을 제안
- **기존 등록**: `repos.{slug}`가 이미 있고 `--resurvey`가 없으면 3장에서 도메인 이동·remote 추가만 묻고 2장 조사를 생략, 둘 다 아니면 `.local/paths.json`만 갱신해 6장으로
- **휴면 레포**: `--excluded`가 있으면 조사·질문 없이 `status: excluded` 노드를 기록하고 4장으로 — `stack`·`summary`는 빈 문자열, `areas`는 빈 객체, `hosts`는 빈 배열, `branch` 기본값은 `main`

## 2. 조사 — 서브에이전트 1회

`model: sonnet` Agent 1회로 현재 체크아웃을 읽습니다. 입력을 5종으로 고정하는 것은 재현성 때문입니다 — 무엇을 열지 에이전트가 정하면 같은 레포에서도 실행마다 다른 노드가 나옵니다. 응답은 건수만 받고 초안은 파일로 씁니다.

````
레포 하나를 조사해 위키 노드 초안을 만드는 작업입니다. 문서 작성이 아니라 JSON 초안 기록이며, 파일을 고치거나 커밋하지 마세요.

아래 5종만 읽으세요. 그 밖의 파일은 열지 말고 사전 지식으로 채우지 마세요.
① `README*`
② 빌드 파일(`package.json`·`pom.xml`·`build.gradle*`·`pyproject.toml`·`go.mod`)의 이름과 의존 목록
③ 최상위 디렉터리 목록과 소스 패키지 3단계 목록
④ 컨트롤러·라우터·핸들러 파일명과 라우트 선언 — `grep -rE '@RequestMapping|@GetMapping|@PostMapping|router\.|app\.(get|post|put|delete)|@Controller'`
⑤ 설정 파일(`application*.yml|properties`, `.env.example`)의 URL·호스트·큐 이름과 HTTP 클라이언트 base URL·Feign name

업무 영역은 아래 기존 키를 우선 쓰고, 없을 때만 새 이름을 제안하세요 — {대상 도메인의 기존 영역 키 목록}.

나가는 간선의 방향은 "이 레포가 상대의 계약에 의존"입니다. 빌드 의존은 `library`, HTTP 클라이언트·Feign은 `http`, 큐·토픽 리스너는 `message`(이 레포가 소비하므로 target은 발행 측 식별자), 타 레포 스키마 직접 조회는 `data`입니다.

출력: {스크래치}/survey.json에 Write —
{"stack": "언어·프레임워크 한 줄",
 "summary": "80자 이내 소관 한 줄, 업무 낱말 우선",
 "areas": [{"area": "업무 영역 이름", "role": "40자 이내 역할", "evidence": "경로 또는 심볼"}],
 "hosts": ["이 레포가 서빙·발행하는 호스트명·group:artifact·큐 이름"],
 "outgoing": [{"target": "호스트명·artifact·큐 이름·레포 이름", "kind": "library|http|message|data",
               "identifiers": ["계약 식별자"], "evidence": "경로 또는 심볼"}]}
근거를 찾지 못한 항목은 넣지 마세요. 응답은 영역·호스트·간선 건수만 반환하세요.
````

## 3. 질문 — 정지점 하나

조사 초안을 보이고 AskUserQuestion 한 라운드로 확인합니다. 초안 수정은 자유 입력으로 받고 `알아서`는 초안 채택입니다.

- **도메인**: `registry.json`의 `domains` 목록 중 선택 또는 신규 `{조직}-{도메인}`(`^[a-z0-9]+-[a-z0-9-]+$`) — 신규면 `description` 한 줄과 `access`(접근 좌표 불릿, 빈 값 허용)를 같은 라운드에 받음
- **기본 브랜치**: `git symbolic-ref refs/remotes/origin/HEAD`의 꼬리를 초안으로 제시(없으면 `main`)
- **상태**: `active` 기본, `excluded`를 고르면 사유를 받음
- **기존 등록 레포**: 도메인 이동(대상 도메인)과 remote 추가(현재 URL을 `remotes`에 더함) 여부를 같은 라운드에 물음
- **조사 초안 표**: `| 항목 | 초안 | 근거 |`로 스택·소관·영역별 역할·호스트·나가는 간선 대상을 싣고 수정을 받음 — 영역 키는 도메인 접두를 붙인 꼴로 보임

## 4. registry.json·deps.json

- **노드**: `repos.{slug}`에 규약 9장 9키(+`excluded`면 `reason`)를 기록 — `areas` 키는 `{domain}/{영역}` 꼴이고 타 도메인 영역 참여는 그 도메인 접두, `source`는 `확인 — register 조사, {오늘}`
- **도메인**: 신규 도메인이면 `domains.{d}`에 `description`·`access` 기록
- **간선**: `outgoing`의 `target`을 다른 노드의 `hosts`·slug·`remotes`와 대조해 걸린 것만 `deps.json`에 `관찰 — register 조사, {오늘}` 간선으로 추가(`kind`는 `outgoing.kind`, `note`는 `identifiers`를 ` · `로 나열) — 걸리지 않은 대상은 보고의 `미등록 상대`로만 남기고 간선을 만들지 않음
- **도메인 이동 — 승인 하나**: `knowledge/{old}/{slug}/`가 있으면 `git mv knowledge/{old}/{slug} knowledge/{new}/{slug}` 대상·건수를 보이고 승인 후 실행, `deps.json`의 `{old}/{slug}` 끝점을 `{new}/{slug}`로 치환 — 영역 키의 도메인 접두는 참여 도메인을 뜻하므로 바꾸지 않으며, 새 도메인 영역 참여가 필요하면 `--resurvey`로 재조사하라고 보고에 안내
- **레포 폴더**: `knowledge/{d}/{slug}/`는 만들지 않음 — 첫 레포 종속 문서가 생길 때 add·update가 만듦

## 5. 검사·커밋

- **paths.json**: `.local/paths.json`에 `{slug: git toplevel 절대경로}` 갱신 — 미추적 파일이라 머신마다 따로 쌓임
- **검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {WIKI_ROOT}/registry.json {WIKI_ROOT}/deps.json` 에러 0
- **커밋**: `chore(register): {slug} → {domain}` 한 커밋에 `registry.json`·`deps.json`을 함께 담고(이동이면 `chore(register): {slug} {old} → {new}`), `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 상태 표·보고

- **상태 표**: `registry.json`·`state/*.json`·`.local/paths.json` 3파일을 Read해 `| 레포 | 도메인 | 상태 | 영역 | 간선(out/in) | 브랜치 | 커서 | 로컬 경로 |` 표를 출력 — 커서 없음은 `없음`, 경로 없음은 `없음`(그 레포에서 세션을 열거나 register하면 기록됨)
- **미등록 상대**: 4장에서 간선이 되지 못한 `outgoing.target`을 그대로 나열 — 그 레포를 등록하거나 상대 노드의 `hosts`를 `/llm-wiki:add`로 보강하면 이어짐
- **다음**: 세션을 다시 열면 도메인 목록·역인덱스·간선·인접 좌표가 주입되고, 머지 반영은 `/llm-wiki:update`, 자료 반영은 `/llm-wiki:add`
