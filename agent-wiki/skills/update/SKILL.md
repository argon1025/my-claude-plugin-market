---
name: update
description: Reflect merged code of one domain's registered repos into the wiki in time-ordered batches and open a wiki PR carrying the docs and cursors.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`remote`·`baseBranch`)과 `workspace.root`를 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`(이하 규약), 배정 이후 공통 절차는 `${CLAUDE_PLUGIN_ROOT}/references/apply.md`, 위키 원격 호스트 절차는 `${CLAUDE_PLUGIN_ROOT}/references/publish.md`이며, 서브에이전트에게는 규약·스크립트 경로를 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. `registry.json`·`deps.json`은 규약 9장 편집 주체 범위만 고칩니다.

인자: `--domain {domain}`(대상 도메인), `--max-merges N`(머지 예산, 기본 20), `--dry-run`(PR 본문 `{work}/pr.md`까지 쓰고 커밋·push·PR 없음).

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

## 3. 추출

레포별 `batches`마다(다시 나누지 않음) Agent 1회를 `model: sonnet`으로 한 메시지에 최대 15개씩 병렬 실행하고, 출력 파일이 없는 묶음은 4절 전에 다시 실행합니다. `{diff 목록}`은 그 묶음 `diffs`, `{지도}`는 그 레포 registry 노드의 `responsibilities`·`hosts`, `deps.{domain}/{slug}` 블록, 도메인 등록 레포 `{domain}/{slug}` 목록의 JSON입니다.

```
머지 묶음 1개에서 위키에 남길 사실을 추출하라.
입력: {diff 목록}을 목록 순서대로 한 파일씩 끝까지 Read(길면 offset으로 나눔) — 머지마다 첫 파일 머리말에 PR 제목·커밋 메시지·변경 파일 목록이 있고, {sha7}.{k}.diff는 같은 머지의 이어지는 조각이다.
대상: 변경 줄, 커밋 메시지, diff 속 작업 기록(plan·feedback)이 직접 말하는 사실만 — 바뀌지 않은 문맥에서 추론한 사실(부재 주장 등)은 담지 않는다.
기준: `sed -n '/^## 1\./,/^## 3\./p' {doc_contract_path}` — 1장으로 담을 문장을 고르고 2장으로 scope를 정한다.
graph: 레포 소관·책임·서빙 호스트·레포 사이 의존을 바꾸는 diff는 사실 대신 graph에 담는다 — 기준 `sed -n '/^## 9\./,$p' {doc_contract_path}`, 현재 지도 {지도}. 현재 responsibilities가 덮지 않는 새 기능 단위(엔드포인트 묶음·메시지 구독·스케줄러)는 responsibilities add이고, 간선 to는 현재 지도의 등록 레포만 쓴다.
병합: 묶음 안 같은 주장은 하나로 합쳐 shas에 모두 적는다. 값이 다른 두 사실은 둘 다 남기되, 같은 머지의 커밋 메시지·작업 기록이 변경 줄과 다르면 변경 줄 값만 남긴다.
금지: 입력 목록 밖 파일 열기, 사전 지식으로 채우기.
출력: {work}/facts/{slug}/{batch_id}.json에 Write —
{"facts": [{"fact": "현재 상태 한 문장(업무 낱말 우선, 식별자 괄호 병기, 줄바꿈 금지) — deleted면 지워지기 전 상태",
            "topic": "2~4낱말 주제",
            "code": "저장소 상대 경로 또는 경로#심볼",
            "scope": "root(도메인 루트)|repo(레포 폴더) — 두 성격이면 사실을 둘로 나눔",
            "deleted": false,
            "set": "닫힌 집합 원소의 뜻을 말하면 정의 식별자(심볼·공통코드 그룹), 코드를 인용만 하면 빈 문자열",
            "set_total": 0,
            "shas": ["근거 머지 sha7"]}],
 "graph": [{"key": "responsibilities|hosts|deps", "op": "add|remove|replace",
            "value": "책임 문장, {\"env\", \"host\"}, {\"to\", \"desc\"} 중 하나", "old": "교체·삭제면 기존 값",
            "code": "저장소 상대 경로 또는 경로#심볼", "shas": ["근거 머지 sha7"]}]}
deleted는 diff가 그 동작·값·코드값을 지우면 true, set_total은 diff가 집합 정의 전체를 보이면 원소 수(원소마다 사실을 남김)이고 아니면 0이다. 사실·후보가 없으면 {"facts": [], "graph": []}. 응답은 사실·후보 건수만.
```

## 4. 정리

메인이 `{work}/facts/**/*.json`을 모두 읽어 정리합니다.

- **병합**: 묶음 사이 같은 주장은 하나로 합치고 `shas`는 합집합 — `deleted`가 다르면 합치지 않음
- **대체**: 같은 대상의 값이 다른 두 사실은 `order`에서 늦은 머지의 사실만 남기고 앞 사실(복합 사실이면 충돌하는 주장만)은 `rejected`에 `대체 — {남긴 사실 id}`로 넘김 — 뒤 머지 diff가 변경 근거라 7장 다른 값 판정 대상이 아님
- **번호**: `order`에서 가장 늦은 근거 머지 순으로 `F1`부터 `id`를 매김 — 문서별 사실 순서도 이 순서

`apply.md` 0장 형식으로 `{work}/facts.json`을 씁니다. `slug`는 묶음의 레포, `source`는 `shas`마다 `{slug}@{sha7}`, `check`는 `source`의 레포마다 `{"repo_path": repos[레포].path, "rev": 그 레포의 가장 늦은 근거 머지 sha}`, `quote`는 `source`를 쉼표로 이은 값, `input`은 빈 배열이고 나머지 키는 추출 값 그대로입니다. `graph`는 같은 방식으로 병합·대체하고 `G1`부터 번호를 매겨 `{work}/graph-candidates.json`에 씁니다. 2절 스크립트가 준비한 레포는 0장 레포 읽기에서 다시 준비하지 않습니다.

## 5. 반영

`apply.md` 1~5장을 실행합니다.

## 6. 커서

`repos`의 레포마다 커서 sha를 정합니다.

- **기본**: `commits`의 마지막 머지 — 사실 0건 머지도 전진함
- **원복 있음**: `검토 기각`으로 넘긴 사실의 그 레포 근거 머지(`source`) 중 `commits`에서 가장 앞선 머지의 직전 머지, 그것이 첫 머지면 `cursor`
- **부트스트랩**: `bootstrapped`이고 `commits`가 비면 `cursor`(시작 지점)
- **불변**: 부트스트랩이 아니고 `commits`가 비면 쓰지 않음

커서 뒤 머지에서 나온 지도 후보는 `graph-candidates.json`에서 뺍니다 — 다음 실행이 같은 머지에서 다시 추출합니다.

## 7. 지도·커밋

`apply.md` 6·7장을 실행합니다. `--dry-run`이 아니면 이어서 커서를 정한 레포마다 `{tmp}/state/{slug}.json`에 `{"cursor": "{전체 sha}", "at": "YYYY-MM-DD"}`를 Write하고 커밋합니다.

```
git -C {tmp} add state/{slug}.json
git -C {tmp} commit -m "chore(update): {slug} 커서 {sha7} · 머지 N건"
```

## 8. 게시·보고

`${CLAUDE_PLUGIN_ROOT}/templates/wiki-pr.md`대로 `{work}/pr.md`를 씁니다. `--dry-run`이면 `{work}/pr.md`·`{tmp}`·`{work}` 경로를 보고하고 지우지 않은 채 종료합니다. `{tmp}`에 새 커밋이 없으면 게시하지 않고 집계만 보고합니다. 있으면 `publish.md` 2장으로 push·PR을 만들고, PR 링크, 요약 집계 한 줄, "머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`로 지웁니다. 어느 단계든 실패하면 지우지 않고 `{tmp}`·`{work}` 경로와 원인을 보고합니다.
