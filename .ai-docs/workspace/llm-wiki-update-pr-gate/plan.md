# llm-wiki update — PR 승인 게이트와 사실 원장 PR 본문

## Context

- **현황**: `/llm-wiki:update`는 문서·커서 커밋을 위키 `main`에 바로 push하고, 처리 근거는 터미널 보고로만 남아 세션이 끝나면 사라짐
- **목표**: 반영 결과를 PR로 올려 사람이 머지해야 `main`에 들어가게 하고, PR 본문에 추출 사실마다 판정·사유·출처를 남겨 검토 자료이자 이후 히스토리로 삼음
- **완료 조건**: update 1회 실행이 `wiki-update/*` 브랜치 PR 1건으로 끝나고, 본문만으로 "어느 머지에서 무엇을 뽑아 어느 문서에 어떻게 반영·기각했는지" 추적 가능함

## 결정 사항

- **커서 동행**: `state/{slug}.json` 커서 커밋도 PR에 포함 — 머지 전에는 `main` 커서가 그대로라 PR close가 곧 전체 거절이 되고 다음 실행이 같은 머지를 다시 처리함
- **중복 방지**: 열린 `wiki-update/` PR이 있으면 그 링크를 보고하고 중단 — 머지 전 재실행은 같은 머지를 두 번 추출함
- **작업 위치**: `WIKI_ROOT` 자체에서 `origin/main` 기준 브랜치로 전환 후 작업, 끝나면 `main`으로 복귀 — worktree는 `.local/mirrors`가 `--wiki` 경로 아래라 미러를 다시 clone하므로 채택하지 않음, 복귀는 세션 주입이 미승인 문서를 읽지 않게 하기 위함
- **PR 생성 실패**: 브랜치 push까지는 수행하고 `gh pr create` 실패 시 브랜치 이름과 오류 한 줄을 보고 — 무인 실행에서 묻지 않음 원칙 유지
- **머지 방식 안내**: 본문 꼬리에 squash 금지 명시 — 문서별 커밋 본문(규약 8장 발견 근거·기존/새 값)이 이력의 정본
- **본문 작성 주체**: 메인 에이전트가 JSON 산출물을 한 번 순회해 템플릿을 채움, 별도 렌더 스크립트는 두지 않음

## 변경 파일

### `llm-wiki/templates/update-pr.md` (신규) — PR 본문 템플릿

````markdown
## 요약
- **레포**: {slug} 머지 {N}건 외 레포별 한 구
- **집계**: 사실 {n}건 — 추가 {a} · 교체 {r} · 동일 {s} · 건너뜀 {k} · 검토 삭제 {d} · 기각 {j}, 문서 신규 {c} · 수정 {m}, 그래프 {변경 요약 또는 "변경 없음"}

## 레포
| 레포 | 처리 머지 | 커서 | 비고 |
|---|---|---|---|
| pigeon-trade | [c61a8ab](https://github.com/.../commit/{sha}) {커밋 제목} | 1c7f783 → c61a8ab | — |
| pigeon-trade-dashboard | 0건 | 변화 없음 | 대상 브랜치 main 없음 — registry `defaultBranch` 수정 필요 |

## 추출 사실
| # | 사실 | 판정 | 사유 | 출처 |
|---|---|---|---|---|
| F1 | 도메인 모듈은 위임 전용 외부 노출 서비스(`{Domain}ExternalService`) 하나만 export | 추가 | — | pigeon-trade@c61a8ab |
| F4 | 통화 타입 이름은 `Currency` | 교체 | 기존 `BrokerageCurrency` · 인용 "…" | pigeon-trade@c61a8ab |
| F6 | 외부 노출 서비스 파일 위치는 `service/{domain}-external.service.ts` | 검토 삭제 | 코드로 확인 가능, 기각 대안 없음 | pigeon-trade@c61a8ab |
| F9 | … | 기각 | 한 주제 아님 | pigeon-trade@c61a8ab |

## 문서

### pigeon-trade/domain-module-exports.md · 신규
- **추가**: `외부 노출` 절에 외부 노출 서비스 단일 export 규칙과 기각한 DI 파사드 설계 (F1)
- **추가**: `검증` 절에 모듈 연결 변경 시 로컬 기동 확인 절차 (F2)
- **삭제**: 외부 노출 서비스 파일 위치 불릿 — 코드로 확인 가능 (F6)

### pigeon-trade/brokerage-market-data-strategy.md · 수정
- **교체**: 통화 타입 이름 `BrokerageCurrency` → `Currency` (F4)

## 그래프
- **간선**: … (변경 없으면 절 생략)

## 검토 방법
- **승인**: rebase 또는 merge commit으로 머지 — squash는 문서별 커밋 근거를 지우므로 금지
- **부분 수정**: 이 브랜치에서 해당 불릿을 고친 뒤 머지
- **전체 거절**: PR close — 커서가 `main`에 반영되지 않아 다음 실행이 같은 머지를 다시 처리
- **건너뜀 처리**: 판정 `건너뜀` 행은 머지 후 `/llm-wiki:add`로 반영
````

- **작성 규칙**: 사실 원장은 모든 추출 사실을 번호 순 1행씩(동일 포함), 사유는 교체면 기존 값·인용, 건너뜀이면 기존 값과 사유, 기각·검토 삭제면 사유, 출처는 `{slug}@{sha7}`(근거 여러 개면 쉼표)
- **문서 절**: 편집 문서마다 `### {도메인 루트 기준 상대경로} · 신규|수정`, 불릿은 `**추가|교체|삭제**: {절}에 {무엇} (F번호)`로 판정별 한 줄, 동일은 적지 않음
- **생략**: 행이 없는 절(그래프·문서 등)은 절째 생략

### `llm-wiki/skills/update/SKILL.md`

- **1장 범위**: 동기화 앞에 열린 PR 검사 `gh pr list --repo {origin} --state open --json url,headRefName`에서 `wiki-update/` 접두가 있으면 보고 후 중단, 동기화 뒤 `git -C {WIKI_ROOT} switch -c wiki-update/{YYYYMMDD-HHMM} origin/main`(`--dry-run`은 브랜치를 만들지 않음)
- **3장 배정**: 병합한 사실마다 `F{n}` 번호를 시각 순으로 부여하고, 기각 사실도 `assign.json` `rejected[{id, fact, shas, reason}]`에 남김 — 지금은 사유별 건수만 남아 원장에 쓸 수 없음
- **4장 반영 출력**: `verdicts[]`에 `summary`(절과 반영 내용 한 구) 추가 — 문서 절 불릿의 원천
- **5장 검토 입력·출력**: 입력에 그 문서 사실 행(`id`·`fact`)을 싣고 `removed[]`에 `ids`(삭제 불릿이 담던 사실 번호) 추가 — 삭제를 원장 행과 잇기 위함
- **6장**: 커밋 규칙은 그대로 브랜치에 커밋, `push` 줄을 `git push -u origin {branch}` 후 `gh pr create --base main --head {branch} --title "update: {날짜} 머지 {N}건 · 문서 {M}장" --body-file {스크래치}/pr.md`, 마지막에 `git switch main`으로 교체 — 커밋 0건(부트스트랩 없음·사실 0건·커서 불변)이면 브랜치 삭제 후 PR 없이 종료
- **7장 보고**: `templates/update-pr.md` 규칙으로 `{스크래치}/pr.md` 작성, 터미널 보고는 PR 링크와 요약 2줄로 축소
- **본문 길이**: `pr.md`가 60,000바이트를 넘으면 사실 원장을 PR 첫 코멘트(`gh pr comment --body-file`)로 옮기고 본문에 그 안내 한 줄
- **머리말**: "사용자에게 묻지 않습니다" 뒤에 "반영은 PR 머지로 승인됩니다" 한 구 추가, description의 "advances cursors"를 "opens a PR carrying docs and cursors"로

### 그 외

- **`references/doc-contract.md` 8장**: 편집 주체 표 update 행의 커서 칸을 `state/` 전진(PR 경유)로, 건너뜀 보고 문장에 "update는 PR 본문 사실 원장" 병기
- **`README.md`**: update 행 설명에 "PR로 올려 머지 승인" 반영
- **버전**: `plugin.json` 5.2.0 → 5.3.0, `marketplace.json` 설명 문장에 PR 승인 반영

## 검증

- **정적 확인**: 수정한 SKILL.md에서 1~7장이 참조하는 JSON 키(`rejected`·`summary`·`ids`)가 생산 장과 소비 장에서 같은 이름인지 대조
- **dry-run**: `/llm-wiki:update --dry-run`이 브랜치·PR 없이 3장에서 종료하는지 확인
- **실실행**: 위키에 미처리 머지가 있는 레포로 `/llm-wiki:update --repo {slug}` 실행 후 `gh pr view`로 본문이 템플릿 구조(요약·레포·추출 사실·문서·검토 방법)를 따르는지, 로컬 `WIKI_ROOT`가 `main`으로 복귀했는지, `main`의 `state/{slug}.json`이 불변인지 확인
- **중복 차단**: PR이 열린 상태에서 재실행해 PR 링크 보고 후 중단하는지 확인
