# dev-harness

프로젝트별 개발 하네스를 플러그인 하나로 제공해요. 프로젝트 위키(`.harness/docs/`)와 브랜치 작업 기록(`.harness/workspace/`)을 중심으로 한 계획 → 실행 → 리뷰 → 문서 수확 워크플로 규약을 세션 시작 시 자동 주입하고, 각 단계를 스킬 6종으로 지원해요.

## 동작 방식

- **SessionStart 훅**: 프로젝트 루트에 `.harness/` 디렉토리가 있으면 운영 규약(`rules/agent-guide.md`)을 세션 컨텍스트로 주입해요. `.harness/`가 없는 프로젝트에서는 아무것도 주입하지 않아요(무음 skip). 규약 안의 스크립트 경로는 훅이 실제 플러그인 설치 경로로 치환해서 넣어줘요. matcher를 지정하지 않아서 세션 시작뿐 아니라 컨텍스트 압축(compact)·재개(resume) 후에도 다시 실행돼요 — 규약이 압축으로 사라지지 않아요.
- **UserPromptSubmit 훅**: 매 턴 한 줄(~50토큰) 리마인드를 주입해요 — "알게 된 사실은 즉시 feedback.md에 append, 플랜 모드면 planning 스킬 필수 로드". 긴 세션에서 감쇠하기 쉬운 규칙만 되짚고, 전체 규약은 SessionStart 주입분이 담당해요. `.harness/`가 없으면 역시 무음 skip.
- **플러그인 vs 프로젝트 데이터 분리**: 플러그인은 규약·스킬·위키 인덱서(`scripts/wiki_index.py`)만 제공해요. 위키 문서와 브랜치 기록은 각 프로젝트의 `.harness/`에 남아요. 기존에 `.harness/`를 쓰던 프로젝트는 수정 없이 그대로 동작해요.

## 프로젝트 데이터 구조

```
<프로젝트 루트>/.harness/
├── docs/                    # 영구 위키 (frontmatter: description/scope/created/updated)
│   ├── {slug}.md            # flat 문서
│   ├── procedures/          # 절차 문서
│   ├── external/            # 외부 리소스 포인터
│   └── adr/                 # 아키텍처 결정 기록
└── workspace/
    ├── progress/{branch-slug}/   # 진행 중 브랜치: plan.md, feedback.md, review.md
    └── done/{branch-slug}/       # 머지 완료 브랜치 아카이브 (삭제 금지)
```

## 워크플로

1. `/dev-harness:init` — `.harness/` 없는 프로젝트에 데이터 디렉토리를 스캐폴딩해요 (멱등).
2. `/dev-harness:planning` — 플랜모드에 들어가면 진입 경로와 무관하게 반드시 먼저 로드해요. 요구사항 질문 커버리지·플랜 자기완결성을 보강하고, 승인 시 `plan.md` 스냅샷을 브랜치 첫 커밋으로 남겨요.
3. `/dev-harness:executing-plan` — 새 세션에서 승인된 플랜을 그대로 실행해요 (1 Task = 1 commit).
4. `/dev-harness:walkthrough` — 브랜치 작업을 유닛 단위로 개발자에게 인터랙티브하게 설명하고, 코멘트를 트리아지해 `review.md`로 남겨요.
5. `/dev-harness:writing-docs` — 머지된 브랜치의 `feedback.md`를 위키로 수확하고 워크스페이스 폴더를 `done/`으로 옮겨요.
6. `/dev-harness:harvest-docs` — 위키 전체를 주기적으로 감사해요 (중복 수렴, 도메인 분할, frontmatter 정리).

## 스킬 목록

| 스킬 | 역할 |
| --- | --- |
| `/dev-harness:init` | 프로젝트에 `.harness/docs`, `workspace/progress`, `workspace/done` 스캐폴딩 |
| `/dev-harness:planning` | 플랜모드 보강 — 질문 커버리지, 플랜 자기완결성, 승인 스냅샷 커밋 |
| `/dev-harness:executing-plan` | 승인된 플랜 스냅샷을 새 세션에서 실행 |
| `/dev-harness:walkthrough` | 브랜치 작업 인터랙티브 설명 + 코멘트 트리아지 + 리뷰 기록 |
| `/dev-harness:writing-docs` | 머지 브랜치 피드백을 위키로 수확, 워크스페이스를 done/으로 이동 |
| `/dev-harness:harvest-docs` | 위키 코퍼스 주기 감사 |

## 유스케이스 커버리지

규약은 주입된 가이드가 담고 있어서 **스킬을 호출하지 않아도 적용돼요.**

| 작업 경로 | 데이터 적재 |
| --- | --- |
| 플랜모드 + planning 스킬 | `plan.md` 스냅샷 커밋 + 작업 중 `feedback.md` append |
| 플랜모드 (스킬 미로드 방지) | 가이드·매 턴 리마인드가 planning 스킬 로드를 강제해요 |
| 직접 실행 (플랜 없음) | `feedback.md`만 쌓여요 — writing-docs는 `plan.md` 없는 폴더도 정상 수확해요 |
| 통합 브랜치(develop/main/master) 작업 | `feedback.md`를 기록하지 않아요 — 수확되지 않는 폴더가 생기는 것을 막기 위한 의도된 트레이드오프예요 |

## 요구 사항

- `python3` — 훅의 컨텍스트 주입과 위키 인덱서 실행에 사용해요.
- 프로젝트에 `.harness/` 디렉토리 — 없으면 규약이 주입되지 않아요. `/dev-harness:init`으로 생성해요.
