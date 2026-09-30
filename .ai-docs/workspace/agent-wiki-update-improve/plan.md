# agent-wiki update 실행 예산 하향과 추출 단위 재설계

## 의도

- **왜**: 커서가 밀린 도메인에서 update 한 번이 기본 예산 40건 안의 머지를 모두 처리해, 머지 27건 실행(위키 PR #3)이 사실 313건·문서 42장·에이전트 105회·PR 본문 한도 초과로 이어졌고, 추출 에이전트 묶음 7개 중 3개가 diff를 끝까지 읽지 못함
- **누가**: 적체된 도메인에 `/agent-wiki:update`를 실행하는 위키 운영자와 그 PR을 검토하는 사람
- **완료**: 인자 없이 실행한 update가 시각 순 앞 머지 10건까지만 처리하고 나머지는 `예산 밖 이월 N건`으로 보고하며, 추출 에이전트 1회 입력이 머지 1건(150KB 초과 머지는 파일 경계 조각 1개)이고, 모범 답안 대조 테스트로 누락 여부를 확인한 상태 — 같은 주제 이어 붙이기는 두지 않음

## 배경

- **PR #3 규모**: 머지 1건당 사실 11.6건·문서 1.6장·에이전트 3.9회·PR 본문과 코멘트 약 5,600자 — 10건이면 약 56,000자로 GitHub 한도 65,536자 안
- **같은 주제 확장 기각 근거**: 대체 34쌍의 전역 시각 순 거리 3~12로 인접 쌍 0건, 캔들 집계 주제(70f1e21·758b01e·f8fc090·935bc6c·6b9cca8)의 작업 기록 폴더·이슈 번호가 모두 달라 기계 판정 불가
- **Read 도구 상한**: 1회 25,000토큰, 범위 없는 Read는 256KB 파일까지(실측 — package-lock 2,000줄 63KB가 34,014토큰으로 거부)
- **미열람 관측**: 추출 묶음 25.1만~46.2만 바이트 3개가 diff 일부를 읽지 않고 완료 보고, 2,000줄 넘는 파일이 없던 dashboard b02(25.1만 바이트)도 포함, 9.1만 바이트 묶음은 끝까지 읽음 — 에이전트 1회 누적 입력량이 원인
- **제외 규칙 버그**: `:(exclude)**/package-lock.json`은 glob 매직이 없어 루트 `package-lock.json`을 빼지 못함 — `:(exclude,glob)`로 바꾸면 PR #3 전체 diff가 2,472KB에서 1,952KB(−21%), 0365460은 267KB에서 19KB
- **분할 영향**: 제외 규칙 수정 후 150KB 초과 머지는 27건 중 3건(dcb6779 187KB, 552cdd8 154KB, f8fc090 196KB)이고 각 2조각, 27건 전체 조각 30개
- **메인 역할**: 현행 추출에서도 메인은 diff 파일 경로·지도 JSON만 넘기고 diff를 읽지 않음, diff 추출은 스크립트가 재현성(제외 규칙·머지 범위 `sha^1...sha`·딸린 커밋 메시지)을 위해 맡음

## 확정 결정 (사용자 확인 2026-09-30)

- **실행 예산**: 단위는 머지 건수로 유지하고 `--max-merges` 기본값을 40에서 10으로 낮춤
- **같은 주제 확장**: 예산 경계 뒤 같은 주제 머지를 이어 붙이는 확장은 두지 않음
- **추출 단위**: 추출 에이전트 1회 = 머지 1건, 150KB를 넘는 머지는 스크립트가 파일 경계로 150KB 이하 조각으로 나눠 조각마다 1회이며 조각마다 커밋 메시지 머리말을 둠
- **삭제**: 묶음 로직(`BATCH_MERGES`·`BATCH_BYTES`·`batches()`)과 미검증 "묶음 1개·머지 3건 이하면 메인 직접 추출" 예외
- **이어 읽기**: 추출 응답에 끝까지 읽지 못한 파일을 적게 하고, 있으면 같은 에이전트에 이어 읽기를 요청함
- **테스트**: "권장안으로 일단 가보되 사실 추출 테스트 진행, 모범 답안 준비하고 서브에이전트로 돌려봐 누락 되는지.. 그리고 더 간단한 구조가 있을지 등도 열어놓고 검토 그래서 현 방식말고 에이전트 지침으로 테스트한번 해보는것도 좋을거같음" — 권장안(스크립트 조각)과 에이전트 지침안(레포·sha만 넘기고 에이전트가 git으로 파일별 읽기)을 모범 답안에 대조함

## 선행 읽기

- `.ai-docs/workspace/agent-wiki-update-improve/feedback.md` — 앞쪽 9축 결정(재배정 루프·원복 커서 삭제 등)은 이 계획 범위 밖이며, 끝 항목들이 이 계획의 근거 수치임
- `agent-wiki/skills/update/SKILL.md` 2~4절 — 고칠 대상이며 `work.json` 필드와 추출 프롬프트가 스크립트 출력과 맞물림

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/collect_update_merges.py` | 제외 규칙 glob 매직, 머지 diff 조각 분할, 묶음 로직 삭제, `--max-merges` 기본 10 | 기존 파일 수정 — 조각 분할은 ⑦: 파일 경계로 diff를 자르는 기존 함수가 없고 `batches()`를 대체함, 제외 규칙은 ⑥ |
| `agent-wiki/skills/update/SKILL.md` | description, 인자 기본값, 2절 `work.json` 설명, 3절 조각 단위 실행·이어 읽기·프롬프트, 4절 묶음 낱말 | 기존 파일 수정 |
| `agent-wiki/README.md` | 스킬 표 update 행의 "시간 순 묶음으로"를 "시간 순으로" | 기존 파일 수정 |
| `agent-wiki/templates/wiki-pr.md` | `레포` 표 예시의 shop-worker `40건`을 `10건` | 기존 파일 수정 |
| `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | agent-wiki 0.7.0, 마켓플레이스 `metadata.version` 4.1.0 | 기존 파일 수정 — 플러그인 버전을 올리는 PR마다 마켓플레이스 버전도 올리는 관례 |
| 테스트 하네스 | `mktemp -d` 폴더의 임시 파일과 명령만 쓰고 커밋하지 않음 | ① |

### collect_update_merges.py

- **머리 주석 2행**: "diff를 파일로 꺼내 묶음으로 자른다"를 "diff를 파일로 꺼내며 큰 머지는 파일 경계 조각으로 나눈다"로 고침
- **제외 규칙**: `EXCLUDE_PATHSPECS` 11개를 모두 `:(exclude,glob)`로 바꿈 — 패턴 목록은 유지
- **상수**: `BATCH_MERGES`·`BATCH_BYTES`와 그 주석을 지우고 `PART_BYTES = 150_000`을 둠, 주석은 "추출 에이전트 1회가 끝까지 읽는 조각 상한 — 25만 바이트 입력부터 미열람이 관측됨" 한 줄
- **조각 분할**: `batches()`를 지우고 `split_parts(body)`를 둠 — `re.split(r"(?m)^(?=diff --git )", body)`로 파일 단위로 나눠 앞에서부터 담다가 다음 파일을 더하면 `PART_BYTES`(UTF-8 바이트)를 넘을 때 새 조각을 시작함, 파일 하나가 상한을 넘으면 그 파일만으로 조각 하나, 본문이 비면 빈 조각 하나 — `re` import 추가
- **파일 쓰기**: `extract_diff`는 400KB 절단 뒤 본문을 조각으로 나눠 조각이 1개면 `{sha7}.diff`, 여럿이면 `{sha7}-{i}.diff`로 씀, 머리말은 현행과 같되 첫 줄 다음에 `# 조각 {i}/{n} · {전체 줄 수}줄`을 넣고 줄 수는 머리말을 포함한 그 파일 전체 줄 수
- **행 필드**: `row["diff_path"]`·`row["bytes"]`를 지우고 `row["parts"] = [{"id": 파일 이름에서 .diff를 뺀 값, "path", "bytes"}]`
- **work.json**: `repos[slug]`에서 `batches`를 지움, 요약 출력은 `{slug}: 머지 N건 · 조각 M개{이월}{부트스트랩}`
- **인자**: `--max-merges` 기본값 10

### SKILL.md

- **description**: "in time-ordered batches"를 "in time order"로 고침
- **인자 줄**: `--max-merges N`(머지 예산, 기본 10)
- **2절 work.json**: `repos[slug]{path, branch, head, cursor, bootstrapped, commits[{sha, date, subject, parts[{id, path, bytes}]}], remaining}`로 고치고 "묶음은 다시 나누지 않으며"를 지움 — `parts`는 머지 diff를 파일 경계에서 150KB 이하로 나눈 조각이라는 한 구를 둠
- **3절 실행 문단**: "레포별 `commits[].parts`의 조각마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행합니다. 출력 파일이 없는 조각은 4절 전에 다시 실행하고, 응답에 끝까지 읽지 못한 파일이 있으면 같은 에이전트에 SendMessage로 이어 읽어 출력 파일을 보강하도록 요청합니다." 뒤에 기존 `{지도}` 설명 문장을 유지하고 `{diff 목록}` 설명은 지움
- **3절 프롬프트**: 아래 네 줄만 바꾸고 작업 기록·기준·graph·금지·set·set_total 줄과 출력 스키마는 유지함

```
머지 diff 조각 1개에서 위키에 남길 사실을 추출하라.
입력: {diff 경로}를 offset·limit으로 나눠 머리말의 줄 수까지 Read — 머리말에 커밋 메시지·변경 파일 목록·절단 여부·조각 번호가 있다.
병합: 같은 주장은 하나로 합친다. 값이 다른 두 사실은 둘 다 남긴다.
출력: {work}/facts/{slug}/{part_id}.json에 Write —
```

- **3절 응답 줄**: "사실·후보가 없으면 {"facts": [], "graph": []}. 응답은 사실·후보 건수와 끝까지 읽지 못한 파일(없으면 `없음`)만."
- **4절**: 병합 불릿의 "묶음 사이"를 "조각 사이"로, facts.json 문단의 "`slug`는 묶음의 레포"를 "`slug`는 조각의 레포"로 고침

### 테스트 설계

- **대상**: pigeon-trade-dashboard b3f89a2·9254ffe·bf4ddb5·f9ee70a·fddf462(PR #3에서 미열람된 묶음 b02, 25.1만 바이트)와 pigeon-trade f8fc090(196KB, 2조각)
- **가짜 위키**: `t=$(mktemp -d)`에 `wiki-d`·`wiki-p` 두 폴더를 만들고, 각 `registry.json`은 `{"domains": {"personal-stock-trading": {"repos": {slug: {"remote", "defaultBranch": "develop"}}}}}`로 레포 하나만 둠 — remote는 `https://github.com/argon1025/pigeon-trade-dashboard.git`·`https://github.com/argon1025/pigeon-trade.git`, 커서 `state/{slug}.json`은 dashboard `289648741e372d4437da552ff3845e8027c4208f`(2896487), pigeon-trade `ee8e90bb3cf813bbcc4dcc9d9cee6208ef30865f`(ee8e90b)
- **입력 생성**: 새 스크립트로 `--wiki $t/wiki-d --max-merges 5 --out $t/S-d`, `--wiki $t/wiki-p --max-merges 1 --out $t/S-p`, 기준선은 `git show main:agent-wiki/scripts/collect_update_merges.py > $t/old.py`로 `--wiki $t/wiki-d --max-merges 5 --out $t/C-d` — 공통 인자 `--workspace ~/.agent-wiki-workspace --domain personal-stock-trading`
- **모범 답안**: 머지마다 Agent 1회(모델 상속)를 아래 프롬프트로 실행하고, 메인이 답안의 `file` 집합과 그 머지 조각들의 `diff --git` 줄 b/ 경로 집합이 같은지 확인해 다르면 빠진 파일만 다시 요청함

```
머지 1건의 diff에서 위키에 남길 사실의 모범 답안을 만들라.
입력: {조각 diff 경로 목록}을 파일마다 offset·limit으로 나눠 머리말의 줄 수까지 Read.
기준: `sed -n '/^## 1\./,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 작업 기록(plan·feedback) 추가 줄도 코드 diff와 같이 후보로 본다.
출력: {t}/gold/{sha7}.json에 Write — {"files": [{"file": "diff --git 줄의 b/ 경로", "facts": ["현재 상태 한 문장"]}]} — diff 본문의 모든 파일을 빠짐없이 적고 사실이 없는 파일은 빈 목록.
응답은 파일 수와 사실 수만.
```

- **C 기준선**: `$t/C-d` 묶음 1개를 `main`의 SKILL.md 3절 프롬프트로 1회 실행, 출력은 `$t/C1/`
- **S 권장안**: `$t/S-d`·`$t/S-p` 조각 7개를 새 SKILL.md 3절 프롬프트로 2회 실행, 출력은 `$t/S1/`·`$t/S2/`, 미열람 응답은 이어 읽기까지 수행
- **I 지침안**: 머지 6건을 아래 입력 줄로 바꾼 새 3절 프롬프트로 2회 실행 — 나머지 줄은 같고 출력은 `$t/I{회차}/{sha7}.json`

```
입력: 레포 {repo_path}의 머지 {sha}. 커밋 메시지는 `git -C {repo_path} log --max-count=20 --format='%h %s%n%b' {sha}^1..{sha}`, 변경 파일은 `git -C {repo_path} diff --name-status {sha}^1 {sha}`로 본다. 잠금 파일(package-lock.json·yarn.lock·pnpm-lock.yaml·poetry.lock·composer.lock·gradle.lockfile)·*.min.js·*.min.css·*.svg·dist/·node_modules/ 아래 파일은 건너뛰고, 나머지 파일마다 `git -C {repo_path} diff {sha}^1 {sha} -- {파일}`을 끝까지 읽는다.
```

- **채점**: 메인이 머지마다 모범 답안 사실과 각 실행의 사실을 의미로 대조해 `$t/score.md`에 실행·회차·머지별 `답안 사실 수 · 일치 수 · 재현율 · 누락 파일`을 씀 — 누락 파일은 답안 사실이 1건 이상인 파일 중 그 파일의 답안 사실을 하나도 잡지 못한 파일
- **판정**: S는 두 회차 모두 누락 파일 0건이면 통과, C는 기준선으로 누락 파일 수만 기록, I가 두 회차 모두 누락 파일 0건이고 재현율이 S 평균 − 5%p 이상이면 더 간단한 구조 후보로 보고 재계획 정지
- **규모**: 에이전트 33회(모범 답안 6, C 1, S 14, I 12)

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `collect_update_merges.py`·`SKILL.md`·`README.md`·`wiki-pr.md` — 예산·제외 규칙·조각 분할·묶음 삭제 | ① `t=$(mktemp -d)`에 dashboard 커서 `7370732e3239f54c55d767047ea88115bca6e5fc`, pigeon-trade 커서 `4c2a4d46181e9f817c48972975c585c9a8958dca`를 둔 두 레포 가짜 위키로 인자 없이 실행 — 종료 코드 0, 출력 `pigeon-trade: 머지 8건 · 조각 9개 · 예산 밖 11건`과 `pigeon-trade-dashboard: 머지 2건 · 조각 2개 · 예산 밖 6건` ② 같은 위키로 `--max-merges 40` — 머지 19건·8건, 조각 합계 30개 ③ 파이썬 검사로 머지마다 조각 본문(`# --- diff (제외 규칙 적용) ---` 줄 뒤)을 이어 붙인 값이 `:(exclude,glob)` 규칙의 `git show --format=`(부모 1개) 또는 `git diff {sha}^1...{sha}`(부모 2개) 출력의 400,000바이트 절단과 같고, 파일 2개 이상 조각은 본문 150,000바이트 이하, 머리말 줄 수가 `wc -l`과 같음 ④ `grep -rn -e '묶음' -e 'batch' agent-wiki/skills/update agent-wiki/scripts/collect_update_merges.py agent-wiki/README.md` 결과 없음 |
| 2 | `.ai-docs/workspace/agent-wiki-update-improve/feedback.md` — 테스트 결과 | 테스트 설계대로 실행해 `$t/score.md` 생성, 모범 답안 파일 집합 일치 6/6, S 두 회차 누락 파일 0건, C·S·I 재현율과 누락 파일 수를 `why`·`constraint` 항목으로 기록 — S 불통과 또는 I가 판정 조건 충족이면 이 커밋 뒤 정지하고 재계획 |
| 3 | `plugin.json` 0.7.0, `marketplace.json` `metadata.version` 4.1.0 | `python3 -c "import json;print(json.load(open('agent-wiki/.claude-plugin/plugin.json'))['version'], json.load(open('.claude-plugin/marketplace.json'))['metadata']['version'])"` 출력 `0.7.0 4.1.0` |

## 특이 사항

- **범위 밖**: feedback.md 앞쪽 9축 결정(검토 check 시점, 재배정 루프·원복 커서 삭제, PR 본문 축소 등)과 apply.md 반영·검토 단계는 이 계획에서 고치지 않음
- **경계 비용**: 예산 10이면 PR #3 이력의 대체 34쌍 중 25쌍이 실행 경계를 넘어 4절 대체 대신 규약 7장 다른 값 판정(변경 의도 근거 필요)을 거치고, 밀린 27건은 실행·PR 머지 3회로 나뉨
- **의도적 단순화**: 파일 하나가 150KB를 넘으면 그 파일만으로 조각 하나라 끝까지 읽기는 이어 읽기에 기대며, 이런 파일이 반복되면 제외 규칙 보강이나 파일 안 hunk 분할을 검토함
- **조각 문맥**: 작업 기록 폴더(`.ai-docs/` 등 점으로 시작하는 경로)는 diff 앞쪽에 와 첫 조각에 담기므로 둘째 조각부터는 커밋 메시지 머리말만으로 이유를 봄
- **후속 판단**: I 지침안이 판정 조건을 충족하면 스크립트의 diff 추출을 지우는 구조 변경을 사용자 결정으로 재계획함

## 추가 계획 2026-09-30 — 테스트를 간결한 대안 접근법 비교로 확장

- 폐기: `### 테스트 설계` 전체, `## 커밋 분해` 2행, `## 특이 사항`의 `후속 판단` 불릿 — 대안이 에이전트 지침안 하나뿐이라 여러 간결한 접근법을 고안해 비교한다는 테스트 의도를 담지 못하며, 이 절의 `### 작업`·`### 커밋 분해`·`### 특이 사항`이 대체함

### 의도

- **왜**: 권장안을 구현한 뒤에도 더 간결한 추출 구조가 누락 없이 같은 사실을 뽑을 수 있으므로, 권장안 하나의 누락 확인이 아니라 간결한 대안 여러 개를 같은 모범 답안으로 비교해 구조를 골라야 함
- **누가**: `/agent-wiki:update`를 운영·개선하는 위키 운영자
- **완료**: 권장안 S와 대안 M·I·W의 점수표(누락 파일·재현율·비용·구조 크기)와 선정 결과가 feedback.md에 남고, 선정안이 S가 아니면 재계획으로 넘어간 상태

### 확정 결정 (사용자 확인 2026-09-30)

- **테스트 의도**: "테스트는 수정 후 현 방안과 또다른 간결한 접근법들을 고안해보고 비교해보라는것이였음 새로 나온 프로세스가 더 좋을 수 있으니.."
- **비교 대상**: S 권장안, M 무분할, I 에이전트 지침, W 작업 기록 중심 — 프로세스 수준 대안(머지 순차 직접 반영)은 넣지 않음
- **비교 축**: 누락 파일, 재현율, 비용(토큰·소요 시간), 구조 크기(스크립트·프롬프트 줄 수), 안마다 2회 실행

### 작업

| 대상 | 내용 | 사다리 |
|---|---|---|
| 테스트 하네스 | `mktemp -d` 폴더의 가짜 위키·스크립트 사본·에이전트 출력·점수표, 커밋하지 않음 | ① |
| `.ai-docs/workspace/agent-wiki-update-improve/feedback.md` | 점수표 요약과 선정 근거 | 기존 파일 덧붙이기 |

#### 비교 대상

| 안 | 추출 입력 | 에이전트 단위 | 구조 차이 |
|---|---|---|---|
| S 권장안 | 새 스크립트의 조각 diff 파일 | 조각 1개 | 커밋 1 그대로 |
| M 무분할 | `PART_BYTES`만 `10**9`로 바꾼 스크립트 사본의 머지 diff 파일 | 머지 1건 | S에서 `split_parts()` 삭제 |
| I 에이전트 지침 | 레포 경로와 머지 sha | 머지 1건 | 스크립트에서 diff 추출·분할·제외 규칙 삭제, 입력 줄이 git 읽기 지시 |
| W 작업 기록 중심 | 레포 경로와 머지 sha | 머지 1건 | I와 같고 입력 줄이 코드 파일 선별 지시 |
| C 기준선 | `main` 스크립트의 묶음 diff 파일 | 묶음 1개 | 비교 기준, 1회만 |

#### 대상 머지와 입력

- **대상**: pigeon-trade-dashboard b3f89a2·9254ffe·bf4ddb5·f9ee70a·fddf462(PR #3 미열람 묶음 b02), pigeon-trade dcb6779(187KB)·f8fc090(196KB) — 7건
- **가짜 위키**: `t=$(mktemp -d)`에 레포 하나만 둔 위키 세 개를 만듦 — `registry.json`은 `{"domains": {"personal-stock-trading": {"repos": {slug: {"remote", "defaultBranch": "develop"}}}}}`, remote는 `https://github.com/argon1025/{slug}.git`
  - `wiki-d`: pigeon-trade-dashboard, 커서 `289648741e372d4437da552ff3845e8027c4208f`, `--max-merges 5`
  - `wiki-p1`: pigeon-trade, 커서 `1f40f1947b206c1722b9fb89f9587cbc3abfe365`, `--max-merges 1`(dcb6779)
  - `wiki-p2`: pigeon-trade, 커서 `ee8e90bb3cf813bbcc4dcc9d9cee6208ef30865f`, `--max-merges 1`(f8fc090)
- **입력 생성**: 공통 인자 `--workspace ~/.agent-wiki-workspace --domain personal-stock-trading`
  - S: 새 스크립트로 세 위키를 `$t/S-d`·`$t/S-p1`·`$t/S-p2`에 — 조각 9개(dashboard 5, dcb6779 2, f8fc090 2)
  - M: `sed 's/^PART_BYTES = 150_000$/PART_BYTES = 10**9/'` 사본으로 `wiki-p1`·`wiki-p2`만 `$t/M-p1`·`$t/M-p2`에 — dashboard 5건은 150KB 이하라 S 입력과 같아 S 실행 결과를 M 점수에 그대로 씀
  - C: `git show main:agent-wiki/scripts/collect_update_merges.py` 사본으로 `wiki-d`만 `$t/C-d`에 — 묶음 1개

#### 프롬프트

- **S·M·C**: S·M은 새 SKILL.md 3절 프롬프트, C는 `main`의 SKILL.md 3절 프롬프트 — 출력 경로만 `$t/{안}{회차}/`
- **I 입력 줄**: 새 3절 프롬프트에서 입력 줄만 아래로 바꾸고 출력은 `$t/I{회차}/{sha7}.json`

```
입력: 레포 {repo_path}의 머지 {sha}. 커밋 메시지는 `git -C {repo_path} log --max-count=20 --format='%h %s%n%b' {sha}^1..{sha}`, 변경 파일은 `git -C {repo_path} diff --name-status {sha}^1 {sha}`로 본다. 잠금 파일(package-lock.json·yarn.lock·pnpm-lock.yaml·poetry.lock·composer.lock·gradle.lockfile)·*.min.js·*.min.css·*.svg·dist/·node_modules/ 아래 파일은 건너뛰고, 나머지 파일마다 `git -C {repo_path} diff {sha}^1 {sha} -- {파일}`을 끝까지 읽는다.
```

- **W 입력 줄**: 새 3절 프롬프트에서 입력 줄을 아래로 바꾸고 응답 줄 끝에 "읽지 않은 코드 파일 수"를 더함, 출력은 `$t/W{회차}/{sha7}.json`

```
입력: 레포 {repo_path}의 머지 {sha}. 커밋 메시지는 `git -C {repo_path} log --max-count=20 --format='%h %s%n%b' {sha}^1..{sha}`, 변경 파일은 `git -C {repo_path} diff --stat {sha}^1 {sha}`로 본다. 작업 기록·문서 파일(plan·feedback·README 등 .md)은 끝까지 읽고, 코드 파일은 레포 밖에서 보이는 값(API 요청·응답, DB 스키마, 메시지, 코드값 정의, 설정·환경 값)을 바꾸거나 작업 기록이 이유·함정을 말한 파일만 `git -C {repo_path} diff {sha}^1 {sha} -- {파일}`로 끝까지 읽는다. 잠금 파일·*.min.js·*.min.css·*.svg·dist/·node_modules/ 아래 파일은 건너뛴다.
```

- **모범 답안**: 머지마다 Agent 1회(모델 상속)를 S 조각 파일을 입력으로 아래 프롬프트로 실행하고, 메인이 답안 `file` 집합과 조각들의 `diff --git` 줄 b/ 경로 집합이 같은지 확인해 다르면 빠진 파일만 다시 요청함

```
머지 1건의 diff에서 위키에 남길 사실의 모범 답안을 만들라.
입력: {조각 diff 경로 목록}을 파일마다 offset·limit으로 나눠 머리말의 줄 수까지 Read.
기준: `sed -n '/^## 1\./,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 작업 기록(plan·feedback) 추가 줄도 코드 diff와 같이 후보로 본다.
출력: {t}/gold/{sha7}.json에 Write — {"files": [{"file": "diff --git 줄의 b/ 경로", "facts": ["현재 상태 한 문장"]}]} — diff 본문의 모든 파일을 빠짐없이 적고 사실이 없는 파일은 빈 목록.
응답은 파일 수와 사실 수만.
```

- **채점**: 머지마다 Agent 1회(모델 상속)가 그 머지의 모범 답안과 모든 안·회차의 사실(S는 조각 출력 합집합, C는 `shas`로 나눈 행)을 함께 대조함 — 한 에이전트가 같은 머지의 모든 안을 판정해 기준을 맞춤

```
머지 1건의 모범 답안과 추출 결과 여러 벌을 대조해 채점하라.
입력: 모범 답안 {t}/gold/{sha7}.json, 추출 결과 {안·회차별 사실 파일 목록}.
판정: 답안 사실마다 각 결과에 같은 주장(표현이 달라도 같은 값·조건·결과)이 있으면 일치로 본다. 답안에 없는 결과 사실은 답안 밖으로 센다.
출력: {t}/score/{sha7}.json에 Write — {"{안}{회차}": {"gold": 답안 사실 수, "hit": 일치 수, "missed_files": ["답안 사실이 있으나 하나도 잡지 못한 파일"], "extra": 답안 밖 사실 수}}
응답은 안·회차별 hit/gold만.
```

- **비용**: 안·회차마다 Agent 결과에 표시되는 토큰·소요 시간 합계와 이어 읽기 횟수를 메인이 기록함
- **구조 크기**: S는 커밋 1 이후 스크립트 `wc -l`, M은 거기서 `split_parts()` 줄 수를 뺀 값, I·W는 `extract_diff()`·`split_parts()`·`EXCLUDE_PATHSPECS`·`DIFF_MAX_BYTES`·`PART_BYTES`·`MESSAGE_MAX_COMMITS` 줄을 뺀 값이며, 각 안의 3절 입력 줄 글자 수를 병기함

#### 선정

- **자격**: 두 회차 모두 누락 파일 0건인 안 — C는 기준선이라 제외
- **후보**: 자격 안 가운데 평균 재현율이 최고 평균 재현율 − 5%p 이상인 안
- **선정**: 후보 가운데 구조 크기가 가장 작은 안, 같으면 평균 토큰이 적은 안
- **결과 처리**: S가 선정되면 커밋 3으로 진행하고, M·I·W가 선정되거나 자격 안이 없으면 커밋 2 뒤 정지하고 점수표를 근거로 재계획함

### 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 2 | `feedback.md` — 비교 결과 | `$t/score/` 7개 파일과 `$t/score.md`(안·회차별 재현율, 누락 파일 수, 답안 밖 사실 수, 토큰, 소요 시간, 구조 크기를 한 표로) 생성, 모범 답안 파일 집합 일치 7/7, 선정 규칙 적용 결과를 `why` 항목으로, 안별 관측(미열람, 선별 누락 등)을 `constraint` 항목으로 기록 |

### 특이 사항

- **규모**: 에이전트 약 65회 — 모범 답안 7, C 1, S 18, M 4, I 14, W 14, 채점 7
- **모범 답안 한계**: 답안도 에이전트가 만들므로 답안 밖 사실 중 규약 1장에 맞는 것은 답안 누락일 수 있어, 선정은 재현율과 누락 파일로 하고 답안 밖 사실 수는 참고치로만 씀
- **W 판정**: W는 코드 파일을 건너뛰도록 설계되어 건너뛴 파일에 답안 사실이 있으면 누락 파일로 잡혀 자격을 잃음 — 이 결과가 "레포 안 코드는 선별해 읽어도 되는가"의 답임
- **범위 밖**: 프로세스 수준 대안(머지 순차 직접 반영)은 사용자 선택으로 비교하지 않음
