---
name: register
description: Survey the current repo with subagents and record it in the wiki as a node with dependency edges.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`baseRoot`·`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 인자로 범위 지시가 오면 그 범위의 등록 레포만 간선 탐색합니다.

## 1. 위키 최신화

`{baseRoot}/registry.json`이 있으면 최신화합니다.

```
git -C {baseRoot} pull --ff-only origin {baseBranch}
```

`registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다. 현재 브랜치가 `baseBranch`가 아니면 브랜치 전환·stash 없이 중단 후 보고합니다.

## 2. 레포 준비

등록 레포(범위 지시가 있으면 그 slug만)와 현재 레포를 워크스페이스에 둡니다. 현재 레포의 slug는 `origin` URL 마지막 경로에서 `.git`을 뺀 소문자입니다.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_register_repositories.py {baseRoot}/registry.json {workspace.root} [slug ...]
git remote get-url origin
git clone {remote} {workspace.root}/{slug}
git -C {workspace.root}/{slug} branch --show-current
```

아래 세 줄은 현재 레포용이며, clone은 `{workspace.root}/{slug}`가 없을 때만 실행하고 마지막 명령의 결과를 `defaultBranch`로 씁니다. `fail` 줄의 등록 레포는 간선 탐색에서 빼고 보고하며, 현재 레포의 `fail`은 clone이 성공하면 무시합니다. 현재 레포 clone이 실패하면 중단합니다.

## 3. 분석

노드 에이전트 1개와 등록 레포(현재 레포 제외)마다 간선 에이전트 1개를 `model: sonnet` Agent로 한 메시지에 병렬 실행합니다.

```
{workspace.root}/{slug}를 읽기 전용으로 분석하라. 파일을 고치지 말고, 스크립트로 코드를 추출하지 말라.
기술 스택을 가정하지 말고 빌드·설정 파일부터 확인한 뒤 소스를 전수로 읽어라.
아래 JSON과 필드별 근거 파일 경로를 응답하라.
{"stack": ["주 언어·프레임워크, 버전은 주 항목만"],
 "summary": "이 레포가 맡는 일 한 줄",
 "responsibilities": ["이 레포를 참고해야 할 작업 단위 짧은 문장"],
 "hosts": {"qa|stg|prod": "설정·코드에 적힌 서빙 호스트 리터럴, 못 찾은 환경은 키 생략"}}
```

```
현재 레포 {workspace.root}/{slug}가 대상 레포 {workspace.root}/{target}({domain}/{target})을 보고 있는지 읽기 전용으로 확인하라.
대상 정보: summary {summary}, responsibilities {responsibilities}, hosts {hosts}
파일을 고치지 말고, 스크립트로 코드를 추출하지 말라. 기술 스택을 가정하지 말라.
현재 레포에서 import·의존 좌표·URL·호스트·큐·테이블·이름 등 대상의 흔적을 찾고, 대상 레포 코드에서 그 실재를 확인하라.
보고 있으면 아래 JSON과 근거 파일 경로를, 아니면 "없음"만 응답하라.
{"to": "{domain}/{target}", "desc": "대상의 무엇을 현재 레포 어디에서 쓰는지 한 줄"}
```

등록 레포가 없으면 노드 에이전트만 실행합니다.

## 4. 초안 승인

AskUserQuestion 한 라운드로 도메인과 초안 표를 확인받습니다.

```
| 항목 | 초안 | 근거 |
```

행은 remote·defaultBranch·stack·summary, responsibilities 문장마다, hosts 환경마다, 간선마다 하나씩 둡니다. 도메인은 registry의 기존 도메인 중 선택하거나 신규 `{조직}-{도메인}`과 description 한 줄을 받습니다. 수정은 자유 입력으로 받고 `알아서`는 초안을 채택합니다. 이미 등록된 slug면 기존 도메인을 유지하고 기존 값과 초안을 함께 보입니다.

## 5. 기록

승인된 값으로 `registry.json`의 `domains.{domain}.repos.{slug}`를 7키(`remote`·`defaultBranch`·`status: "active"`·`stack`·`summary`·`responsibilities`·`hosts`)로 쓰고, `deps.json`의 `deps.{domain}/{slug}` 블록을 `{"to", "desc"}` 배열로 통째로 교체합니다. 간선이 없으면 그 키를 삭제하고, 신규 도메인이면 `description`과 빈 `repos`를 함께 씁니다.

```
mkdir -p {baseRoot}/knowledge/{domain}/{slug}
touch {baseRoot}/knowledge/{domain}/{slug}/.gitkeep
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_register_file.py {baseRoot} {domain}/{slug}
git -C {baseRoot} add registry.json deps.json knowledge/{domain}/{slug}
git -C {baseRoot} commit -m "chore(register): {slug} → {domain}"
git -C {baseRoot} push origin {baseBranch}
```

`.gitkeep`은 폴더가 비어 있을 때만 만듭니다. 검증이 종료 코드 1이면 출력대로 고쳐 다시 검증합니다. push가 거절되면 `git -C {baseRoot} pull --rebase origin {baseBranch}` 후 한 번 더 push하고, 충돌이면 `git -C {baseRoot} rebase --abort` 후 보고합니다.

## 6. 보고

노드 요약, 간선 목록(`to`·`desc`), 탐색에서 뺀 레포, `git -C {baseRoot} log -1 --oneline`을 보고합니다.
