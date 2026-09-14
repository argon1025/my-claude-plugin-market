# plan-workflow

계획 스냅샷과 작업 중 알게 된 사실을 저장소 안 `.ai-docs/workspace/{slug}/`에 남기는 규약을 세션에 주입하고, 계획 수립·실행 스킬 2종을 제공하는 플러그인입니다.

| 스킬 | 트리거 예 | 역할 |
| --- | --- | --- |
| `/plan-workflow:planning` | "계획 세워줘", "플랜 모드", "기능 설계" | 의도 확인, 요청 분해, 확인 축, 최소 코드 사다리, 자기완결 계획, 승인 시 `plan.md` 스냅샷 커밋(기존 계획이 있으면 `## 추가 계획` 절로 덧붙임) |
| `/plan-workflow:execute` | "계획 실행", "플랜 실행" | 새 세션에서 `plan.md`를 읽어 미실행 절만 태스크 → 검증 → 커밋 단위로 실행, 어긋나면 정지 후 `## Re-plan` |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install plan-workflow@my-claude-plugin-market
```

요구 사항은 `python3`와 `git`입니다. git 저장소 밖에서는 아무것도 주입하지 않습니다.

## 동작 방식

- **SessionStart**: `rules/agent-guide.md`(약 1.7KB)와 `## 현재 워크스페이스` 블록을 주입하며, matcher가 없어 startup·resume·clear·compact 모두에서 다시 실행됨
- **slug 계산**: 현재 브랜치명의 `/`를 `-`로 바꾼 값을 훅이 계산해 값으로 주입하며, `main`·`master`·`develop`이나 detached HEAD면 미확정으로 표시해 첫 기록 시 작업 주제로 폴더를 정하게 함
- **기록 자동 로드**: 현재 slug 폴더에 `feedback.md`가 있으면 전문을 함께 주입하고(4,000바이트 초과 시 최근 항목만), `plan.md`가 있으면 구현은 `/plan-workflow:execute`, 추가 계획은 `/plan-workflow:planning`으로 가도록 안내함
- **형식 지연 로드**: `feedback.md` 항목 형식은 `references/record-format.md`에 두고 첫 기록 전에 읽게 하여 상시 주입에서 제외함

규약 준수 여부는 검사하지 않습니다. 끄려면 `/plugin`에서 플러그인을 비활성화합니다.

## 산출물

```
.ai-docs/workspace/
└── {slug}/
    ├── plan.md        # 플랜 모드를 거친 경우, 승인된 계획 원문 + `## 추가 계획`·`## Re-plan` 절
    └── feedback.md    # 항상, 유형 코드 불릿(why·correction·constraint·context)
```

## 기록 규약 요약

- **의도 확인**: 코드를 고치기 전에 왜·누가·완료 조건을 확인하고 사용자 문장 그대로 `context` 항목으로 기록
- **기록 기준**: 코드를 읽은 에이전트라도 없으면 잘못 움직일 사실만 `why`·`correction`·`constraint`·`context` 네 유형으로 기록
- **계획 분리**: 계획 세션은 `plan.md`·`feedback.md` 스냅샷 커밋에서 끝나고 구현은 새 세션에서 시작
- **계획 누적**: 같은 slug에 계획이 이미 있으면 덮어쓰지 않고 `## 추가 계획 YYYY-MM-DD — {계기}` 절로 덧붙이며, 무효가 된 앞 절은 삭제 대신 폐기 선언으로 표시
- **덧붙이기**: 앞선 항목은 고치지 않고 파일 끝에 추가하며 PR 전 브랜치를 한 번 훑어 보충

## 방법론 출처

최소 코드 사다리는 [ponytail](https://github.com/DietrichGebert/ponytail)의 단계별 최소 구현 원칙을 계획 단계의 설계 결정으로 옮긴 것입니다.
