# llm-wiki 4.0.0 — 그래프 스키마 개편과 현행 합의 모델

## Context

- **배경**: llm-wiki 3.0.0은 노드 스키마·주입 형상·조사 절차·합의 모델(등급·출처·verified·낡음·inbox)이 무거워 주입 토큰과 운영 부담이 큼
- **목표**: 노드·간선 스키마 개편, 레포 지도 중심 주입, 4레인 조사, 그래프 화면, 등급을 없앤 현행 합의 모델을 4.0.0으로 반영
- **합의 범위**: 합의 모델(등급·출처·verified·낡음·inbox 제거, update 무인 전역 시간순)까지 전부, 노드 `project`는 GitHub owner URL, view.py·graph.html 포함, 위키 데이터 이관은 README 안내만

## 변경 대상

- **스키마 개편**: 노드 `remote`·`defaultBranch`·`responsibilities`(평문 배열)·`hosts`(환경별 1개)·`project`, `domains.{d}.repos.{slug}` 중첩, `deps.{from}[]` 그룹 맵·`contracts[]`, `excluded`→`dormant`
- **스키마 단일 정본**: `graph.py schema --for survey|facts --lane --domain`, 스킬 프롬프트의 상수 직기재 제거
- **주입 재편**: 레포 지도·의존 3묶음, `graph.py repo {slug}`·`render`·`map`, 경유 1홉 간선, contracts 형식 경고
- **조사 개편**: register 4레인 병렬 + 2.5장 메인 검증, `survey.py` 증거 인벤토리
- **그래프 화면**: `scripts/view.py`, `templates/graph.html`
- **합의 모델**: frontmatter description만, 등급·출처·inbox·낡음 제거, update.py 전역 시각 순 `--max-merges 40`·`domains` 서브커맨드 삭제, doc-contract 7장 판정 넷
- **저장소 절차**: 스킬 시작 `git pull --ff-only`, 끝 `git pull --rebase && git push`, 건너뛴 사실은 스킬 최종 보고의 `| 주제 | 위치 | 기존 값 | 새 값·사유 |` 표
- **GitHub owner**: `project`는 `https://{host}/{owner}`, 접근 좌표 `GitHub {owner}`, clone 패턴 `{host}/{owner}/{slug}`, register 정본 remote는 upstream → origin

## 검증

- **정적**: `python3 -m py_compile llm-wiki/scripts/*.py`
- **픽스처 위키**: 도메인 1, `project: https://github.com/argon1025`, 레포 2, 간선 1로 아래 명령이 에러 0·기대 출력

```
python3 llm-wiki/scripts/graph.py check --wiki $FIX
python3 llm-wiki/scripts/catalog.py --check --root $FIX/knowledge $FIX/registry.json $FIX/deps.json
python3 llm-wiki/scripts/graph.py render --wiki $FIX --domain argon1025-side --slug my-claude-plugin-market
python3 llm-wiki/scripts/graph.py schema --for survey --lane http
python3 llm-wiki/scripts/view.py --wiki $FIX --no-open
```

- **훅**: `LLM_WIKI_ROOT=$FIX CLAUDE_PROJECT_DIR=$PWD bash llm-wiki/hooks/session_start.sh </dev/null`이 JSON을 내고 접근 좌표 `GitHub argon1025`, clone 패턴 `github.com/argon1025/{slug}`, 위키 부재 시 `/llm-wiki:init` 안내

## 추가 계획 2026-09-25 — 프롬프트 잔존 문장 제거와 규칙 단일 소유

### Context

- **배경**: `feat/llm-wiki-v4`의 프롬프트 7종(agent-guide, doc-contract, 스킬 5종)은 3.x 문장 위에 4.0.0 변경만 덧대어 같은 규칙이 2~3곳에 중복되고, 설계 근거 문장과 3.x 잔재가 에이전트 지시에 섞여 있음
- **목표**: 규칙마다 소유 위치를 하나로 정하고 나머지는 장 번호 참조로 바꾸며, 실행에 영향 없는 근거·메타 문장과 스크립트(`graph.py schema`·`check`, `catalog.py --check`)가 이미 강제하는 항목을 제거함
- **범위 밖**: `hooks/session_start.sh`(주입 문자열은 이미 최소, 나머지는 셸 주석), `README.md`, 스크립트 코드

### 소유 원칙

- **doc-contract**: 판정 기준의 유일한 정본 — 스킬은 "규약 N장"으로만 참조하고 기준 문장을 다시 쓰지 않음
- **graph.py schema 출력**: 서브에이전트용 값 규칙 정본 — 스킬 프롬프트·레인 표에 같은 규칙을 다시 적지 않음
- **스킬**: 순서·정지점·명령·실패 처리만 소유 (동기화 명령·push 재시도는 스킬 쪽에 둠)

### 파일별 조치

### rules/agent-guide.md (매 세션 주입 — 토큰 직결)

- **레포 지도**: 행위 낱말 8종 나열 삭제 — 지도 행 자체에 낱말이 실리고 정의는 doc-contract 9장 소유, `(휴면)` 파급 포함 설명만 유지
- **도메인의 다른 의존**: 불릿 삭제 — 주입 헤더(`graph.py` render)가 이미 "계약은 `graph.py map`"을 출력함, 수정 순서 용도는 추가 조회의 `map` 행에 한 구절로 흡수
- **직접 수정 금지**: "노드·간선은 register·add·update만, `state/` 커서는 update만" 삭제 — 스킬 내부 편집 주체라 일반 세션 에이전트 행동에 무관, doc-contract가 소유
- **유지**: 이 레포가 의존·이 레포에 의존·문서 목록·추가 조회·문서 우선·모순 보고·기록 제안

### references/doc-contract.md

- **1장 제외 통합**: `제외 판정선`과 `담지 않는 것`을 한 불릿으로 병합, `레포 폴더` 불릿은 3장 위치 판정으로 이동, `자료 필터`는 add 전용이라 add 2장으로 이동
- **3장 레포 편차 삭제**: 7장 레포 편차와 중복 — 7장 하나에 국가코드 예시를 옮겨 통합
- **7장 대조**: 정본 유지, add 3장·update 3장의 대조 문장은 이 장 참조로 교체
- **7장 적용 순서 삭제**: update 전용이며 update 3장 시각 순과 중복, 교체 조건의 "머지 시각은 적용 순서만 정함" 구절로 충분
- **7장 병합 방식 보강**: "기존 본문 유지·해당 값만 고침"에 "새 값으로 거짓이 된 다른 불릿은 같은 편집에서 삭제" 추가 — 현행 규칙은 에이전트의 기존 줄 보존 경향을 위키 자체에 고착시켜 모순 불릿이 남음
- **8장 동기화·입력 밖 금지 삭제**: 스킬 5종이 명령과 실패 처리를 각자 소유하고 서브에이전트 프롬프트에도 금지가 있어 3중 기재
- **9장 축소**: `graph.py schema`·`check`가 강제하는 항목(책임 문장 형식·행위 낱말·책임 금지·hosts 리터럴, project·remote 형식, dormant `reason`)은 한 줄 "값 규칙은 `graph.py schema --for facts`, 형식은 `check`"로 교체하고, 스크립트에 없는 의미만 유지 — 중첩, project가 owner 파생원, dormant 의미, remote 정본·포크 금지, defaultBranch 용도, 경로 접두·IP 규칙
- **간선 대상 판정 이동**: 9장에서 10장으로 옮기고 register 2.5③·4장, update 3장의 동일 절차(메시지 소비처 `@RabbitListener` 확인, http 라우트 실재 확인, 호스트 정규화 비교)를 이 한 곳으로 모음
- **10장 중복 병합**: `외부 시스템`은 9장 책임 금지 괄호와 합쳐 한 곳, `삭제` 불릿은 `contracts` 불릿의 "7장 교체 조건" 구절과 합침
- **편집 주체 통합**: 9장 `편집 주체`와 10장 `작성 주체`를 8장 아래 `| 스킬 | 노드 | 간선 | 커서 |` 표 하나로 병합

### skills/register/SKILL.md (중복·근거 문장 최다)

- **3.x 잔재 삭제**: 3장 도메인의 "(접근 좌표는 노드 `project`에서 파생되므로 따로 받지 않음)" — 3.x에서 묻던 항목의 부정 서술
- **근거 문장 삭제**: 1장 도메인 예비 판정 꼬리("확정은 3장이며 … 다시 보이지 않음"), 2장 도입 설계 근거, 스키마 "다시 적지 않습니다" 메타 문장, 2.5장 도입, 2.5④ 꼬리, 3장 상대 미정 꼬리, 4장 도메인 이동의 "책임 문장은 도메인 접두가 없어" 반복, 6장 조사 품질 꼬리
- **레인 표**: http 초점의 "(선언 위치 원칙)" 괄호 삭제 — 프롬프트에 싣는 schema 출력이 동일 규칙 포함
- **2.5③·4장 병합**: target 확정 절차를 doc-contract 10장 참조 한 줄로, 4장 `간선 상대 판정`은 "2.5③에서 정해진 target만 실재 확인"으로 축소
- **contracts 접기**: 2.5⑤와 4장 간선의 "3건 넘으면 접음" 중 4장 쪽 삭제
- **3장 상태**: "휴면이어도 스택·소관·책임은 지우지 않음" 삭제 — 9장 dormant 의미가 소유

### skills/update/SKILL.md

- **3장 축소**: `대조`·`간선 상대`·`선언 위치`·`책임·호스트` 교체 조건을 각각 규약 7장·10장 참조로 교체하고, update 고유 규칙(후보 둘이면 좁은 문서, 기각 사유 문자열)만 유지
- **시각 순**: 유지 — doc-contract 7장 적용 순서 삭제로 이 장이 유일 소유

### skills/add/SKILL.md

- **3장 대조**: 규약 7장 참조로 축약
- **2장 자료 필터**: doc-contract 1장에서 이동해 받음
- **6장 반영 시점**: 유지 — 사용자 보고 항목

### skills/audit/SKILL.md

- **1장 그래프**: "`responsibilities`가 빈 `active` 노드" 삭제 — `graph.py check`가 이미 에러로 냄(`graph.py:660`)
- **3장 적용 제외**: 빈 노드·contracts 상한 간선을 건너뜀 표에서 빼고 6장 `그래프 경고` 행으로 이동 — 건너뜀 표는 값이 어긋난 사실용이라 용도 불일치
- **2장 신호표**: description 길이 행을 "`--check` 힌트의 길이 에러·'때' 미종결·범주어만"으로 — 60자는 `catalog.py` `DESCRIPTION_LIMIT`가 소유

### skills/init/SKILL.md

- **3장 골격**: 각 파일의 이유 꼬리를 삭제하고 파일·내용만 남김, `.gitignore`만 "clean-tree 판정" 한 구절 유지 (누락 시 이후 스킬이 막히는 유일한 비자명 항목)

### 검증

- **참조 무결성**: 스킬이 가리키는 "규약 N장"과 서브에이전트 `sed` 범위(`## 1\.`~`## 8\.`, `## 3\.`~`## 8\.`, `## 5\.`~`## 6\.`)가 재편 후 장 번호와 일치하는지 grep으로 대조

```
grep -n "규약 [0-9]" llm-wiki/skills/*/SKILL.md llm-wiki/rules/agent-guide.md
grep -n "sed -n" llm-wiki/skills/*/SKILL.md
```

- **규칙 누락 대조**: 삭제한 규칙마다 소유 위치(doc-contract 장 또는 `graph.py schema` 출력)에 같은 내용이 있는지 확인

```
python3 llm-wiki/scripts/graph.py schema --for facts
python3 llm-wiki/scripts/graph.py schema --for survey --lane responsibilities
```

- **주입 크기**: 픽스처 위키로 훅을 실행해 agent-guide 축약 전후 `additionalContext` 길이 비교

```
LLM_WIKI_ROOT=$FIX CLAUDE_PROJECT_DIR=$PWD bash llm-wiki/hooks/session_start.sh </dev/null | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"]))'
```

- **커밋**: 파일 성격별 3커밋 — `refactor(llm-wiki): doc-contract 규칙 단일 소유`, `refactor(llm-wiki): 스킬 중복·근거 문장 제거`, `refactor(llm-wiki): 세션 주입 규약 축약`
