---
name: add
description: Use when material the user hands over or a decision settled in conversation must become facts in the wiki — a pasted spec, a read file, a fetched page, work records, "we agreed X", or a skipped or relocated row in an update PR ("위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘", "건너뜀 처리"). Lists the extracted facts, asks once where a fact differs from the wiki, then opens a wiki PR. NOT for merged code (that is the update skill).
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`(이하 규약), 배정 이후 공통 절차는 `${CLAUDE_PLUGIN_ROOT}/references/apply.md`, 위키 원격 호스트 절차는 `${CLAUDE_PLUGIN_ROOT}/references/publish.md`이며, 서브에이전트에게는 규약·스크립트 경로를 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. `registry.json`·`deps.json`은 규약 9장 편집 주체 범위만 고칩니다.

인자: `--domain {domain}`(대상 도메인), `--dry-run`(PR 본문 `{work}/pr.md`까지 쓰고 커밋·push·PR 없음). 그 밖의 인자와 대화 맥락은 2절 입력입니다.

## 1. 준비

`mktemp -d`를 두 번 실행해 출력 경로를 `{tmp}`(위키 clone)와 `{work}`(추출 산출물)로 쓰고, 위키를 `{tmp}`에 clone합니다.

```
git clone -b {baseBranch} {remote} {tmp}
```

clone이 실패하거나 `{tmp}/registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다.

도메인은 `--domain`이고, 없으면 현재 레포의 `git remote get-url origin`이 registry 노드의 `remote`와 같을 때 그 도메인입니다. 둘 다 아니거나 registry `domains`에 없으면 AskUserQuestion 한 질문으로 고릅니다. 옵션은 도메인마다 `{domain} (레포 N개)`이고 4개를 넘으면 나머지는 기타 입력으로 받습니다.

## 2. 입력 확정

- **입력 집합**: 붙여 넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 정한 문장, update PR(링크 또는 붙여 넣은 본문)의 `제외된 사실 목록` 행, 작업 기록(커밋 메시지, plan, feedback — 등록 레포의 `.devcenter/workspace/progress/*/feedback.md` 같은 파일) — 이 밖의 사실 기록 금지, 에이전트의 추론은 대화 문장이 아님
- **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
- **원문 보관**: 자료마다 번호 `{n}`을 매기고 붙여 넣은 텍스트·대화 문장·가져온 페이지는 `{work}/input/{n}.md`에 원문을 Write, 파일은 경로만 기록하며, 자료마다 규약 8장 근거 줄 값(파일 경로, 등록 레포 파일은 `{slug}@{sha7} {경로}`, 페이지 URL, 자료 제목, 대화 문장은 `사용자 확인 YYYY-MM-DD`)을 정함
- **update PR**: 링크는 `publish.md` 3장으로 읽고, 붙여 넣은 본문은 그대로 씀

## 3. 추출

붙여 넣은 텍스트·대화 문장·update PR 행은 메인이 아래 기준으로 직접 추출합니다. `{지도}`는 도메인 등록 레포마다 `{domain}/{slug}`, registry 노드의 `responsibilities`·`hosts`, `deps` 블록을 JSON 그대로 넣은 것입니다. 파일·페이지 자료는 합쳐 500줄 이하면 메인이 직접, 넘으면 원문의 장(최상위 제목) 단위로 나눠 장마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행합니다. 출력 파일이 없는 장은 4절 전에 다시 실행합니다.

```
자료 한 장에서 위키에 남길 사실을 추출하라.
입력: {input 파일} {장 범위} — 근거 줄 {source}.
기준: `sed -n '/^## 1\./,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 화면 시안, UI 문구 원문, 일정·담당자, "검토 중"·미확정 항목도 담지 않는다.
작업 기록: plan·feedback의 이유·버린 대안·제약·바로잡은 사실은 후보이고, 의도·범위·후속 작업·작업 현황은 1장 변경 서사로 담지 않는다.
금지: 입력 밖 파일 열기, 사전 지식으로 채우기, 원문 절 구조 옮기기.
set: 원소의 뜻을 말하는 사실이면 정의 식별자(심볼 또는 공통코드 그룹 이름), 규칙 문장이 코드를 인용할 뿐이면 빈 문자열.
set_total: 자료가 그 집합의 전체 목록(공통코드 전체 표, enum 전체 정의)을 보여 주면 전 원소 수이고 원소마다 사실을 남긴다, 아니면 0.
충돌: 같은 대상의 값이 둘이면 개정 일자·판본으로 가려 뒤의 값만 남기고 가린 근거를 conflict에 적는다. 가려지지 않으면 둘 다 남기고 conflict에 상대 사실 번호를 적는다 — 뒤쪽이 최신이라 가정하지 않는다. 복합 사실이면 충돌하는 주장만 떼어 낸다.
graph: 레포 소관·책임·서빙 호스트·레포 사이 의존을 말하는 문장은 사실이 아니라 graph에 담는다 — 기준 `sed -n '/^## 9\./,$p' {doc_contract_path}`, 현재 지도 {지도}. slug와 간선 to는 현재 지도의 등록 레포 키로 쓰고, 등록되지 않은 레포는 이름 그대로 둔다.
출력: {work}/facts/{n}-{장}.json에 Write —
{"facts": [{"fact", "topic", "code": "식별자, 없으면 빈 문자열", "slug": "사실이 다루는 등록 레포, 없으면 빈 문자열", "set", "set_total", "loc": "원문 장·절·페이지", "conflict": ""}],
 "graph": [{"slug", "key", "op", "value", "old", "loc"}]}
응답은 사실·후보 건수만.
```

- **update PR 행**: `제외된 사실 목록` 행마다 새 값을 사실로, 문서·기존 값·출처(`{slug}@{sha7}`)를 그대로 옮기고 `check`를 출처 레포와 sha로 두며 근거 줄은 `{PR 링크} {F번호}`

## 4. 목록과 질문

이 스킬의 정지점은 이 절 하나입니다.

- **정리**: 같은 주장을 병합하고 `A1`부터 번호를 매긴 뒤, 사실·후보의 `slug`와 간선 후보 `to`마다 `apply.md` 0장 레포 읽기를 하고 `apply.md` 1장 배정을 먼저 돌려 대상 문서의 기존 값과 다른 사실을 교체 후보로 표시함
- **목록**: 메시지 본문에 사실 표와 지도 후보 표를 출력함

```
| # | 사실 | 문서 | 판정 후보 | 원문 |
| # | 레포 | 변경 | 원문 |
```

- **질문**: 교체 후보(기존 값과 새 값, 코드로 확인되면 현재 값 병기, 옵션 `새 값`·`기존 유지`), 자료 내부 미결 충돌, PR 제외 행의 건너뜀·미해결 충돌(교체 후보와 같음), 위치가 갈리지 않는 사실을 AskUserQuestion으로 묻고 마지막에 `진행`·`수정`(수정 내용은 기타 입력) 한 질문을 둠 — 한 라운드 4질문까지이며 넘치면 같은 정지점에서 라운드를 잇고, 교체 외 행에는 권장안을 첫 옵션으로 둠
- **답 반영**: `새 값`은 `quote`를 `사용자 확인 YYYY-MM-DD 새 값 선택`으로 두고, `기존 유지`와 교체 후보의 `모름`은 사실을 빼서 6절 미기록 표로 넘기며, 그 밖의 `모름`은 권장안을 채택함
- **답 원문**: 질문과 답을 `{work}/input/answers.md`에 Write하고, 답으로 정해진 사실은 `input`에 이 파일을, `source`에 `사용자 확인 YYYY-MM-DD`를 더함 — 검토의 자료 대조가 답을 원문으로 보지 못하면 자료 속 다른 값으로 되돌림
- **기록**: `apply.md` 0장 형식으로 `{work}/facts.json`·`{work}/graph-candidates.json`을 씀 — `check`는 준비한 `{workspace.root}/{slug}`와 `origin/{defaultBranch}`(등록 레포 파일 근거면 그 sha), `input`은 그 사실을 낸 자료의 원문 파일, `source`는 2절 근거 줄
- **브랜치**: `--dry-run`이 아니면 `git -C {tmp} switch -c wiki-add/{YYYYMMDD-HHMM}`

## 5. 반영

`apply.md` 1~7장을 실행합니다. 1장 배정은 4절 답을 반영해 다시 쓰며, update PR 행은 옮긴 문서로 배정합니다.

## 6. 게시·보고

`${CLAUDE_PLUGIN_ROOT}/templates/wiki-pr.md`대로 `{work}/pr.md`를 씁니다. `--dry-run`이면 `{work}/pr.md`·`{tmp}`·`{work}` 경로와 미기록 표를 보고하고 지우지 않은 채 종료합니다. `{tmp}`에 새 커밋이 없으면 게시하지 않고 집계만 보고합니다. 있으면 `publish.md` 2장으로 push·PR을 만듭니다.

PR 링크, 요약 집계 한 줄, 미기록 표, "머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`로 지웁니다. 미기록 표는 `기존 유지` 행, 자료에 없어 기록하지 못한 항목, 검토 `conflicts`(미해결 충돌), 지도 `rejected`를 담습니다. 어느 단계든 실패하면 지우지 않고 `{tmp}`·`{work}` 경로와 원인을 보고합니다.

```
| 사실 | 위치 | 기존 값 | 새 값·사유 |
```
