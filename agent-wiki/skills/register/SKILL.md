---
name: register
description: Survey the current repo with subagents and record it in the wiki as a node with dependency edges.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. registry·deps는 1절 임시 clone `{tmp}`의 파일입니다. 인자로 범위 지시가 오면 registry의 slug·도메인과 대조해 slug 목록으로 바꾸고, 대조되지 않는 이름은 보고 후 확인받습니다(`인자 없이 진행`·`중단`, 다른 이름은 기타 입력). 인자가 있으면 재등록이어도 인자가 간선 대상을 정하고, 대조된 slug가 0개면 간선 대상은 없습니다.

## 1. 위키 clone

`mktemp -d`가 출력한 경로를 `{tmp}`로 쓰고, 위키를 `{tmp}`에 clone합니다.

```
git clone -b {baseBranch} {remote} {tmp}
```

clone이 실패하거나 `{tmp}/registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다.

## 2. 메타 질문

현재 레포의 `{origin}`은 `git remote get-url origin` 결과이고, slug는 그 마지막 경로에서 `.git`을 뺀 소문자입니다. slug가 registry에 있으면 재등록이므로 이 절을 건너뛰고 기존 도메인과 `defaultBranch`를 씁니다.

신규 slug면 레포 준비 전에 AskUserQuestion 한 라운드로 네 가지를 묻습니다. 질문마다 옵션은 2~4개이고 자유 입력은 기타 입력으로 받습니다. 기존 도메인이 없으면 신규 도메인 후보 이름 2개를 옵션으로 두고, 등록 레포가 없으면 연동 레포 질문을 빼고 간선 대상 없음으로 진행합니다.

- **도메인**: 기존 도메인 하위에 등록(가까운 기존 도메인 최대 3개) 또는 신규 도메인 생성(`{조직}-{도메인}` 이름과 description 한 줄)
- **역할**: 이 레포가 하는 일 한 줄(현재 레포 README의 첫 설명 줄을 후보로), 또는 `분석으로 작성`
- **연동 레포**: 이 레포가 호출·구독·의존하는 등록 레포(multiSelect), 또는 `모름`(전체 등록 레포 조사)
- **기본 브랜치**: 아래 명령의 원격 기본 브랜치, 또는 다른 브랜치

```
git ls-remote --symref {origin} HEAD
```

인자로 범위 지시가 있으면 연동 레포 질문은 생략하고 인자를 씁니다.

## 3. 레포 준비

현재 레포와 간선 대상 등록 레포(인자, 연동 레포 답, 둘 다 없으면 현재 레포를 뺀 전체)를 워크스페이스에 원격 기본 브랜치 최신으로 준비합니다. 간선 대상 slug는 모두 나열하며, 없으면 비웁니다.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_register_repositories.py {tmp}/registry.json {workspace.root} --current {slug} {origin} {defaultBranch} [target ...]
```

레포마다 `ok`·`fail` 한 줄이 나옵니다. `fail` 줄의 등록 레포는 간선 탐색에서 빼고 보고하며, 현재 레포가 `fail`이면 중단합니다.

## 4. 분석

노드 에이전트 1개와 간선 대상 레포마다 간선 에이전트 1개를 `model: sonnet` Agent로 한 메시지에 병렬 실행합니다. `{hint}`에는 역할 답이나 재등록의 기존 `summary`·`responsibilities`를(`분석으로 작성`이면 `없음`), 간선의 `{domain}`에는 대상 레포의 도메인을, 대상 정보에는 registry 값을 JSON 그대로 넣습니다.

```
{workspace.root}/{slug}를 분석하라. 스크립트로 코드를 추출하지 말라.
참고 정보(검증 대상): {hint} — 코드와 맞는 문장은 그대로 쓰고, 다르면 코드를 따르라.
기술 스택을 가정하지 말고 빌드·설정 파일부터 확인한 뒤 소스를 전수로 읽어라.
전수 읽기는 git ls-files로 소스 목록을 만들고 Read 도구로 파일마다 끝까지 여는 것이다. 여러 파일을 cat·for 루프로 한 출력에 이어 붙이지 말라(긴 출력은 잘린다). 파일명·grep 결과로 내용을 추정하지 말라. 제외는 lock·빌드 산출물·vendor·node_modules·바이너리뿐이다.
소스가 많아 다 열 수 없으면 진입점·라우트·메시지 발행/구독·외부 클라이언트·스케줄러·설정 파일을 먼저 열고, 열지 못한 파일은 추정하지 말고 미열람 목록에 적어라.
stack에는 언어·주 프레임워크만 쓰고 빌드 도구·DB·개별 라이브러리 좌표는 넣지 말라.
hosts에는 이 레포 자신이 요청을 받는 호스트명만 쓴다. 호출하는 API·DB·브로커·캐시 주소는 넣지 말고, 서빙 호스트가 없으면 {}로 둔다.
responsibilities는 기능 단위로 쓰고 헬스체크·공통 설정·빈 스텁은 넣지 않는다.
아래 JSON을 응답하고, 이어서 `필드(배열이면 인덱스): 근거 경로`를 한 줄씩, 마지막 줄에 `읽음 {읽은 소스 수}/{전체 소스 수}`와 읽지 않은 파일 경로를 적어라.
{"stack": ["주 언어·프레임워크, 버전은 주 항목만"],
 "summary": "이 레포가 맡는 일 한 줄",
 "responsibilities": ["이 레포를 참고해야 할 작업 단위 짧은 문장"],
 "hosts": {"qa|stg|prod": "설정·코드에 적힌 서빙 호스트 리터럴, 못 찾은 환경은 키 생략"}}
```

```
현재 레포 {workspace.root}/{slug}가 대상 레포 {workspace.root}/{target}({domain}/{target})을 보고 있는지 확인하라.
대상 정보: summary {summary}, responsibilities {responsibilities}, hosts {hosts}
스크립트로 코드를 추출하지 말라. 기술 스택을 가정하지 말라.
'보고 있다'는 현재 레포의 코드·빌드·설정이 대상의 API·메시지 토픽·테이블·라이브러리를 호출·구독·조회·의존한다는 뜻이다. 대상이 현재 레포를 호출하는 역방향 흔적(CORS 허용 origin 등)과 README·주석·문서의 이름 언급은 해당하지 않는다.
현재 레포에서 import·의존 좌표·URL·호스트·큐·테이블 등 대상의 흔적을 찾고, 대상 레포 코드에서 그 실재를 확인하라.
보고 있으면 첫 줄에 아래 JSON 한 줄을 코드 블록 없이 쓰고 다음 줄부터 근거 파일 경로를, 아니면 설명 없이 `없음` 한 단어만 응답하라.
{"to": "{domain}/{target}", "desc": "대상의 무엇을 현재 레포 어디에서 쓰는지 한 줄"}
```

간선 대상이 없으면 노드 에이전트만 실행합니다.

## 5. 초안 승인

초안 표를 메시지 본문에 출력한 뒤 AskUserQuestion 한 질문(`알아서`·`수정`, 수정 내용은 기타 입력)으로 확인받습니다. 재등록이면 `기존` 칸을 더합니다.

```
| 항목 | 기존 | 초안 | 근거 |
```

행은 domain·remote(`{origin}`)·defaultBranch·stack·summary, responsibilities 문장마다, hosts 환경마다(없으면 `없음` 한 행), 간선마다 하나씩 둡니다. 역할 답이 있으면 summary 초안은 그 문장이고, 연동 레포 답이나 재등록의 기존 간선인데 간선 에이전트가 `없음`이면 `근거 없음` 행으로 보입니다. `알아서`는 초안을 채택하되 재등록에서 기존에만 있는 노드 값은 유지하고, `근거 없음` 간선은 넣지 않습니다. 노드 에이전트의 `읽음` 줄과 미열람 목록도 표 아래에 보입니다.

## 6. 기록

1절의 `{tmp}`에 기록합니다. 승인된 값으로 `{tmp}/registry.json`의 `domains.{domain}.repos.{slug}`를 7키(`remote`·`defaultBranch`·`status: "active"`·`stack`·`summary`·`responsibilities`·`hosts`)로 쓰고, `{tmp}/deps.json`의 `deps.{domain}/{slug}` 블록을 `{"to", "desc"}` 배열로 통째로 교체합니다. 간선이 없으면 그 키를 삭제하고, 신규 도메인이면 `{"description", "repos": {}}`를 만든 뒤 slug를 넣습니다. 수정은 Edit으로 해당 노드·블록 줄만 고치고 파일 서식은 유지하며, 골격 그대로의 한 줄 JSON이면 2칸 들여쓰기로 씁니다.

```
mkdir -p {tmp}/knowledge/{domain}/{slug}
[ -n "$(ls -A {tmp}/knowledge/{domain}/{slug})" ] || touch {tmp}/knowledge/{domain}/{slug}/.gitkeep
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_register_file.py {tmp} {domain}/{slug}
git -C {tmp} add registry.json deps.json knowledge/{domain}/{slug}
git -C {tmp} diff --cached --quiet
git -C {tmp} commit -m "chore(register): {slug} → {domain}"
git -C {tmp} push origin {baseBranch}
```

검증이 종료 코드 1이면 출력대로 고쳐 다시 검증합니다. `diff --cached --quiet`가 종료 코드 0이면 변경이 없으므로 commit·push 두 줄을 실행하지 않고 `변경 없음`으로 보고합니다. push가 거절되면 `git -C {tmp} pull --rebase origin {baseBranch}` 후 한 번 더 push합니다. rebase가 충돌하면 `git -C {tmp} rebase --abort` 후, 두 번째 push도 거절되면 그대로 `{tmp}` 경로와 원인을 보고하고 중단합니다.

## 7. 보고

노드 요약, 간선 목록(`to`·`desc`), 탐색에서 뺀 레포, `읽음` 결과, `git -C {tmp} log -1 --oneline`을 보고한 뒤 `rm -rf {tmp}`로 지웁니다. 로컬 위키 사본에는 다음 세션 시작 때 반영됩니다.
