---
name: register
description: Use when the current git repo must be registered in the wiki, moved to another domain, re-surveyed, or its status inspected ("이 레포 위키에 등록", "레포 등록", "도메인 이동", "위키 상태", session header says 미등록 레포) — surveys the repo once and records its node and dependency edges in registry.json/deps.json, then prints the repo status table. Writes no doc facts (/llm-wiki:add, /llm-wiki:update) and does not create the wiki skeleton (/llm-wiki:init).
disable-model-invocation: true
---

현재 레포를 조사해 위키의 노드와 그 레포가 걸린 의존 간선으로 기록합니다. 규격은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md` 9·10장이 정본이며, 이 스킬은 사실 문서를 쓰지 않습니다.

인자: `--status`(6장만), `--resurvey`(기존 등록 레포를 다시 조사), `--dormant {slug} --remote {URL} --reason {사유} [--default-branch {b}]`(체크아웃 밖 휴면 레포 등록).

## 1. 전제

- **위키**: `{WIKI_ROOT}/registry.json`이 없으면 `/llm-wiki:init` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only` — 충돌·분기는 멈추고 보고
- **레포**: 현재 디렉터리가 git 레포가 아니면 중단, `--status`만 있으면 6장으로
- **정본 remote**: 순서대로 시도하고 scheme·`.git` 없는 소문자 정규화 꼴 하나만 기록
  1. `git remote get-url upstream`이 있으면 그 URL
  2. 없으면 `origin` — upstream 없이 owner가 개인 계정이라 포크인지 불명확하면 여기서 확정하지 않고 `포크 의심`으로 표시만 함
  3. 위로 정해지지 않거나 `포크 의심`이면 3장에서 묻고, 답이 없으면 빈 값으로 두고 보고에 `정본 remote 미상`으로 남김
- **도메인 예비 판정**: 조사 전에 한 번 정함 — 어느 도메인의 `repos.{slug}`가 있으면 그 도메인, 없고 등록 도메인이 하나뿐이면 그 도메인, 둘 이상이면 `미정`
- **slug**: 정본 remote의 마지막 경로 요소에서 `.git` 제거·소문자·비허용 문자 하이픈 치환, remote가 없으면 `git rev-parse --path-format=absolute --git-common-dir`의 부모 디렉터리명 — owner가 달라도 레포 이름이 같으면 slug가 겹치므로 겹치면 `{domain}-{name}`을 제안
- **기존 등록**: 어느 도메인에 `repos.{slug}`가 이미 있고 `--resurvey`가 없으면 3장에서 도메인 이동·정본 remote 교체만 묻고 2장 조사를 생략, 둘 다 아니면 5장 미러만 확보하고 커밋·push 없이 6장으로
- **휴면 레포**: `--dormant`가 있으면 조사·질문 없이 `status: dormant` 노드를 기록하고 4장으로 — `defaultBranch` 기본값은 `main`, `stack`·`summary`·`responsibilities`는 아는 만큼 인자로 받거나 빈 배열·빈 문자열로 두고 나중에 add가 보강함

## 2. 조사 — 4레인 병렬

`model: sonnet` Agent 4회(`library`·`http`·`message`·`responsibilities`)를 한 메시지에 병렬로 띄우고, 응답은 건수만 받고 초안은 파일로 씁니다. 스키마 자리에는 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" schema --for survey --lane {lane} --domain {예비 판정 도메인}` 출력을 그대로 싣고, 도메인이 `미정`이면 `--domain` 없이 냅니다.

````
레포 하나의 {lane} 레인을 조사해 위키 노드 초안을 만드는 작업입니다. 문서 작성이 아니라 JSON 초안 기록이며, 파일을 고치거나 커밋하지 마세요.

## 관용구 판별 — 먼저 답할 것
이 레포가 {lane}의 선언을 어디에 어떻게 두는지 먼저 정하고 근거 파일을 대세요 — 자체 선언 · 공용 라이브러리 임포트 · XML 빈 · 디렉터리 관례 · BFF 프록시 · 환경 파일 중 무엇입니까. 관용구는 레포마다 다르므로 다른 레포의 방식을 가정하지 마세요.

## 탐색
판별한 관용구에 맞게 전수 탐색하세요. 열 파일에 제한은 없고, 사전 지식으로 공백을 채우지 마세요. 항목마다 `evidence`가 필수입니다.
{아래 표의 그 레인 초점}

{graph.py schema --for survey --lane {lane} 출력을 여기에 그대로}

출력: {스크래치}/survey-{lane}.json에 위 스키마대로 Write하되 `idiom` 키에 판별한 관용구와 근거 파일을 함께 담으세요. 응답은 관용구 한 줄과 항목 건수만 반환하세요.
````

| lane | 초점 |
|---|---|
| library | 빌드 파일 전수(멀티모듈 하위 `pom.xml`·워크스페이스 패키지 포함)의 의존 좌표 중 등록 레포·같은 owner의 좌표와 `stack` |
| http | 이 레포 안의 아웃바운드 선언(`@FeignClient`·WebClient·RestTemplate·`fetch`·axios·`<form action>`·rewrites)과 설정의 URL 리터럴 — 공용 라이브러리 심볼을 가져다 부르는 호출은 적지 않음 |
| message | 리스너·발행·바인딩 선언과 타 레포 스키마 접근(jdbc URL·매퍼 테이블·`@Table`) |
| responsibilities | 라우트(클래스+메서드 결합)·배치 잡·화면·공개 심볼에서 책임 문장과 서빙 호스트 |

## 2.5 검증 — 메인

메인이 순서대로 직접 합니다.

- **① 인벤토리 대조**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/survey.py" inventory --root {git toplevel} --out {스크래치}/inventory.json`을 실행하고 인벤토리 행의 파일 집합에서 네 레인 `evidence`의 파일 집합을 뺀 잔여를 레인별로 나눠, 잔여가 있는 레인만 그 행 목록을 붙여 같은 프롬프트로 재질의 1회 — 두 번째 잔여는 6장에 `미소비 N행`으로 남기고 더 묻지 않음
- **② 상호 대조**: http 레인 항목의 `evidence`가 library 레인이 낸 공용 라이브러리의 심볼 import이면 선언 위치 위반이라 버리고 건수를 6장에 남기고, `from_me`가 거짓인 message 항목마다 responsibilities에 `소비` 문장이 있는지 보아 없으면 3장 초안 표에 `책임 후보` 행으로 올림
- **③ target 확정**: 규약 10장 대상 판정·호스트 대조·상대 미정
- **④ 외부 시스템**: `상대 미정`으로 남은 상대마다 responsibilities에 그 시스템 이름이 든 문장이 있는지 보고 없으면 3장 초안 표에 `책임 후보` 행으로 올림
- **⑤ 합치기**: 네 파일을 `{스크래치}/survey.json` 하나로 합침 — `deps`는 kind별로 이어 붙이고 같은 `(target, kind)`는 `contracts`를 합집합해 3건을 넘으면 접두·묶음으로 접음

## 3. 질문 — 정지점 하나

조사 초안을 보이고 AskUserQuestion 한 라운드로 확인합니다. 초안 수정은 자유 입력으로 받고 `알아서`는 초안 채택입니다.

- **도메인**: `registry.json`의 `domains` 목록 중 선택 또는 신규 `{조직}-{도메인}`(`^[a-z0-9]+-[a-z0-9-]+$`) — 신규면 `description` 한 줄을 같은 라운드에 받음
- **owner**: 그 도메인 기존 노드의 `project` distinct를 보여 고르게 하고, 값이 여럿이면 정본 remote의 owner 조각과 같은 것을 초안으로 제시 — 도메인의 첫 레포라 기존 값이 없으면 정본 remote에서 만든 `https://{host}/{owner}`를 초안으로 제시
- **정본 remote 확인**: 1장이 정하지 못했거나 `포크 의심`으로 표시한 remote는 추측하지 않고 같은 라운드에서 정본 remote를 직접 물음
- **기본 브랜치**: `git symbolic-ref refs/remotes/origin/HEAD`의 꼬리를 초안으로 제시(없으면 `main`)
- **상태**: `active` 기본, `dormant`를 고르면 사유를 받음
- **기존 등록 레포**: 도메인 이동(대상 도메인)과 정본 remote 교체 여부를 같은 라운드에 물음
- **조사 초안 표**: `| 항목 | 초안 | 근거 |`로 스택·소관·정본 remote·owner를 싣고, 책임은 문장마다 한 행, 호스트는 환경마다 한 행으로 실어 수정을 받음
- **상대 미정·책임 후보**: 2.5장이 남긴 상대는 `| 상대 미정 | {식별자} | {호스트·근거} |` 행으로, 이름이 책임 문장에 없는 외부 시스템은 `| 책임 후보 | {시스템 이름} | {근거} |` 행으로 같은 표에 실어 수정을 받음
- **호스트 확인**: `hosts_missing`이 참이거나 `미상` 행이 있으면 그 라운드를 `호스트 확인 필요`로 표시하고 사용자 답 없이 기록하지 않음 — `알아서`로 넘어오면 그 환경 키를 빼고 기록하며, 추측 값이나 빈 값을 넣지 않음

## 4. registry.json·deps.json

- **노드**: `domains.{d}.repos.{slug}`에 규약 9장 8키(+`dormant`면 `reason`)를 기록
- **도메인**: 신규 도메인이면 `domains.{d}`에 `description`과 빈 `repos` 기록
- **간선 상대 판정**: 2.5③에서 정해진 target만 그 slug가 registry에 실재하는지 확인
- **간선**: 상대가 정해진 것만 `deps.json`에 간선으로 추가 — `from_me`가 참이면 `deps.{현재 레포}`에 `to: {상대}`로, 거짓이면 `deps.{상대}`에 `to: {현재 레포}`로 넣고 `contracts`는 2.5⑤가 합친 것을 그대로 씀. 상대를 정하지 못한 대상은 보고의 `상대 미정`으로만 남기고 간선을 만들지 않음
- **도메인 이동 — 승인 하나**: `knowledge/{old}/{slug}/`가 있으면 `git mv knowledge/{old}/{slug} knowledge/{new}/{slug}` 대상·건수를 보이고 승인 후 실행, 노드를 `domains.{old}.repos`에서 `domains.{new}.repos`로 옮기고 `deps.json`의 그룹 키와 `to`에 있는 `{old}/{slug}` 끝점을 `{new}/{slug}`로 치환 — `project`가 달라지면 3장에서 함께 물음
- **레포 폴더**: `knowledge/{d}/{slug}/`는 만들지 않음 — 첫 레포 종속 문서가 생길 때 add·update가 만듦

## 5. 검사·커밋·push

- **미러**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" mirror --repo {slug} --wiki {WIKI_ROOT}` — 실패 줄은 6장 보고에 싣고 등록은 그대로 진행
- **검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {WIKI_ROOT}/registry.json {WIKI_ROOT}/deps.json` 에러 0
- **커밋**: `chore(register): {slug} → {domain}` 한 커밋에 `registry.json`·`deps.json`을 함께 담고 본문에 `register 조사`(`--dormant`는 `사용자 확인`), 이동이면 `chore(register): {slug} {old} → {new}`
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 상태 표·보고

- **상태 표**: `registry.json`·`state/*.json`과 `{WIKI_ROOT}/.local/mirrors/` 목록으로 `| 레포 | 도메인 | 상태 | 책임 | 간선(out/in) | 브랜치 | 커서 | 미러 |` 표를 출력 — `책임`은 문장 건수 — 커서 없음은 `없음`, 미러는 `{slug}.git` 폴더 유무로 `있음`·`없음`
- **상대 미정**: 4장에서 간선이 되지 못한 `deps[]` 항목을 `| 식별자 | 외부·내부 미등록 | 근거 |`로 나열 — 내부 미등록 상대는 그 레포를 등록하거나 `/llm-wiki:add`로 간선을 직접 넣으면 이어짐
- **조사 품질**: 2.5장의 `미소비 N행`(재질의 뒤에도 어느 레인도 보지 않은 인벤토리 행)과 `선언 위치 위반 N건`(라이브러리 심볼 import를 근거로 낸 http 항목)을 레인별로 적음
- **다음**: 세션을 다시 열면 레포 지도·의존이 주입되고, 머지 반영은 `/llm-wiki:update`, 자료 반영은 `/llm-wiki:add`
