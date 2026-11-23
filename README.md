# my-claude-plugin-market

argon1025의 개인 Claude Code·Codex 플러그인 마켓플레이스입니다.

## Claude Code 설치

이 체크아웃의 새 흐름은 저장소 루트에서 마켓을 등록하고 업무·위키 플러그인 두 개를 설치합니다.

```
/plugin marketplace add .
/plugin install auto-flow@my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

원격에 게시된 버전은 `/plugin marketplace add argon1025/my-claude-plugin-market`으로 등록합니다. 표의 다른 플러그인도 `/plugin install 플러그인이름@my-claude-plugin-market`으로 개별 설치할 수 있습니다.

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [better-communication](./better-communication/README.md) | 간결하고 이해하기 쉬운 한국어 응답 규칙을 세션에 자동 주입 | `python3` |
| [pr-workflow](./pr-workflow/README.md) | PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종(create·review·fix), 스킬 호출 시에만 동작 | `gh`·`glab`·PR 호스트 MCP 중 1종 |
| [plan-workflow](./plan-workflow/README.md) | 이슈 여러 개를 분류해 한 결정씩 합의하고 이슈별 계획 승인 뒤 실행까지 잇는 planning·execute 스킬, 기록은 `.ai-docs/workspace/{이슈 키}/` | `python3`, `git` |
| [auto-flow](./auto-flow/skills) | 문의·Jira 인계, 개발·독립 검증, 병합·배포 확인과 결과 안내를 각각 호출 | 지정 조건과 판본. 외부 조회·쓰기에는 해당 호스트 연결 필요 |
| [agent-wiki](./agent-wiki/README.md) | 에이전트 위키 | `git`, `python3` |


### auto-flow 직접 호출

| 요청 | 스킬 | 인계할 근거 |
| --- | --- | --- |
| 문의 분류 / 일반 문의에 회신 / Jira 등록·연결 | `classify-inquiry` / `answer-inquiry` / `link-issue` | 원래 대화와 정정. 회신은 정책·현황의 근거, 등록은 프로젝트와 같은 요청의 완료 조건 |
| 조건별 진행 확인 / 작업 배정 또는 변경 인계 | `check-progress` / `assign-work` | 이슈·계획 판본과 PR·검증·대기 근거. 배정은 담당자와 맡길 범위 |
| 질문 전달 / 답을 계획 담당자에게 인계 | `send-question` / `handoff-reply` | 미결 조건과 결정권자, 원래 질문·회신·수신처 |
| Jira 계획 작성·조정 / 레포 실행 가능성 검토 / 독립 착수 판정 | `plan-issue` / `review-repo` / `verify-plan` | 원래 요청, 계획 판본과 조건, 적용 계약·코드 |
| 조건 구현 / 수용한 지적 수정 | `change-code` | 조건별 착수 근거 또는 PR head·스레드별 수용 판정 |
| 지정 변경 테스트 | `test-repo` | 커밋 또는 식별 가능한 작업 사본, 조건·환경 |
| PR 생성 / 기존 PR에 수정본 게시 | `publish-pr` | 준비한 변경, 대상 브랜치 또는 기존 PR, Jira·검증 근거 |
| 코드 결함 리뷰·재리뷰 | `review-code` | PR과 검토할 head, 적용 계약 |
| 지적별 판정 / 처리 결과 답글 | `triage-findings` / `reply-thread` | PR·스레드와 현재 판본. 수정 회신에는 PR의 수정 판본·위치, 이미 해결된 지적에는 현재 코드 위치, 이견에는 판단 근거 |
| 시나리오 실행 | [run-scenario](./auto-flow/skills/run-scenario/SKILL.md) | 진입점, 입력·기대 결과, 환경과 서비스별 실행 판본 |
| 완료 조건 판정 | [review-goal](./auto-flow/skills/review-goal/SKILL.md) | Jira 계획 판본과 조건, 이미 수집된 산출물·실행 증거 |
| 원인 조사 | [investigate-cause](./auto-flow/skills/investigate-cause/SKILL.md) | 제보 원문과 확보한 단서. 이슈·계획 작성 전에도 증상과 판본으로 시작 |
| 병합 조건 조회 / 병합 실행·사람에게 요청 | `check-merge` / `merge-pr` | PR·대상·head와 네 조건의 원본. 실행은 병합 범위와 환경의 병합 방식 |
| 배포 확인 / 이슈 상태 갱신 | `check-deployment` / `update-status` | 서비스·변경·대상 환경 / 이슈 종료 지점, 조건별 판정과 프로젝트의 전환 기준 |
| 안내 대상 조회 / 원래 문의에 결과 전송 | `find-notifications` / `send-result` | 원래 메시지와 기다린 종료 지점, 실제 결과 판본·근거와 기존 안내 |

예를 들어 사람이 만든 PR을 리뷰할 때는 Claude에서 `/auto-flow:review-code`에 PR을 지정한다. 게시까지 요청하면 검토한 커밋에 결과를 남긴다. Jira 계획 양식과 판본 확인법은 [계획과 검토 결과](./auto-flow/references/plan-record.md)에 있다.

### 새 이슈에서 이어받기

1. 원래 문의와 요청자가 기다리는 결과를 확인합니다. 일반 질문은 답변, 원인 조사 요청은 조사 결과에서 끝냅니다. 개발 요청은 기존 Jira가 있는지 확인해 연결합니다. 이미 이슈가 있으면 키와 맡길 작업부터 지정할 수 있습니다.
2. 계획이 필요한 경우 Jira 본문에 완료 조건과 담당·검증 환경을 적습니다. 영역 검토와 독립 판정이 끝난 조건부터 맡깁니다. 정책 선택이 남으면 질문과 회신을 연결하고, 확정 정책의 위키 반영은 `agent-wiki:add`로 맡깁니다. 바뀐 조건에 의존하는 계획·검토·기존 배정만 조정합니다.
3. 맡긴 범위에 따라 변경·테스트·PR 게시와 독립 리뷰를 진행합니다. 수정이 필요하면 스레드별 판정·코드 수정·수정본 게시·최신 head 검토를 연결합니다. 실행자는 시나리오의 환경·버전·관찰을 남기고, 목표 리뷰어는 그 근거로 Jira 조건을 판정합니다.
4. 병합이 범위에 있으면 PR별로 현재 조건을 확인해 실행합니다. 필요한 환경에서만 배포를 확인합니다. 병합 뒤 QA가 가능한 작업이면 그때 연동을 검증합니다. 상태 갱신 담당은 이슈 전체의 조건별 판정에 프로젝트 전환 규칙을 적용합니다.
5. 안내 담당은 원래 문의에서 기다린 결과를 확인하고 해당 판본의 근거가 갖춰진 문의에만 전달합니다. PR 검토나 QA 가능 시점이 종료 지점이면 이슈 전체 완료 전에도 안내할 수 있습니다. 전송에 실패한 후임에게는 원래 대화와 결과 판본을 넘깁니다.

호출자는 필요한 단계만 선택합니다. 같은 봇이 두 작업을 맡아도 조회·배정과 안내 대상 확인·전송은 별개입니다. 실제 인계 위치로는 Jira 조건, PR head, 배포 기록, 원래 대화나 배정 메시지를 사용합니다. 사내 Teams·Jira·Orca·Bitbucket과 VDI, GitHub Actions에서 찾을 원본과 쓰기 방법은 [환경별 연결](./auto-flow/references/operations-environments.md)에 있습니다.

## Codex 설치

저장소 루트에서 다음 두 플러그인을 설치합니다.

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
- `agent-wiki`와 `auto-flow`만 설치한 로더는 `python3 tests/check_codex.py --auto-flow-only`로 확인합니다. 운영 스킬과 3B 판정의 인계 범위는 [AC별 모의 검증 기록](.devcenter/workspace/progress/auto-flow-operations/validation.md), 개발 스킬의 독립 호출은 [개발 경로 검증 기록](.devcenter/workspace/progress/auto-flow-development/plan.md#검증)에 있습니다.
- 실제 클라이언트 검증과 한계는 [검증 기록](.ai-docs/workspace/codex-plugin-support/validation.md)에 있습니다. 설치 성공을 전체 업무·원격 게시 성공으로 간주하지 않습니다.

## 라이선스

[MIT](./LICENSE)
