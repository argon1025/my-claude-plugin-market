---
name: update
description: Inspect a domain’s merges for confirmed decisions and reusable project knowledge. Report policy discrepancies and open a wiki PR with the documents and cursors.
disable-model-invocation: true
---

먼저 [실행 환경 연결](../../references/runtime.md)을 읽고 패키지 경로·질문·위임 도구를 확정합니다.

`{PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 판정 기준은 `{PLUGIN_ROOT}/references/doc-contract.md`(이하 규약), 배정 이후 공통 절차는 `{PLUGIN_ROOT}/references/apply.md`, 위키 원격 호스트 절차는 `{PLUGIN_ROOT}/references/publish.md`이며, 서브에이전트에게는 규약·스크립트 경로를 `{PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. `registry.json`·`deps.json`은 규약 9장 편집 주체 범위만 고칩니다.

인자: `--domain {domain}`(대상 도메인), `--max-merges N`(머지 예산, 기본 10), `--dry-run`(PR 본문 `{work}/pr.md`까지 쓰고 커밋·push·PR 없음).

## 1. 준비

`mktemp -d`를 두 번 실행해 출력 경로를 `{tmp}`(위키 clone)와 `{work}`(추출 산출물)로 쓰고, 위키를 `{tmp}`에 clone합니다.

```
git clone -b {baseBranch} {remote} {tmp}
```

clone이 실패하거나 `{tmp}/registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다.

`--domain`이 없거나 registry `domains`에 없으면 질문 도구 한 질문으로 도메인을 고릅니다. 옵션은 도메인마다 `{domain} (레포 N개)`이고 4개를 넘으면 나머지는 기타 입력으로 받으며, 현재 레포의 `git remote get-url origin`이 registry 노드의 `remote`와 같으면 그 도메인을 첫 옵션으로 둡니다.

`--dry-run`이 아니면 `publish.md` 1장으로 열린 update PR을 확인합니다.

## 2. 범위

```
python3 {PLUGIN_ROOT}/scripts/collect_update_merges.py --wiki {tmp} --workspace {workspace.root} --domain {domain} --out {work} [--start {slug}={rev}]... [--max-merges N]
```

마지막 줄이 `{work}/work.json` 경로이며, 종료 코드별로 처리합니다.

- **20**: `work.json` `unset`의 레포마다 질문 도구으로 시작 지점을 묻고(한 라운드 4질문까지, 옵션은 `candidates`의 `{label} ({sha7})`, 다른 sha는 기타 입력) 답마다 `--start {slug}={sha}`를 붙여 다시 실행함 — 시작 지점 이후 머지부터 반영되며 `HEAD`는 반영 없이 커서만 기록함
- **10**: `미처리 없음` 한 줄과 `skipped` 사유를 보고하고 `rm -rf {tmp} {work}` 후 종료
- **1**: stderr를 전달하고 중단
- **0**: `--dry-run`이 아니면 `git -C {tmp} switch -c wiki-update/{YYYYMMDD-HHMM}`

## 3. 추출

레포별 `batches`마다(다시 나누지 않음) 서브에이전트 1회를 실행 환경 연결에 따라 한 메시지에 최대 15개씩 병렬 실행하고, 출력 파일이 없는 묶음은 4절 전에 다시 실행합니다. `{diff 목록}`은 그 묶음 `diffs`, `{slug}`는 묶음의 레포입니다.

```
머지 1건(큰 머지는 조각 묶음)에서 위키에 남길 사실을 추출하라.
입력: {diff 목록}을 목록 순서대로 한 파일씩 머리말의 줄 수까지 Read(길면 offset으로 나눔) — 머리말에 PR 제목·커밋 메시지·변경 파일 목록·조각 번호가 있다. 현재 지도는 {tmp}/registry.json의 `domains.{domain}.repos`(이 레포는 `{slug}` 노드의 responsibilities·hosts, 키 목록이 도메인 등록 레포)와 {tmp}/deps.json의 `deps."{domain}/{slug}"` 블록이다.
대상: 변경 줄, 커밋 메시지, diff 속 작업 기록과 여기서 직접 가리키는 규격·결정 원문이 명시한 사실만 — 바뀌지 않은 문맥에서 추론한 사실(부재 주장 등)은 담지 않는다. 작업 기록 파일은 추가되거나 고쳐진 줄의 현재 문장만 읽고, 기록에서 지워진 줄은 deleted의 근거로 쓰지 않는다.
기준: `sed -n '/^## 1\./,/^## 3\./p' {doc_contract_path}` — 1장으로 담을 문장을 고르고 2장으로 scope를 정한다.
graph: 레포 소관·책임·서빙 호스트·의존의 현황은 graph 후보로 둔다. 같은 근거에 확정된 서비스 간 의무가 있으면 정책도 facts에 담는다. 지도 후보의 코드 확인 결과는 정책 반영에 영향을 주지 않는다 — 기준 `sed -n '/^## 9\./,$p' {doc_contract_path}`. 현재 responsibilities가 덮지 않는 새 기능 단위(엔드포인트 묶음·메시지 구독·스케줄러)는 responsibilities add이고, 간선 to는 현재 지도의 등록 레포만 쓴다.
정책은 적용 대상과 보장할 동작을 밝힌 규격·결정 원문이 있을 때만 facts에 둔다. quote에 해당 문구를, loc에 판본·절이나 결정 기록 위치를 적는다. 머지가 가리키는 규격·결정은 필요한 부분을 직접 확인한다. 확인할 수 없는 링크나 머지 SHA만으로 정책을 쓰지 않는다.
프로젝트 지식은 해당 레포에서 반복되는 코드 밖 제약과 그 근거를 남긴다. 작업 기록의 파일명이나 커밋됐다는 사실은 정책·제약의 근거가 되지 않는다.
관찰: 외부에서 보이는 코드·테스트 동작은 기존 정책과 대조할 수 있게 대상·조건·관찰값·근거를 observations에 담는다. 내부 리팩터링과 계약에 영향이 없는 편의 기능은 제외한다. 정책 결정과 구현 값이 다르면 결정은 facts에, 구현 값은 observations에 둔다.
병합: 같은 대상·조건·주장이면 shas를 합친다. 구현 순서로 서로 다른 결정을 가리지 않는다.
금지: 근거 없는 추론, diff 원문을 발췌만 읽기.
출력: {work}/facts/{slug}/{batch_id}.json에 Write —
{"facts": [{"fact": "현재 상태 한 문장(업무 낱말 우선, 식별자 괄호 병기, 줄바꿈 금지) — deleted면 지워지기 전 상태",
            "topic": "2~4낱말 주제",
            "code": "저장소 상대 경로 또는 경로#심볼",
            "scope": "root(도메인 루트)|repo(레포 폴더) — 두 성격이면 사실을 둘로 나눔",
            "deleted": false,
            "quote": "규격·결정 또는 프로젝트 제약의 근거 문구", "loc": "그 원문 위치",
            "set": "닫힌 집합 원소의 뜻을 말하면 정의 식별자(심볼·공통코드 그룹), 코드를 인용만 하면 빈 문자열",
            "set_total": 0,
            "shas": ["근거 머지 sha7"]}],
 "observations": [{"대상", "조건", "동작", "code", "shas"}],
 "graph": [{"key": "responsibilities|hosts|deps", "op": "add|remove|replace",
            "value": "책임 문장, {\"env\", \"host\"}, {\"to\", \"desc\"} 중 하나", "old": "교체·삭제면 기존 값",
            "code": "저장소 상대 경로 또는 경로#심볼", "shas": ["근거 머지 sha7"]}]}
deleted는 해당 정책 폐지 결정이나 프로젝트 제약 해소 근거가 있을 때만 true다. set_total은 해당 사실의 근거가 집합 전체를 보장할 때만 그 원소 수이고 아니면 0이다. 사실·관찰·지도 후보가 없는 배열은 비운다. 응답은 사실·후보 건수만.
```

## 4. 정리

메인이 `{work}/facts/**/*.json`을 모두 읽어 정리합니다.

- **병합**: 묶음 사이 같은 주장은 하나로 합치고 `shas`는 합집합 — `deleted`가 다르면 합치지 않음
- **대체**: 같은 적용 대상에서 뒤의 결정이 앞의 결정을 대체했다는 근거가 있을 때만 앞 사실을 `rejected`에 `대체 — {남긴 사실 id}`로 옮긴다. 관계가 불명확하면 두 근거를 기존 문서와 대조하고 6절의 질문 기준을 먼저 적용한다.
- **번호**: 표시 순서는 `order`를 따라 `F1`부터 매긴다. 지도 후보는 같은 레포·대상의 실제 변경 순서로 병합·대체하고 `G1`부터 매긴다.
- **관찰 대조**: 기존 문서와 이번 머지에서 찾은 유효한 후속 결정의 대상·조건을 확인한다. 위반을 보고하기 전에 해당 레포의 이번 수집 마지막 커밋에서 동작을 확인한다. 코드가 보장을 위반하면 해당 코드 위치와 정책 원문을 결과에 보고한다. 규격에 없는 예외의 지속 보장을 이번 요청에서 정해야 하면 배정 전에 6절로 확인한다. 새로 확정된 의무는 답변 원문·결정권자·적용 대상을 갖춘 신규 정책 사실로 만들어 함께 배정한다. 보장 밖 편의 기능이나 동작이 보존된 리팩터링은 문서를 편집하지 않는다.

`apply.md` 0장 형식으로 `{work}/facts.json`과 `{work}/graph-candidates.json`을 쓴다. 사실의 `slug`는 추출한 레포이고 `source`는 `{slug}@{sha7}`와 원문 위치, `quote`는 확인한 근거 문구다. 문서 검토의 `check`는 레포마다 이번에 처리하는 마지막 커밋(`work.json`의 해당 레포 `commits[-1].sha`)과 로컬 경로다. 예산 밖 커밋은 포함하지 않는다. `input`에는 결정·제약을 확인한 diff 파일 또는 확인한 원문 사본의 경로를 넣는다. 지도 후보의 `check`에는 후보의 마지막 근거 커밋과 로컬 경로를 넘긴다.

## 5. 반영

`apply.md` 1~5장을 실행한다.

## 6. 미결 결정

결정 원문끼리 충돌하거나 규격에 없는 코드 예외를 발견하면 현재 근거와 적용 대상을 보고한다. 이번 요청에서 보장 여부를 정해야 할 때만 그 근거를 보여 주고 결정권자에게 한 번에 하나씩 묻는다. 응답이 없거나 결정권을 확인할 수 없으면 해당 항목을 편집에서 빼고 보고한다. 코드와 정책의 차이만으로 정책 선택을 묻지 않는다.

새 결정이 있으면 질문과 답을 `{work}/input/answers.md`에 쓰고 해당 사실의 `quote`·`source`·`input`에 반영한다. 4절에서 해결한 사실은 5절에서 함께 반영한다. 검토 중 드러난 충돌은 해당 문서에 새로 결정된 사실만 assign-ask.json으로 배정한다. 2·3장을 다시 실행해 결과를 별도 .ask.json에 쓰고, 5장 원복은 이번 재반영분에만 적용하고 프로젝트 사본도 최종 결정에 맞춰 정리한다. 앞서 반영한 다른 사실의 결과를 보존한다. 여기서 장 번호는 `apply.md` 기준이다.

## 7. 커서

`repos`의 레포마다 커서 sha를 정합니다.

- **기본**: `commits`의 마지막 머지 — 사실 0건 머지와 `검토 기각` 사실의 머지도 전진함, reject는 다시 실행해도 같은 내용 판정임
- **부트스트랩**: `bootstrapped`이고 `commits`가 비면 `cursor`(시작 지점)
- **불변**: 부트스트랩이 아니고 `commits`가 비면 쓰지 않음

## 8. 지도·커밋

`apply.md` 6·7장을 실행합니다. `--dry-run`이 아니면 이어서 커서를 정한 레포마다 `{tmp}/state/{slug}.json`에 `{"cursor": "{전체 sha}", "at": "YYYY-MM-DD"}`를 Write하고, 모두 쓴 뒤 커밋 한 개로 남깁니다. 본문은 레포마다 `{slug} {sha7}` 한 줄입니다.

```
git -C {tmp} add state
git -C {tmp} commit -m "chore(update): 커서 {N}개 레포 · 머지 {M}건" -m "{본문}"
```

## 9. 게시·보고

`{PLUGIN_ROOT}/templates/wiki-pr.md`대로 `{work}/pr.md`를 씁니다. 집계는 레포별 처리 머지·예산 밖 이월·`skipped` 사유와 액션별 건수, 4절 관찰과 검토 differences에서 확인한 정책 위반의 두 값·근거, 미결 항목입니다. `--dry-run`이면 집계와 `{work}/pr.md`·`{tmp}`·`{work}` 경로를 보고하고 지우지 않은 채 종료합니다. `{tmp}`에 새 커밋이 없으면 게시하지 않고 집계만 보고합니다. 있으면 `publish.md` 2장으로 push·PR을 만들고, PR 링크, 집계, "머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`로 지웁니다. 어느 단계든 실패하면 지우지 않고 `{tmp}`·`{work}` 경로와 원인을 보고합니다.
