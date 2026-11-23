# my-claude-plugin-market

argon1025의 개인 Claude Code·Codex 플러그인 마켓플레이스입니다.

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install better-communication@my-claude-plugin-market
/plugin install pr-workflow@my-claude-plugin-market
/plugin install plan-workflow@my-claude-plugin-market
/plugin install auto-flow@my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [better-communication](./better-communication/README.md) | 간결하고 이해하기 쉬운 한국어 응답 규칙을 세션에 자동 주입 | `python3` |
| [pr-workflow](./pr-workflow/README.md) | PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종(create·review·fix), 스킬 호출 시에만 동작 | `gh`·`glab`·PR 호스트 MCP 중 1종 |
| [plan-workflow](./plan-workflow/README.md) | 이슈 여러 개를 분류해 한 결정씩 합의하고 이슈별 계획 승인 뒤 실행까지 잇는 planning·execute 스킬, 기록은 `.ai-docs/workspace/{이슈 키}/` | `python3`, `git` |
| [auto-flow](./auto-flow/skills) | Jira 계획과 개발·PR 리뷰, 시나리오 실행, 목표 판정, 원인 조사를 각각 호출 | 지정 조건과 판본. Jira·PR 조회나 게시에는 대상 호스트 연결 필요 |
| [agent-wiki](./agent-wiki/README.md) | 에이전트 위키 | `git`, `python3` |


### auto-flow 직접 호출

| 요청 | 스킬 | 인계할 근거 |
| --- | --- | --- |
| Jira 계획 작성·조정 / 레포 실행 가능성 검토 / 독립 착수 판정 | `plan-issue` / `review-repo` / `verify-plan` | 원래 요청, 계획 판본과 조건, 적용 계약·코드 |
| 조건 구현 / 수용한 지적 수정 | `change-code` | 조건별 착수 근거 또는 PR head·스레드별 수용 판정 |
| 지정 변경 테스트 | `test-repo` | 커밋 또는 식별 가능한 작업 사본, 조건·환경 |
| PR 생성 / 기존 PR에 수정본 게시 | `publish-pr` | 준비한 변경, 대상 브랜치 또는 기존 PR, Jira·검증 근거 |
| 코드 결함 리뷰·재리뷰 | `review-code` | PR과 검토할 head, 적용 계약 |
| 지적별 판정 / 처리 결과 답글 | `triage-findings` / `reply-thread` | PR·스레드와 현재 판본. 수정 회신에는 PR의 수정 판본·위치, 이미 해결된 지적에는 현재 코드 위치, 이견에는 판단 근거 |
| 시나리오 실행 | [run-scenario](./auto-flow/skills/run-scenario/SKILL.md) | 진입점, 입력·기대 결과, 환경과 서비스별 실행 판본 |
| 완료 조건 판정 | [review-goal](./auto-flow/skills/review-goal/SKILL.md) | Jira 계획 판본과 조건, 이미 수집된 산출물·실행 증거 |
| 원인 조사 | [investigate-cause](./auto-flow/skills/investigate-cause/SKILL.md) | 제보 원문과 확보한 단서. 이슈·계획 작성 전에도 증상과 판본으로 시작 |

예를 들어 사람이 만든 PR을 리뷰할 때는 Claude에서 `/auto-flow:review-code`에 PR을 지정한다. 게시까지 요청하면 검토한 커밋에 결과를 남긴다. Jira 계획 양식과 판본 확인법은 [계획과 검토 결과](./auto-flow/references/plan-record.md)에 있다.

## Codex 설치

로컬에서 검증한 개발 경로는 저장소 루트에서 다음 두 플러그인을 설치합니다.

~~~bash
codex plugin marketplace add .
codex plugin add auto-flow@my-claude-plugin-market
codex plugin add agent-wiki@my-claude-plugin-market
~~~

새 세션에서 `$` 선택기로 표의 스킬을 지정합니다. 위키 색인에서 적용할 정책 판본을 찾고, `plan-issue`로 계획을 작성한 뒤 `review-repo`와 `verify-plan`으로 조건별 착수 범위를 확인합니다. 변경·테스트·PR 리뷰를 마친 판본에서 `run-scenario`로 실행한 결과는 `review-goal`에 넘깁니다. 예를 들어 화면 연동 증거가 빠졌으면 실행 담당이 그 화면에서 다시 수집하고, 기대와 다른 응답이나 화면을 관찰했으면 조사 담당이 그 기록과 판본을 받습니다. [합성 상점에서 확인한 판정과 인계](.devcenter/workspace/progress/auto-flow-runtime/validation.md)

다른 플러그인도 함께 쓰려면 같은 마켓에서 원하는 패키지를 추가합니다.

~~~bash
codex plugin add better-communication@my-claude-plugin-market
codex plugin add pr-workflow@my-claude-plugin-market
codex plugin add plan-workflow@my-claude-plugin-market
~~~

변경이 원격에 게시된 뒤에는 첫 명령 대신 다음 Git 소스를 등록할 수 있습니다.

~~~bash
codex plugin marketplace add argon1025/my-claude-plugin-market
~~~

새 세션을 열고 CLI의 /hooks 또는 데스크톱의 Hooks 설정에서 번들 훅을 검토·신뢰합니다. 설치만으로 훅이 실행되지는 않습니다. 스킬은 $ 선택기 또는 /skills에서 플러그인 이름을 확인해 선택합니다. Claude 전용 /플러그인:스킬 명령을 Codex에 그대로 입력하지 않습니다.

agent-wiki의 init·register·update는 명시 호출 전용입니다. add는 자료 반영 요청으로 자동 선택될 수 있습니다. PR 호스트 도구와 위키 인증은 기존 환경의 것을 사용하며 플러그인에 자격 증명을 넣지 않습니다.

업데이트는 codex plugin marketplace upgrade my-claude-plugin-market 뒤 필요한 플러그인을 다시 codex plugin add하고 새 세션에서 확인합니다. 로컬 소스는 원본 수정 뒤 add로 캐시를 갱신합니다. 스크립트 변경 시 훅 재검토가 필요할 수 있습니다.

## 호환성과 검증

- Claude는 .claude-plugin/plugin.json, Codex는 .codex-plugin/plugin.json을 사용하며 skills·references·scripts는 공유합니다.
- Codex CLI 0.166.0에서 루트 portable plugin.json이 있으면 훅이 누락되는 현상을 재현해, 이 배포에는 루트 manifest를 두지 않습니다. CLI 버전이 바뀌어도 실제 hooks/list 또는 /hooks로 등록을 확인한 뒤 형식을 변경합니다.
- 계획 플러그인의 훅은 두 클라이언트 모두 SessionStart만 사용합니다. 계획 승인과 스냅샷은 공통 planning 스킬이 담당하며, 도구 호출이나 계획 모드 전환을 사용자 승인으로 판정하지 않습니다.
- hooks·git·bash·python3가 있는 로컬 실행 환경이 대상입니다. Cloud·웹과 Windows 셸 호환성은 검증 범위 밖입니다.
- 자동 검사: python3 -m unittest discover -s tests -p 'test_*.py'
- 실제 Codex 로더 검사(모델 호출 없음): python3 tests/check_codex.py
- `agent-wiki`와 `auto-flow`만 설치한 로더는 `python3 tests/check_codex.py --auto-flow-only`로 확인합니다. [단독 호출과 복구 검증 기록](.devcenter/workspace/progress/auto-flow-development/plan.md#검증)에서 사용한 판본과 모의 호스트 범위를 볼 수 있습니다.
- 실제 클라이언트 검증과 한계는 [검증 기록](.ai-docs/workspace/codex-plugin-support/validation.md)에 있습니다. 설치 성공을 전체 업무·원격 게시 성공으로 간주하지 않습니다.

## 라이선스

[MIT](./LICENSE)
