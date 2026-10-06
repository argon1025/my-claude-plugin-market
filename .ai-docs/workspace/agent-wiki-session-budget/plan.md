# agent-wiki 세션 주입 구성 벤치마크

## 의도

- **왜**: 도메인이 커지면서 agent-wiki 세션 주입이 훅 출력 한도 10,000자를 넘었고, 그 결과 문서 목록이 빠지거나 에이전트가 원문을 다시 읽어 토큰을 두 번 씀
- **누가**: 등록 레포에서 기획 검토·계획·구현·리뷰를 하는 에이전트가 세션 시작 직후 관련 문서와 영향 레포를 고를 때 겪음
- **완료**: 여러 주입안을 같은 과제로 실측해 문서·레포 재현율이 가장 높으면서 한도 안에 드는 안을 근거와 함께 제안하면 이번 계획은 끝나며, 구현은 채택 뒤 추가 계획으로 진행함

## 배경

- **한도 동작**: Claude Code는 훅의 `additionalContext`를 훅마다 따로 재서 10,000자를 넘으면 원문을 세션 폴더 파일로 저장하고, 컨텍스트에는 `<persisted-output>` 안내와 앞 2,000자 미리보기만 남기며 읽으라는 지시는 붙이지 않음
- **현행 크기**: 사내 위키의 대형 도메인(레포 16개, 도메인 공유 문서 92개) 레포에서 주입이 17~18K자이고, 중형 도메인 레포도 11K자로 한도를 넘음. 대형 도메인 원문의 구성은 책임 문장 62%, 문서 목록 33%임
- **실세션 기준선**: 사내 도메인 레포 세션 78건(도구 호출 5회 이상) 중 64건(82%)에서 위키 주입이 파일로 빠졌고, 그중 41건(64%)은 에이전트가 원문 파일을 다시 읽었음(중앙값 두 번째 도구 호출, 회당 8.4~9.5K 토큰). 배포 PR 세션 10건 중 3건도 다시 읽었음
- **공개 레포 제약**: 이 레포는 PUBLIC이므로 사내 위키 내용과 실행 기록은 커밋하지 않고 로컬 `~/.agent-wiki-bench/session-injection/`에만 둠

## 확정 결정 (사용자 확인 2026-10-06)

- **진행 순서**: 개선안을 바로 구현하지 않고, 수정 범위 파악·리뷰 시 의존성 파악 같은 실제 쓰임에서 잘 참조하는지 먼저 실측한 뒤 제안함
- **설계 방식**: 세션 주입의 구성 요소(지침, 레포 목록, 문서 목록)마다 수준을 바꿔 use case별 반응을 보고 요소별 최선을 조합함
- **진행 세션**: 새 세션으로 넘기지 않고 이 세션에서 하네스 구축부터 실측·선정까지 진행함
- **범위 제외**: 책임 원본 축약(register·update 규약)은 이번 범위에서 제외함
- **채택**: 요소별 최선 조합안을 채택하고, 구현은 추가 계획으로 진행함

## 비교 설계

기준 구성은 강화 지침, summary 레포 목록과 색인(책임·간선), 이름 인라인 문서 목록이며, 요소 하나만 바꿔 1회씩 실행함.

| 요소 | 수준 | use case 과제 |
|---|---|---|
| 문서 목록 | description 인라인 · 이름 인라인 · 색인 경로만 · 조회 스크립트 | 기획 검토, 레포 내부 암묵지, description 전용 낱말, 실세션 프롬프트 재현 |
| 레포 목록 | summary만(간선 없음) · summary+색인 간선 · 간선 인라인 | 리뷰 시 영향 레포 파악, 크로스 레포 메시지 변경 순서 |
| 지침 | 현행 문구 · 강화 문구("기획 검토·계획 수립·구현·리뷰 전 확인") | 실세션 프롬프트 재현, 무관 과제(배포 PR 본문) |
| 조합 확인 | 요소별 최선 조합 · 현행 | 위 과제 6종 |

- **실행**: `claude -p`(Opus 5.5, 읽기 전용 도구, 최대 30턴, 회당 5달러 상한)를 레포 사본에서 돌리고, 위키 계열 플러그인을 끈 채 비교 주입만 `--settings`의 SessionStart 훅으로 넣음
- **지표**: 정답 문서 본문 열람률, 정답 레포 코드 확인·언급률, Sonnet 5.5 블라인드 사실 채점, 오버헤드(주입 + 색인·스크립트·원문 파일 읽기 글자 수), 비용

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `~/.agent-wiki-bench/session-injection/*`(레포 밖) | 과제·정답표, 구성 생성기, 조회 스크립트 원형, 실행기, 분석기, 채점기 | ⑦ 측정 전용 코드이며 기존 스크립트에 구성 조합·측정 기능이 없음 |
| `.ai-docs/workspace/agent-wiki-session-budget/feedback.md` | 실측 결과와 채택 결정 기록 | ① 기록 |

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `plan.md`·`feedback.md` 기록 | `git show --stat HEAD`에 두 파일만 있고, 로컬 `tasks.json`의 레포명·문서명·API 경로·오류 코드로 `git show HEAD`를 grep한 결과가 없음 |

## 특이 사항

- **후속 구현**: 채택 조합안의 생성기·훅·색인 파일 생성, doc-contract·README 문구, 버전, 사내판 미러링, 위키 세션 훅 문서 갱신(`/agent-wiki:add`)은 `## 추가 계획`으로 진행함
- **측정 한계**: 칸당 1회 실행, 단일 대형 도메인, `claude -p` 단발 실행이라 대화형 세션과 탐색 깊이가 다를 수 있음
- **미실측**: 색인을 레포 책임과 문서 description 두 파일로 나누는 변형은 실측하지 않음

## 추가 계획 2026-10-06 — 채택 조합안 구현

### 의도

- **왜**: 채택한 조합안이 아직 코드에 없어, 대형 도메인 세션은 여전히 주입 17~18K자가 잘리고 에이전트가 원문을 다시 읽음
- **누가**: 등록 레포에서 세션을 여는 모든 에이전트(개인판·사내판)
- **완료**: 개인판 agent-wiki 0.9.0과 사내판 미러가 조합안 주입(사내 위키 전 레포 10,000자 미만)과 세션별 색인 파일을 만들고, 규약·README가 새 구성을 설명하면 끝

### 배경

- **생성기 구조**: 훅(`agent-wiki/hooks/session_start.py`)은 `scripts/generate_wiki_rules.py`·`generate_repository_map.py`·`generate_document_list.py`의 stdout을 순서대로 합쳐 주입함. 블록마다 생성기를 따로 두는 구조는 2026-09-29 사용자 결정임
- **사본 정리**: `sync_wiki.py`는 `git clean -fd`(무시 파일 보존)로 정리하고, 골격(`scripts/write_skeleton.sh`)이 `.local/`을 gitignore에 넣으므로 `.local/index/`는 세션 시작 정리에도 남음
- **벤치마크 기준 주입문**: 로컬 `~/.agent-wiki-bench/session-injection/preview-api.txt`(5,586자)가 이번 구현의 기대 출력이며, 문서 목록 제목 문구만 다름
- **버전 관례**: 기능 변경은 plugin.json minor를 올리고 marketplace.json `metadata.version`도 함께 올림. 사내판은 marketplace.json 최상위 `version`과 agent-wiki 항목 `version`을 올리고 master에 직접 커밋함

### 확정 결정 (사용자 확인 2026-10-06)

- **주입 구성**: 지침 현행 문구, `slug (표식) — summary` 레포 목록, 레포 전용 문서 `이름 — description`, 도메인 공유 문서 이름 한 줄, 다른 도메인 목록
- **색인 생성 시점**: 훅이 세션 시작(startup·resume·clear·compact)마다 로컬 위키 사본으로 생성함. 스킬 시점 생성·커밋안은 동시 PR의 생성 파일 충돌과 스킬 밖 편집에 따른 낡음 때문에 기각함
- **색인 위치·구성**: `{baseRoot}/.local/index/{domain}/{slug}.md` 한 파일에 레포별 책임 전체(의존 표식 포함)와 문서 전체 `이름 — description`을 담음
- **간선 desc**: 주입·색인 어디에도 넣지 않음
- **문서 목록 제목**: "(description은 색인)" 축약 대신 경로 줄 뒤에 "문서별 용도(description)는 색인 파일에 있음"을 풀어 씀
- **사내판 미러링**: 이번 계획에 포함하며, 사내 마켓플레이스 push는 실행 시점에 따로 확인받음

### 외부 계약

- **훅 출력**: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<text>"}}`이며, Claude Code는 `additionalContext`를 훅마다 10,000자까지만 그대로 싣고 넘으면 파일로 빼고 앞 2,000자만 남김

### 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/generate_repository_map.py` | 기본 행을 summary로, `--full`이면 `## 레포별 책임` 제목과 책임 전체 행을 출력 | ② 기존 `row()` 재사용 |
| `agent-wiki/scripts/generate_document_list.py` | 기본은 레포 전용 문서 `이름 — description`, 도메인 공유 문서 이름 한 줄, 다른 도메인 순서. `--full`이면 도메인 공유·레포 전용 문서 `이름 — description` 출력 | ② 기존 `doc_rows()`·`description()` 재사용 |
| `agent-wiki/scripts/generate_wiki_rules.py` | 선택 인자 `<index_path>`를 받아 문서 규칙 문장과 `색인:` 줄을 출력 | ② |
| `agent-wiki/hooks/session_start.py` | `--full` 출력을 합쳐 색인 파일을 원자적으로 쓴 뒤, 성공하면 색인 경로를 규칙 생성기에 넘김 | ⑦ `write_index` 5줄 |
| `agent-wiki/README.md` | 세션 주입 절, 로컬 사본 표, 위키 구조 트리 | ① 문서 |
| `agent-wiki/references/doc-contract.md` | 도입 문장, 6장 참조 금지 근거, 9장 도입·summary·responsibilities 문구 | ① 문서 |
| `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | 0.8.1→0.9.0, `metadata.version` 4.2.1→4.3.0 | ① |
| 사내 `plugins/agent-wiki/*`, 사내 `.claude-plugin/marketplace.json` | 위 변경 미러링(사내 고유 3파일은 바뀐 문구만), 최상위 4.3.1→4.4.0, agent-wiki 항목 0.9.0 | ① 복사 |

#### generate_repository_map.py

- **인자**: `<baseRoot> <workspace.root> <domain>/<slug> [--full]`
- **기본 출력**: 기존 `HEAD`를 유지하되 "의존 표식은 참고용이므로 책임만으로도"를 "summary만으로도"로 바꾸고 "레포별 책임 전체는 색인에 있습니다."를 덧붙임. 행 본문은 `summary`, 없으면 책임을 ` · `로 이은 값
- **`--full` 출력**: `## 레포별 책임` 제목 뒤 같은 표식의 행을 책임 전체(없으면 summary)로 출력하고 `HEAD`는 출력하지 않음

#### generate_document_list.py

- **인자**: `<baseRoot> <domain>/<slug> [--full]`
- **기본 출력**: `## {slug} 전용 문서`(경로 줄, `- 이름 — description`) → `## 도메인 공유 문서 {N}개`(경로 줄 뒤 ` — 문서별 용도(description)는 색인 파일에 있음`, 빈 줄, 이름을 `, `로 이은 한 줄) → `## 다른 도메인 문서`. 문서가 없는 블록은 지금처럼 제목째 생략함
- **`--full` 출력**: `## 도메인 공유 문서`와 `## {slug} 전용 문서`를 경로 줄과 `- 이름 — description` 행으로 출력하고 다른 도메인은 넣지 않음

#### generate_wiki_rules.py

- **인자**: `<domain>/<slug> [<index_path>]`
- **색인 있음**: 첫 불릿을 "사용자 요청에 맞는 문서를 아래 이름 목록에서 찾아 읽으세요. 이름만으로 고르기 어려우면 색인의 description을 보고, 그래도 없으면 문서 폴더를 grep해 본문까지 찾습니다."로 쓰고, 규칙 불릿 뒤에 빈 줄과 `` 색인: `{index_path}` — 레포별 책임 전체, 문서별 description ``을 둠
- **색인 없음**: 첫 불릿을 현행 문장으로 두고 `색인:` 줄을 생략함. 색인 쓰기에 실패한 세션만 해당함

#### session_start.py

- **순서**: 도메인 판정 뒤 `generate_repository_map.py … --full`과 `generate_document_list.py … --full`을 실행함. `# 위키 색인 — {key}` 제목과 두 출력을 빈 줄로 이어 `write_index`로 씀. 이어서 규칙(성공 시 색인 경로 포함), 레포 지도, 문서 목록 순으로 주입문을 만듦
- **`write_index`**: `{baseRoot}/.local/index/{domain}/{slug}.md`의 상위 폴더를 만들고, 같은 폴더의 `{name}.{pid}.tmp`에 쓴 뒤 `os.replace`로 바꿈. 같은 레포 세션이 동시에 열려도 반쯤 쓰인 파일이 보이지 않게 하기 위함이며, `OSError`면 색인 없이 진행함
- **기존 동작 유지**: 생성기별 5초 timeout과 실패 블록 생략, 어떤 실패에도 종료 코드 0, 미등록·위키 없음 한 줄 주입은 그대로 둠
- **머리 주석**: 2~3행에 색인 파일 생성을 덧붙임

#### README.md

- **세션 주입 절**: 주입은 위키 규칙, 같은 도메인 레포 지도(summary와 의존 표식), 레포 전용 문서 `이름 — description`, 도메인 공유 문서 이름, 다른 도메인 목록이라고 적음. 레포별 책임 전체와 문서 description은 훅이 세션마다 `{baseRoot}/.local/index/{domain}/{slug}.md`에 쓰는 색인에 있고 주입에는 그 경로만 넣는다고 적음
- **로컬 사본 표**: 위키 사본 행에 "단, 훅이 세션마다 `.local/index/`에 색인을 생성"을 덧붙임
- **위키 구조 트리**: `.local/index/` 행(세션 색인, 훅 생성)을 추가함

#### doc-contract.md

- **도입(3행)**: "세션에 주입된 `이름 — description` 목록으로 열 문서를 고르고"를 "세션에 주입된 문서 이름과 색인 파일의 `이름 — description`으로 열 문서를 고르고"로 바꿈
- **6장 참조 금지**: 근거 "목록이 매 세션 주입됨"을 "이름 목록과 색인이 매 세션 제공됨"으로 바꿈
- **9장 도입**: "세션은 `responsibilities`(없으면 `summary`)와 간선의 `to`로 작업할 레포를 고릅니다"를 "세션 주입은 `summary`와 간선의 `to`로 만든 의존 표식을 싣고, `responsibilities`는 세션 색인에 실립니다"로 바꿈
- **9장 summary·responsibilities**: summary에 "— 세션 주입에서 레포를 고르는 한 줄임", responsibilities 근거를 "색인에서 작업할 레포를 고르는 열쇠임"으로 바꿈

### 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | 생성기 3종과 훅 | 아래 V1~V4가 모두 통과함 |
| 2 | README·doc-contract 문구 | `grep -n '이름 — description\` 목록으로' agent-wiki/references/doc-contract.md`와 `grep -n '목록이 매 세션 주입됨' agent-wiki/references/doc-contract.md` 결과가 없음. `grep -c '.local/index' agent-wiki/README.md`가 2 이상임 |
| 3 | 버전 0.9.0·4.3.0 | `python3 -c "import json;print(json.load(open('agent-wiki/.claude-plugin/plugin.json'))['version'], json.load(open('.claude-plugin/marketplace.json'))['metadata']['version'])"` 출력이 `0.9.0 4.3.0`임 |
| 4 | 사내 마켓플레이스 미러 커밋(사내 레포, push는 확인 후) | `diff -rq {사내}/plugins/agent-wiki agent-wiki` 출력이 `README.md`·`config.json`·`references/publish.md` 세 줄뿐임. V5 통과. 사내 marketplace.json 최상위 `version` 4.4.0, agent-wiki 항목 0.9.0 |

검증 명령은 zsh 단어 분리 문제를 피하려고 bash 스크립트 파일이나 `python3 - <<'EOF'`로 실행합니다.

- **V1 생성기 단위**: 개인 위키(`~/.agent-wiki`)의 이 레포 키로 세 생성기를 기본·`--full`로 실행함. 기본 지도 행에 summary가 있고 책임 문장이 없음, `--full` 첫 줄이 `## 레포별 책임`임, 문서 목록 기본 출력에 `문서별 용도(description)는 색인 파일에 있음`이 있음
- **V2 훅 통합**: `echo '{"source":"compact"}' | CLAUDE_PROJECT_DIR=$PWD python3 agent-wiki/hooks/session_start.py` 출력이 JSON으로 파싱되고, `additionalContext`에 `` 색인: ` ``이 있으며, `~/.agent-wiki/.local/index/personal-claude-tooling/my-claude-plugin-market.md`가 `## 레포별 책임`과 `## 도메인 공유 문서`를 담음. `compact`를 써서 위키 강제 정리를 건너뜀
- **V3 사내 위키 전수 크기**: 수정한 생성기를 `~/.onestore-llm-wiki`의 모든 등록 키로 실행해 주입문(규칙은 색인 경로 인자 포함)을 조립하고, 최댓값이 10,000자 미만이며 상위 3개 크기를 보고함
- **V4 벤치마크 일치**: V3에서 벤치마크 대상 레포의 주입문을 `~/.agent-wiki-bench/session-injection/preview-api.txt`와 diff해, 차이가 문서 목록 제목·경로 줄 문구와 위키 고정 시점(7e1086e) 뒤의 위키 내용 변화뿐임을 확인함
- **V5 사내 미러 통합**: V3에서 주입이 가장 큰 레포의 로컬 체크아웃으로 `CLAUDE_PROJECT_DIR`를 두고 사내 미러 훅을 `compact`로 실행해, `additionalContext`가 10,000자 미만이고 `~/.onestore-llm-wiki/.local/index/{domain}/{slug}.md`가 생성됨을 확인함

### 특이 사항

- **범위 밖**: 개인판 PR 생성(`/pr-workflow:create`), 머지 뒤 개인 위키의 세션 훅·위키 사본 문서 갱신(`/agent-wiki:add`), 책임 원본 축약(register·update 규약), 색인 두 파일 분리(미실측)
- **의도적 단순화**: 색인 쓰기에 실패하면 그 세션만 현행 문서 규칙 문장으로 돌아가지만, 레포 지도 문구의 "레포별 책임 전체는 색인에 있습니다"와 문서 목록 제목 줄은 그대로 남음. 쓰기 실패가 반복 보고되면 두 문구도 색인 경로 유무로 가름
- **동기화 지연**: 위키 동기화가 3초를 넘기면 색인도 주입문과 같이 이전 사본으로 만들어지며, 다음 세션에서 바로잡힘(현행 주입과 같은 동작)
- **실세션 확인**: 사내 플러그인 갱신 뒤 대형 도메인 레포에서 새 세션을 열어 `<persisted-output>` 없이 주입되는지를 사용자가 한 번 확인함
