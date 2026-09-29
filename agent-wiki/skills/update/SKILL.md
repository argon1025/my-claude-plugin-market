---
name: update
description: Reflect merged code of one domain's registered repos into the wiki in time-ordered batches and open a wiki PR carrying the docs and cursors.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`(이하 규약)이고 위키 원격 호스트 절차는 `${CLAUDE_PLUGIN_ROOT}/references/publish.md`이며, 서브에이전트에게는 규약·스크립트 경로를 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. 이 스킬은 `registry.json`·`deps.json`을 고치지 않습니다.

인자: `--domain {domain}`(대상 도메인), `--max-merges N`(머지 예산, 기본 40), `--dry-run`(7절 보고까지, 커밋·push·PR 없음).

## 1. 준비

`mktemp -d`를 두 번 실행해 출력 경로를 `{tmp}`(위키 clone)와 `{work}`(추출 산출물)로 쓰고, 위키를 `{tmp}`에 clone합니다.

```
git clone -b {baseBranch} {remote} {tmp}
```

clone이 실패하거나 `{tmp}/registry.json`이 없으면 `/agent-wiki:init` 실행을 안내하고 중단합니다.

`--domain`이 없거나 registry `domains`에 없으면 AskUserQuestion 한 질문으로 도메인을 고릅니다. 옵션은 도메인마다 `{domain} (레포 N개)`이고 4개를 넘으면 나머지는 기타 입력으로 받으며, 현재 레포의 `git remote get-url origin`이 registry 노드의 `remote`와 같으면 그 도메인을 첫 옵션으로 둡니다.

`--dry-run`이 아니면 `publish.md` 1장으로 열린 update PR을 확인합니다.

## 2. 범위

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect_update_merges.py --wiki {tmp} --workspace {workspace.root} --domain {domain} --out {work} [--start {slug}={rev}]... [--max-merges N]
```

마지막 줄이 `{work}/work.json` 경로이며, 종료 코드별로 처리합니다.

- **20**: `work.json` `unset`의 레포마다 AskUserQuestion으로 시작 지점을 묻고(한 라운드 4질문까지, 옵션은 `candidates`의 `{label} ({sha7})`, 다른 sha는 기타 입력) 답마다 `--start {slug}={sha}`를 붙여 다시 실행함 — 시작 지점 이후 머지부터 반영되며 `HEAD`는 반영 없이 커서만 기록함
- **10**: `미처리 없음` 한 줄과 `skipped` 사유를 보고하고 `rm -rf {tmp} {work}` 후 종료
- **1**: stderr를 전달하고 중단
- **0**: `--dry-run`이 아니면 `git -C {tmp} switch -c wiki-update/{YYYYMMDD-HHMM}`

`work.json`은 `order[{slug, sha7, date}]`(선택 머지의 시각 순), `repos[slug]{path, branch, head, cursor, bootstrapped, commits, batches[{id, shas, bytes}], remaining}`, `skipped{slug: 사유}`를 담습니다. 묶음은 다시 나누지 않으며, `skipped`와 `remaining`은 PR 본문 `레포` 절 비고로 넘깁니다.

## 3. 추출

레포별 `batches`마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행합니다. 묶음이 1개이고 머지 3건 이하면 메인이 같은 기준으로 직접 처리하고, 출력 파일이 없는 묶음은 4절 전에 다시 실행합니다. `{diff 목록}`은 그 묶음 `shas`의 `commits[].diff_path`입니다.

```
머지 묶음 1개에서 위키에 남길 사실을 추출하라.
입력: 아래 diff 파일을 순서대로 Read — {diff 목록}. 머리말에 커밋 메시지·변경 파일 목록·절단 여부가 있다.
작업 기록: 커밋 메시지와 diff에 포함된 작업 기록(plan·feedback 같은 문서)은 코드가 드러내지 못하는 이유·버린 대안·도메인 규칙의 원천이다. 그 추가 줄을 코드 diff와 함께 후보로 보되, 미확정 계획·작업 현황은 1장대로 담지 않는다.
기준: `sed -n '/^## 1\./,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 레포 지도(소관·의존)는 사실이 아니다.
금지: diff 밖 파일 열기, 사전 지식으로 채우기.
병합: 묶음 안 같은 주장은 하나로 합치고 shas에 모두 적는다. 값이 다른 두 사실은 둘 다 남긴다.
set: 사실이 닫힌 집합(enum·공통코드·상태·허용 채널처럼 원소가 정의된 값) 원소의 뜻을 말하면 정의 식별자(심볼 또는 공통코드 그룹 이름), 아니면 빈 문자열로 둔다. 규칙 문장이 조건·결과로 코드를 인용할 뿐이면 빈 문자열이다.
set_total: set이 있고 diff가 정의 전체(새 enum 파일, 선언 전체가 보이는 hunk)를 보여 주면 전 원소 수, 아니면 0. 정의 전체가 보이면 원소마다 뜻을 사실로 남긴다.
출력: {work}/facts/{slug}/{batch_id}.json에 Write —
{"facts": [{"fact": "현재 상태 한 문장(업무 낱말 우선, 식별자 괄호 병기, 줄바꿈 금지)",
            "topic": "2~4낱말 주제",
            "code": "저장소 상대 경로 또는 경로#심볼",
            "set": "정의 식별자, 아니면 빈 문자열",
            "set_total": 0,
            "quote": "기존 동작을 바꾸는 사실이면 그 의도를 밝힌 커밋 메시지·plan·feedback 원문, 없으면 빈 문자열",
            "shas": ["근거 머지 sha7"]}]}
사실이 없으면 {"facts": []}. 응답은 사실 건수만.
```

## 4. 배정

메인이 `{work}/facts/**/*.json`을 모두 읽어 배정합니다.

- **병합**: 묶음 사이 같은 주장은 하나로 합치고 `shas`는 합집합
- **대체**: 같은 대상의 값이 다른 두 사실은 `order`에서 늦은 머지의 사실만 남기고 앞 사실은 `rejected`에 `대체 — {남긴 사실 id}`로 넘김, 앞 사실이 다른 주장도 담으면 충돌하는 주장만 `fact`에서 빼고 뺀 주장을 같은 사유로 넘김 — 같은 실행 안의 값 변화는 뒤 머지 diff가 변경 근거라 7장 다른 값 판정 대상이 아님
- **번호**: 사실마다 `order`에서 가장 늦은 근거 머지의 `date`를 붙이고 그 순서로 `F1`부터 `id`를 매김 — 문서별 사실 목록도 이 순서
- **위치**: 규약 2장으로 도메인 루트·레포 폴더를 정함
- **대조**: 규약 7장 대조 — 목록은 `{tmp}/knowledge/{domain}/*.md`와 `{tmp}/knowledge/{domain}/{slug}/*.md`의 frontmatter `description`, 본문은 `grep -ril '{핵심 식별자}' {tmp}/knowledge/{domain}`
- **신규 문서**: 대상 문서가 없는 사실은 같은 위치끼리 주제로 묶어 규약 3장 한 주제가 서면 신규 문서 1장(규약 2장 파일명), 서지 않으면 `기각 — 한 주제 아님`

`{work}/assign.json`에 씁니다.

```
{"docs": [{"doc": "knowledge/{domain} 기준 상대 경로", "created": true,
           "facts": [{"id", "fact", "topic", "code", "set", "set_total", "quote", "slug", "shas", "date"}]}],
 "rejected": [{"id", "fact", "shas", "reason"}]}
```

## 5. 반영

`docs`의 문서마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행하며, 에이전트는 커밋하지 않습니다.

```
위키 문서 한 장에 사실 여러 건을 반영하라.
입력: {work}/assign.json `docs`에서 `doc`이 "{doc}"인 항목 — 문서 {tmp}/knowledge/{domain}/{doc}, 신규 여부, 사실 행.
기준: `sed -n '/^## 2\./,/^## 8\./p' {doc_contract_path}` — 2~7장.
판정: 사실을 주어진 순서대로 7장으로 판정한다 — 동일·추가·교체는 본문에 반영하고, 건너뜀(7장 다른 값의 근거 없음)은 본문을 고치지 않는다.
신규 문서: 2장 위치·파일명, 3장 description, 4장 모양으로 만든다. 도메인 루트 문서는 `## 적용 대상`을 사실 행의 레포·모듈로 반드시 둔다.
코드값: set이 있는 사실은 4장 집합 표기대로 `## 코드값` 표에 사실이 뜻을 말한 원소만 담고, 표 위에 set_total이 0이면 `원본: \`{set}\` — 일부`, 아니면 `원본: \`{set}\` 전 {set_total}종`을 둔다. 기존 표에 원소를 더할 때는 기존 원본 줄의 `전 N종`을 `— 일부`로 낮추지 않되, 더한 원소로 N이 맞지 않으면 `— 일부`로 바꾼다.
금지: 이 문서 밖 파일 편집, 코드 저장소 조회, 사전 지식.
출력: {work}/applied/{doc_slug}.json에 Write —
{"doc": "{doc}", "created",
 "verdicts": [{"id", "verdict": "동일|추가|교체|건너뜀", "summary": "추가·교체면 `{절}`에 반영한 내용 한 구", "old": "교체·건너뜀이면 기존 값"}]}
응답은 판정별 건수만.
```

`{doc_slug}`는 `doc`의 `/`를 `__`로, `.md`를 뺀 이름입니다.

## 6. 검토

`docs`의 문서마다 Agent 1회를 한 메시지에 병렬 실행합니다. 모델은 메인을 상속하고 에이전트는 커밋하지 않습니다. 검토가 이 스킬의 유일한 품질 게이트이므로 형식 검사 스크립트로 대신하지 않습니다. `{근거}`는 그 문서 사실 행의 `slug`마다 `repos[slug].path`와 `shas` 중 `order`에서 가장 늦은 머지입니다.

```
방금 사실을 반영한 위키 문서 한 장을 끝까지 읽고 규약 위반을 고쳐라.
입력: 문서 {tmp}/knowledge/{domain}/{doc}, 이번 반영 사실 {id·fact 목록}, 이번 변경 `git -C {tmp} diff -- knowledge/{domain}/{doc}`(신규 문서는 파일 전체), 근거 레포·머지 {근거}, 다른 문서 목록 `grep -H '^description:' {tmp}/knowledge/{domain}/*.md {tmp}/knowledge/{domain}/*/*.md`.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장을 의미와 형식 모두 판정한다.
- 의미: 1장 판정(코드 전사·변경 서사·일반 지식·레포 안 사실), 5장 문장, 6장 겹침
- 형식: 2장 위치·파일명, 3장 description, 4장 절 이름·순서와 `## 코드값` 표마다 `원본:` 줄, `전 N종`이면 표 행 수가 N
코드 확인: 1장 판정, 식별자 확인, `전 N종` 원본 줄의 원소 수 대조는 `git -C {repo_path} grep {패턴} {sha}`·`git -C {repo_path} show {sha}:{경로}`로 머지 시점 레포를 읽는다. `— 일부` 표는 원소를 채우지 않는다.
범위: 이번 변경 줄, description, 이번에 손댄 코드값 표 — 그 밖의 기존 줄은 고치지 않는다.
금지: 새 사실 추가, 이 문서 밖 편집. 예외로 `전 N종` 표의 원소가 원본 정의와 다르면 원본에 맞추고, 도메인 루트 문서에 없는 `## 적용 대상`은 문서에 이미 있는 사실의 레포·모듈로만 채운다.
위치: 2장 위치에 맞지 않는 불릿은 삭제하고 reason을 `위치 — {올바른 위치}`로 적는다.
고칠 수 없는 문서(한 주제가 서지 않음, 남길 불릿이 없음 등)는 reject를 true로 두고 사유를 적는다.
출력: {work}/review/{doc_slug}.json에 Write —
{"doc": "{doc}", "removed": [{"bullet", "reason", "ids": ["그 불릿이 담던 사실 id"]}],
 "fixed_sets": [{"set", "before": "고치기 전 원본 줄과 행 수", "after": "고친 뒤"}],
 "edited": [{"bullet": "고친 뒤 불릿 또는 절", "reason": "고친 규약 조항과 이유 한 구"}],
 "reject": false, "reject_reason": ""}
응답은 삭제·맞춤·수정 건수와 reject 여부만.
```

## 7. 커밋·커서

`reject`가 true인 문서와 검토로 본문이 빈 신규 문서는 원복하고(`git -C {tmp} checkout -- {경로}`, 신규는 삭제) 그 사실을 `검토 기각`으로 넘깁니다.

`--dry-run`이면 `git -C {tmp} diff`, 신규 문서 경로, 판정 집계를 보고하고 커밋 없이 `{tmp}`·`{work}` 경로를 남긴 채 종료합니다.

그 밖에는 문서마다 규약 8장대로 커밋합니다. 근거 줄은 그 문서 사실의 `{slug}@{sha7}`이고, 교체 판정이 있으면 `기존 {old} / 새 {값}` 줄을 둡니다.

```
git -C {tmp} add knowledge/{domain}/{doc}
git -C {tmp} commit -m "docs({domain}): {doc} {요약}" -m "{근거}"
```

이어서 `repos`의 레포마다 커서 sha를 정해 `{tmp}/state/{slug}.json`에 `{"cursor": "{전체 sha}", "at": "YYYY-MM-DD"}`를 Write하고 커밋합니다.

- **기본**: `commits`의 마지막 머지 — 사실 0건 머지도 전진함
- **원복 있음**: 원복한 문서 사실의 그 레포 `shas` 중 `commits`에서 가장 앞선 머지의 직전 머지, 그것이 첫 머지면 `cursor`
- **부트스트랩**: `bootstrapped`이고 `commits`가 비면 `cursor`(시작 지점)
- **불변**: 부트스트랩이 아니고 `commits`가 비면 쓰지 않음

```
git -C {tmp} add state/{slug}.json
git -C {tmp} commit -m "chore(update): {slug} 커서 {sha7} · 머지 N건"
```

## 8. 게시·보고

`${CLAUDE_PLUGIN_ROOT}/templates/update-pr.md`대로 `{work}/pr.md`를 씁니다. `{tmp}`에 새 커밋이 없으면 게시하지 않고 집계만 보고합니다. 있으면 `publish.md` 2장으로 push·PR을 만들고, PR 링크, 요약 집계 한 줄, "머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`로 지웁니다. 어느 단계든 실패하면 지우지 않고 `{tmp}`·`{work}` 경로와 원인을 보고합니다.
