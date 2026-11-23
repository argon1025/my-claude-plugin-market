---
name: add
description: Use when material the user hands over or a decision settled in conversation must become facts in the wiki — a pasted spec, a read file, a fetched page, work records, or "we agreed X" ("위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘"). Record scoped decisions and reusable project knowledge with their sources, then open a wiki PR. Ask only about unresolved decisions. NOT for merged code (that is the update skill).
---

먼저 [실행 환경 연결](../../references/runtime.md)을 읽고 패키지 경로·질문·위임 도구를 확정합니다.

`{PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 판정 기준은 `{PLUGIN_ROOT}/references/doc-contract.md`(이하 규약), 배정 이후 공통 절차는 `{PLUGIN_ROOT}/references/apply.md`, 위키 원격 호스트 절차는 `{PLUGIN_ROOT}/references/publish.md`이며, 서브에이전트에게는 규약·스크립트 경로를 `{PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. `registry.json`·`deps.json`은 규약 9장 편집 주체 범위만 고칩니다.

인자: `--domain {domain}`(대상 도메인), `--dry-run`(PR 본문 `{work}/pr.md`까지 쓰고 커밋·push·PR 없음). 그 밖의 인자와 대화 맥락은 2절 입력입니다.

## 1. 준비

`mktemp -d`를 두 번 실행해 출력 경로를 `{tmp}`(위키 clone)와 `{work}`(추출 산출물)로 쓰고, 위키를 `{tmp}`에 clone합니다.

```
git clone -b {baseBranch} {remote} {tmp}
```

clone이 실패하거나 `{tmp}/registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다.

도메인은 `--domain`이고, 없으면 현재 레포의 `git remote get-url origin`이 registry 노드의 `remote`와 같을 때 그 도메인입니다. 둘 다 아니거나 registry `domains`에 없으면 질문 도구 한 질문으로 고릅니다. 옵션은 도메인마다 `{domain} (레포 N개)`이고 4개를 넘으면 나머지는 기타 입력으로 받습니다.

## 2. 입력 확정

- **입력 집합**: 붙여 넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 정한 문장, 작업 기록(커밋 메시지, 저장소에 남은 계획·결정 기록 문서) — 이 밖의 사실 기록 금지, 에이전트의 추론은 대화 문장이 아님
- **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
- **원문 보관**: 자료마다 번호 `{n}`을 매기고 붙여 넣은 텍스트·대화 문장·가져온 페이지는 `{work}/input/{n}.md`에 원문을 Write, 파일은 경로만 기록하며, 자료마다 규약 8장 근거 줄 값(파일 경로, 등록 레포 파일은 `{slug}@{sha7} {경로}`, 페이지 URL, 자료 제목, 대화 문장은 `사용자 확인 YYYY-MM-DD`)을 정함

## 3. 추출

붙여 넣은 텍스트·대화 문장은 메인이 아래 기준으로 직접 추출합니다. 파일·페이지 자료는 합쳐 500줄 이하면 메인이 직접, 넘으면 원문의 장(최상위 제목) 단위로 나눠 장마다 서브에이전트 1회를 실행 환경 연결에 따라 한 메시지에 병렬 실행합니다. 출력 파일이 없는 장은 4절 전에 다시 실행합니다.

```
자료 한 장에서 위키에 남길 사실을 추출하라.
입력: {input 파일} {장 범위} — 근거 줄 {source}. 현재 지도는 {tmp}/registry.json의 `domains.{domain}.repos`(노드의 responsibilities·hosts, 키 목록이 도메인 등록 레포)와 {tmp}/deps.json의 `deps`에서 `{domain}/`로 시작하는 블록이다.
기준: `sed -n '/^## 1\./,/^## 3\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 화면 시안, UI 문구 원문, 일정·담당자, "검토 중"·미확정 항목도 담지 않는다.
정책은 적용 대상과 필수 동작을 명시한 규격·확정 결정의 문구를 quote에, 문서 판본과 절 또는 대화 출처를 loc에 적는다. 승인 전 계획이나 코드 설명을 결정으로 해석하지 않는다. 프로젝트 지식은 해당 레포와 반복해서 필요한 이유가 입력에 있어야 한다. 코드 관찰만 있으면 문서 후보에서 빼고, 유효한 정책과 어긋나는지 대조할 경계 동작은 관찰로 따로 반환한다.
금지: 입력 밖 파일 열기, 사전 지식으로 채우기, 원문 절 구조 옮기기.
deleted: 규약 7장의 제거 근거가 있으면 true로 두고 제거할 문장을 fact에 쓴다.
set: 원소의 뜻을 말하는 사실이면 정의 식별자(심볼 또는 공통코드 그룹 이름), 규칙 문장이 코드를 인용할 뿐이면 빈 문자열.
set_total: 해당 사실의 근거가 보장하는 집합 전체를 보여 주면 전 원소 수이고 원소마다 사실을 남긴다, 아니면 0.
충돌: 대상·조건이 같고 후속 결정이 앞선 값을 대체한 근거가 있으면 현행 값만 남기고 근거를 conflict에 적는다. 가려지지 않으면 둘 다 남기고 conflict에 상대 사실 번호를 적는다 — 뒤쪽이 최신이라 가정하지 않는다. 복합 사실이면 충돌하는 주장만 떼어 낸다.
graph: 레포 소관·책임·서빙 호스트·의존의 현황은 graph 후보로 둔다. 같은 근거에 확정된 서비스 간 의무가 있으면 정책도 facts에 담는다. 지도 후보의 코드 확인 결과는 정책 반영에 영향을 주지 않는다 — 기준 `sed -n '/^## 9\./,$p' {doc_contract_path}`. slug와 간선 to는 현재 지도의 등록 레포 키로 쓰고, 등록되지 않은 레포는 이름 그대로 둔다.
출력: {work}/facts/{n}-{장}.json에 Write —
{"facts": [{"fact", "topic", "code": "식별자, 없으면 빈 문자열", "slug": "사실이 다루는 등록 레포, 없으면 빈 문자열", "scope": "root|repo", "quote": "변경을 뒷받침하는 원문", "deleted": false, "set", "set_total", "loc": "원문 장·절·페이지", "conflict": ""}],
 "observations": [{"대상", "동작", "loc"}],
 "graph": [{"slug", "key", "op", "value", "old", "loc"}]}
응답은 사실·후보 건수만.
```


## 4. 목록과 질문

- 같은 주장을 병합해 `A1`부터 번호를 매기고, 자료별 `source`에 원문 위치(`loc`)를 포함한다. 레포와 지도 후보는 `apply.md` 0장에 따라 준비한다.
- 적용 대상과 기존 정책·출처를 대조해 사실, 대상 문서, 판정, 근거를 표로 보인다. 레포 지도 후보도 별도 표에 레포·변경·원문을 보인다. 정책과 다른 관찰은 두 값과 출처를 보고한다. 규격에 없는 예외를 발견하면 현재 동작과 근거를 보고하고, 이번 요청에서 그 예외를 보장할지 정해야 할 때만 결정권자에게 묻는다. 결정 전에는 문서에 쓰지 않는다.
- 같은 범위의 유효한 규격·결정이 확인되면 바로 반영한다. 두 근거의 관계나 보장할 범위를 확인할 수 없고 이번 요청에서 결정해야 하면, 두 값과 출처를 보여 주고 결정권자에게 한 가지씩 묻는다. 확인되지 않은 항목은 미기록 표에 남긴다. 별도의 일괄 진행 확인은 받지 않는다.
- 관찰에서 처음 확정된 보장은 신규 정책 사실로 배정한다. 답으로 결정된 사실은 질문과 답을 `{work}/input/answers.md`에 보관하고 `quote`에 결정 문구, `input`에 파일 경로, `source`에 결정 출처를 더한다.
- `apply.md` 0장 형식으로 `{work}/facts.json`·`{work}/graph-candidates.json`을 쓴다. `check`는 준비한 레포와 `origin/{defaultBranch}`(등록 레포 파일 근거면 그 sha), `input`은 해당 원문 파일이다. 레포 폴더에 쓸 사실의 slug가 불분명하면 자료의 출처로 확인하고 확인되지 않으면 배정하지 않는다.
- **브랜치**: `--dry-run`이 아니면 `git -C {tmp} switch -c wiki-add/{YYYYMMDD-HHMM}`

## 5. 반영

`apply.md` 1~5장을 실행합니다. 검토 또는 재배정에서 처음 발견한 충돌도 4절 기준으로 판단합니다. 이번 요청에 결정이 필요하면 두 근거를 보여 주고 하나씩 묻습니다. 답변은 원문·출처로 보관하고 해당 사실만 다시 배정해 반영·검토합니다. 재반영 뒤에는 5장의 원복과 프로젝트 사본 정리까지 최종 결정에 맞춰 다시 실행합니다. 앞서 검토를 통과한 다른 변경은 보존하고 미결 항목은 미기록 표에 남깁니다. 마지막에 6·7장을 실행합니다.

## 6. 게시·보고

`{PLUGIN_ROOT}/templates/wiki-pr.md`대로 `{work}/pr.md`를 씁니다. 4절 관찰과 검토 differences에서 확인한 정책 위반은 두 값과 근거를 함께 보고합니다. `--dry-run`이면 `{work}/pr.md`·`{tmp}`·`{work}` 경로와 미기록 표를 보고하고 지우지 않은 채 종료합니다. `{tmp}`에 새 커밋이 없으면 집계와 미기록 사유를 보고하고 종료합니다. 있으면 `publish.md` 2장으로 push·PR을 만듭니다.

게시했으면 PR 링크, 요약 집계 한 줄, 미기록 표, "머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`로 지웁니다. 미기록 표는 결정 근거를 확인하지 못한 행, 자료에 없어 기록하지 못한 항목, 검토 `conflicts`(미해결 충돌), 지도 `rejected`를 담습니다. 어느 단계든 실패하면 지우지 않고 `{tmp}`·`{work}` 경로와 원인을 보고합니다.

```
| 사실 | 위치 | 기존 값 | 새 값·사유 |
```
