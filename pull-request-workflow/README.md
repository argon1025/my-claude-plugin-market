# pull-request-workflow

GitHub PR 워크플로 플러그인이에요. PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종을 제공해요.

| 스킬 | 트리거 예 | 역할 |
|---|---|---|
| `/pull-request-workflow:create-pull-request` | "PR 생성", "PR 올려줘" | 피처 브랜치를 base 브랜치 대상 PR로 생성해요 |
| `/pull-request-workflow:review-pull-request` | "PR 리뷰해줘", PR URL 제시 | PR을 파일별로 리뷰하고 승인 후에만 코멘트를 게시해요 |
| `/pull-request-workflow:resolve-review-comments` | "리뷰 반영", "코멘트 반영" | 미해결 리뷰 코멘트를 판정·수정하고 답글까지 처리해요 |

## 전제 조건 (필수)

- **GitHub CLI(`gh`) 설치 + 로그인** — 세 스킬 모두 `gh` 명령(REST/GraphQL 포함)을 사용해요. `gh auth status`가 실패하면 스킬이 시작 시점에 중단돼요.
- 대상 repo의 체크아웃 안에서 실행해야 해요 — review/resolve는 로컬 git 이력으로 diff를 조달해요.

## /pull-request-workflow:create-pull-request — PR 생성

완성된 피처 브랜치로 PR을 생성해요. base 브랜치는 `develop`이 있으면 `develop`, 없으면 repo 기본 브랜치를 써요. 로컬 `origin`이 개인 fork여도 `gh`가 원본 repo를 감지해서 푸시·리뷰어 지정·PR 본문 작성을 자동으로 처리해요.

## /pull-request-workflow:review-pull-request — AI 코드리뷰

PR 스냅샷을 기준으로 파일별 리뷰와 반증 패스를 거쳐 발견 사항을 Blocker/Bug/개선으로 판정해요. 코멘트는 보고서를 먼저 보여주고 사용자가 승인한 뒤에만 게시해요.

### 방법론 출처 — alibaba/open-code-review

이 스킬의 리뷰 방법론은 [alibaba/open-code-review](https://github.com/alibaba/open-code-review)(이하 OCR)에서 가져왔어요.

- OCR은 Go로 작성된 AI 코드리뷰 CLI(`ocr` 명령)예요. 알리바바 사내 공식 리뷰 도구로 2년 운영한 뒤 오픈소스(Apache-2.0)로 공개됐어요. ([공식 문서](https://alibaba.github.io/open-code-review/))
- 설계 철학: 파일 선정·룰 매칭·코멘트 라인 위치 지정은 결정론적 코드가 담당하고, 결함 판단은 LLM이 담당하는 하이브리드 구조예요.
- 제품 원칙: 재현율(Recall)을 희생하더라도 정밀도(Precision)를 우선해요 — 노이즈 코멘트보다 놓침을 감수하는 선택이에요.

OCR의 주요 기능:

- 명령 3종 — `ocr review`(diff 리뷰), `ocr scan`(diff 없이 전체 파일 감사), `ocr viewer`(세션 기록 WebUI)
- 파일별 독립 서브에이전트 병렬 리뷰 + Strict Focus 규칙 (다른 파일에서 발견한 이슈는 코멘트 금지)
- category/severity 필드를 강제하는 구조화 코멘트 스키마
- falsify(반증) 필터 — 리뷰 완료 후 별도 LLM 호출로 "틀렸다고 확인 가능한 코멘트만" 제거해요
- 변경 50라인 이상일 때만 리뷰 전에 계획(Plan)을 세우는 조건부 Plan 단계
- 슬라이딩 윈도우 라인 앵커링 + 실패 시 재앵커링
- 언어별 내장 룰 체크리스트 19종과 4계층 룰 우선순위

### 무엇을 어떻게 이전했는지

프롬프트 전략은 이식하고, 결정론적 코드가 필요한 부분은 근사하거나 제외했어요. 실구현은 `skills/review-pull-request/SKILL.md`와 `skills/review-pull-request/references/`에 있어요.

| OCR 기능 | 이전 | 이 스킬에서의 구현 |
|---|---|---|
| 파일별 독립 리뷰 + Strict Focus | O | 파일 1개 = 서브에이전트 1개(배치 최대 5개), Strict Focus 원문을 서브에이전트 프롬프트에 그대로 포함해요 |
| 구조화 코멘트 스키마 | O (변형) | category(버그/사이드이펙트/보안/성능/컨벤션/테스트) + grade(Blocker/Bug/개선) JSON 스키마로 재정의했어요 |
| falsify 반증 필터 | O | 리뷰 후 도구 없는 별도 서브에이전트가 diff만 보고 반증 가능한 발견만 제거해요 |
| 조건부 Plan 단계 | O | 파일 변경이 50라인 이상이면 리뷰 전에 리스크 포인트와 확인 전략을 먼저 세워요 |
| 언어별 룰 체크리스트 | O (변형) | OCR 내장 룰에서 선별해 주력 스택용 4종으로 재작성했어요 (`references/checklists/`: common, typescript-react, nestjs, java-spring). 프로젝트 자체 룰이 있으면 그쪽이 우선이에요 |
| 라인 앵커링 이중화 | 근사 | 결정론 코드 대신 3단계로 근사해요: grep 앵커 → 재앵커 LLM 호출 → 실패 시 파일 레벨 코멘트로 강등 |
| 5-gate 파일 필터·토큰 가드 | 근사 | 프롬프트 지시 기반 게이트(바이너리·lockfile·1,500라인 초과 파일 스킵 등)로 근사해요. 코드 수준 강제는 안 돼요 |
| GitHub/GitLab 연동, `ocr` CLI 실행 | X | diff 조회와 코멘트 게시는 `gh` CLI(REST/GraphQL)로 구현했어요 |

## /pull-request-workflow:resolve-review-comments — 리뷰 반영

PR 작성자 입장에서 미해결 코멘트 전건을 수용/기각/이미 해결로 판정해요. 수용한 건은 수정 커밋으로 반영하고, 일괄 승인 한 번으로 푸시·스레드별 답글·스레드 resolve까지 처리해요. `/pull-request-workflow:review-pull-request` 보고서의 "다음 단계"로 이어서 쓰는 스킬이에요.

## 단독 동작 원칙

- 다른 플러그인이나 MCP 서버 없이 `gh` CLI만으로 단독 동작해요.
- repo에 `.claude/pr-review-rules.md`가 있으면 리뷰 규칙으로 최우선 사용해요. 없으면 CLAUDE.md·AGENTS.md·docs/에서 리뷰 관련 규칙을 탐색하고, 그것도 없으면 내장 체크리스트만 사용해요.
