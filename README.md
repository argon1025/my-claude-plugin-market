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


## 권장 에이전트 봇 구성

초기에는 **Teams 응대 봇 1개, PM 봇 1개, 독립 리뷰 봇 1개와 담당 저장소마다 레포 봇 1개**를 권장합니다. 예를 들어 화면과 API가 별도 저장소라면 두 레포 봇을 둡니다. 화면과 BFF가 한 저장소에 있으면 같은 레포 봇이 두 경로를 함께 봅니다.

| 봇 | 맡길 일 | 다음 담당자가 이어받을 근거 |
| --- | --- | --- |
| Teams 응대 봇 | 원래 대화에서 요청과 정정을 확인하고 개발 요청을 Jira에 연결합니다. 요청자나 계약 소유자의 회신을 받아 전달하고, 문의자가 기다린 결과를 안내합니다. | 원래 메시지, 연결한 Jira 키, 질문·회신·안내 메시지 위치 |
| PM 봇 | Jira에 이슈 전체의 계획 하나를 유지합니다. 조건별로 일을 배정하고, 초기 구성에서는 PR 병합과 배포 확인, Jira 상태 갱신까지 맡습니다. | 계획 판본과 조건 번호, 담당자에게 전달한 위치, 실제 병합·배포·전환 기록 |
| 레포 봇 | 담당 저장소에서 조사·구현·테스트·PR 수정을 맡습니다. 여러 서비스가 얽힌 시나리오는 Jira 계획에서 지정한 진입점의 레포 봇이 실행합니다. | 커밋 또는 식별 가능한 작업 사본, PR·스레드, 실행 환경과 관찰 결과 |
| 독립 리뷰 봇 | 계획이 목표의 성공·실패를 가릴 수 있는지, PR의 최신 커밋에 결함이 있는지, 실행 증거가 완료 조건을 충족하는지를 각각 판정합니다. | 검토한 계획·커밋과 조건별 판정, 지적 위치 또는 부족한 근거 |

이 구성은 스킬의 **권장 담당**입니다. 사람도 대상과 근거를 주고 한 스킬만 호출할 수 있습니다. 담당자를 바꿀 때는 이슈·조건, 확인할 판본, 결과를 찾을 위치와 남은 일만 넘깁니다. 독립 검토는 해당 계획이나 코드를 작성한 담당과 분리합니다.

## 스킬별 사용 안내

아래 표는 권장 담당별로 묶었습니다. 각 행은 한 번의 독립 호출입니다. 예를 들어 사람이 만든 PR의 결함만 보고 싶으면 Claude Code에서 `/auto-flow:review-code`에 PR을 지정합니다. Codex에서는 스킬 선택기에서 같은 플러그인의 `review-code`를 선택합니다. 리뷰 게시까지 요청하면 검토한 커밋에 결과를 남깁니다.

### Teams 응대 봇 · 접수와 회신

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [classify-inquiry](./auto-flow/skills/classify-inquiry/SKILL.md) | 문의 원문과 후속 정정을 보고 어떤 요청인지 알고 싶을 때 | 일반 문의·원인 조사·명시적 개발 요청을 구분하고 판단 근거와 요청자가 기다리는 결과를 반환합니다. |
| [answer-inquiry](./auto-flow/skills/answer-inquiry/SKILL.md) | 정책이나 현재 동작에 관한 질문에 답할 때 | 확인한 출처로 원래 대화에 답하고 회신 위치를 반환합니다. 정책만 확인했으면 배포 여부는 미확인으로 밝힙니다. |
| [link-issue](./auto-flow/skills/link-issue/SKILL.md) | 개발 요청이나 같은 조건의 QA 재제보를 Jira에서 추적할 때 | 같은 요청·완료 조건의 이슈를 찾아 원문을 연결하고, 없으면 생성합니다. 이슈 키와 반영한 링크·라벨을 반환합니다. |
| [send-question](./auto-flow/skills/send-question/SKILL.md) | 요청 의도나 서비스 계약을 결정할 사람에게 물어야 할 때 | 요청자나 계약 소유자에게 미결 질문을 보내고, 질문 위치와 답을 기다리는 조건을 반환합니다. 기술 근거는 해당 레포 담당자끼리 직접 확인할 수 있습니다. |
| [handoff-reply](./auto-flow/skills/handoff-reply/SKILL.md) | 원래 질문에 답이 도착했을 때 | 응답자·출처·확정 범위와 남은 질문을 계획 담당자에게 전달합니다. Jira 계획 반영은 PM이 맡습니다. |
| [find-notifications](./auto-flow/skills/find-notifications/SKILL.md) | 지금 어느 문의에 어떤 결과를 안내할 수 있는지 조회할 때 | 새 머지가 없어도 대기 문의를 확인해 안내할 대화·판본·근거 또는 대기 이유를 반환합니다. |
| [send-result](./auto-flow/skills/send-result/SKILL.md) | 확인된 결과를 원래 문의자에게 보내거나 실패한 전송만 복구할 때 | 기존 안내를 확인하고 빠진 결과만 보낸 뒤 메시지 위치를 반환합니다. QA 가능 안내에는 배포 환경과 버전을 명시합니다. |

### PM 봇 · 계획과 운영

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [plan-issue](./auto-flow/skills/plan-issue/SKILL.md) | 처음 계획을 세우거나 확정된 답·정책으로 범위를 조정할 때 | 원래 요청을 보존하면서 Jira 본문의 계획을 갱신하고, 달라진 조건과 영향 범위를 반환합니다. 사본만 있으면 초안을 반환합니다. |
| [check-progress](./auto-flow/skills/check-progress/SKILL.md) | 어느 조건이 어디서 기다리는지 확인할 때 | 이슈·PR·배정처·검증 근거를 읽어 완료·대기·재개 가능한 일을 반환합니다. 사내에서 키를 주면 한 건, 입력이 없으면 추적 라벨이 붙은 미완료 건을 조회합니다. |
| [assign-work](./auto-flow/skills/assign-work/SKILL.md) | 특정 조건을 맡기거나 기존 담당자에게 정책 변경을 알릴 때 | 대상·판본·작업 범위를 실제 수신처에 전달하고 인계 위치를 반환합니다. |
| [check-merge](./auto-flow/skills/check-merge/SKILL.md) | 지금 이 PR을 병합할 수 있는지만 확인할 때 | 현재 커밋의 독립 리뷰·필수 사전 검증·차단 지적 해소·필수 승인을 조회해 가능 여부와 사유를 반환합니다. |
| [merge-pr](./auto-flow/skills/merge-pr/SKILL.md) | 요청과 계획에 포함된 PR 병합을 실행할 때 | 실행 직전 커밋과 네 조건을 다시 확인합니다. 자동 방식은 병합 결과를, 사람 방식은 요청 위치와 실제 병합 여부를 반환합니다. |
| [check-deployment](./auto-flow/skills/check-deployment/SKILL.md) | 특정 서비스의 변경을 QA 등 지정 환경에서 검증할 수 있는지 확인할 때 | 필요한 커밋을 포함한 배포 기록이나 담당자의 회신을 대조해 서비스별 환경·버전·근거 또는 대기 위치를 반환합니다. |
| [update-status](./auto-flow/skills/update-status/SKILL.md) | 완료 조건별 판정에 맞춰 Jira 상태를 바꿀 때 | 프로젝트가 허용한 전환을 적용하고 실제 상태를 확인합니다. 모든 PR이 병합됐어도 필수 QA 판정이 남아 있으면 기다립니다. |

### 레포 봇 · 조사와 개발

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [investigate-cause](./auto-flow/skills/investigate-cause/SKILL.md) | 계획 수립 전이나 검증 실패 후에 증상의 원인을 조사할 때 | 제보·환경·판본을 따라 확인한 원인과 근거를 반환합니다. 원인을 특정하지 못하면 가설을 구별할 다음 관찰을 남깁니다. |
| [review-repo](./auto-flow/skills/review-repo/SKILL.md) | Jira 계획의 특정 조건을 내 저장소에서 구현할 수 있는지 검토할 때 | 실제 호출 경로와 소비자를 따라 변경 위치, 계약 충돌, 추가로 필요한 레포와 검증 방법을 반환합니다. |
| [change-code](./auto-flow/skills/change-code/SKILL.md) | 착수 가능한 조건을 구현하거나 수용한 리뷰 지적만 고칠 때 | 해당 코드와 필요한 테스트 코드를 수정하고 변경 위치·판본을 반환합니다. |
| [test-repo](./auto-flow/skills/test-repo/SKILL.md) | 지정 커밋이나 사람이 준비한 미커밋 변경의 테스트만 실행할 때 | 실제 명령·환경·판본과 조건별 통과·실패·미실행 근거를 반환합니다. |
| [publish-pr](./auto-flow/skills/publish-pr/SKILL.md) | 준비한 변경을 새 PR로 제안하거나 기존 PR에 수정본을 올릴 때 | 지정 브랜치에 게시하고 호스트에서 확인한 PR 링크와 최신 커밋을 반환합니다. |
| [triage-findings](./auto-flow/skills/triage-findings/SKILL.md) | PR 리뷰 지적 중 어떤 것을 고칠지 판단할 때 | 스레드별로 수정 수용·이미 해결·근거 있는 이견을 구분합니다. 근거가 부족한 항목은 확인할 사실을 남깁니다. |
| [reply-thread](./auto-flow/skills/reply-thread/SKILL.md) | 리뷰 지적의 처리 결과를 해당 스레드에 답할 때 | 판정 근거나 PR에 게시된 수정 위치를 확인해 누락된 답글만 보내고 그 위치를 반환합니다. |
| [run-scenario](./auto-flow/skills/run-scenario/SKILL.md) | 화면·API 등 지정한 진입점에서 조건을 직접 실행할 때 | 입력·환경·서비스 판본·관찰값과 증거 위치를 반환합니다. 실제 연동·목업·API 단독 실행을 구분합니다. |

### 독립 리뷰 봇 · 착수와 완료 판정

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [verify-plan](./auto-flow/skills/verify-plan/SKILL.md) | 구현 전, 여러 레포의 계획을 합쳐도 원래 요청의 성공과 실패를 가릴 수 있는지 볼 때 | 계획 판본과 조건마다 착수 가능 여부, 보완할 계약이나 검증 방법을 반환합니다. |
| [review-code](./auto-flow/skills/review-code/SKILL.md) | PR의 최신 커밋을 리뷰하거나 수정 후 재리뷰할 때 | 해당 커밋의 버그·회귀·계약 위반을 검토해 통과 또는 지적 위치·근거와 차단 여부를 반환합니다. |
| [review-goal](./auto-flow/skills/review-goal/SKILL.md) | 수집된 실행 증거나 산출물이 Jira 완료 조건을 충족하는지 판단할 때 | 조건별로 충족·근거 부족·실제 동작 미충족을 판정합니다. 근거가 부족하면 추가 관찰을, 실패를 확인하면 조사·수정할 범위를 넘깁니다. |

### agent-wiki · 정책과 저장소 지식

초기에는 위키 설정을 설치 담당자가, 저장소 등록을 해당 레포 봇이, 확정 결정 반영과 정기 점검을 PM이 맡을 수 있습니다. Jira에는 이슈의 진행 상황을 두고 위키에는 여러 이슈에서 다시 쓸 정책·계약·프로젝트 지식을 둡니다.

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [init](./agent-wiki/skills/init/SKILL.md) | 설정한 원격 위키를 처음 준비하거나 로컬 사본을 동기화할 때 | 빈 원격에는 골격을 만들고, 로컬 읽기 전용 사본을 원격 기준 브랜치에 맞춥니다. |
| [register](./agent-wiki/skills/register/SKILL.md) | 현재 저장소를 위키에 등록하거나 의존 관계를 다시 조사할 때 | 코드에서 확인한 저장소 정보와 의존 관계를 위키의 레포 지도에 반영합니다. |
| [add](./agent-wiki/skills/add/SKILL.md) | 규격이나 확정된 결정을 받았을 때 | 출처와 적용 대상을 확인해 공통 정책이나 프로젝트 지식으로 반영할 위키 PR을 제안합니다. |
| [update](./agent-wiki/skills/update/SKILL.md) | 미처리 머지를 확인하거나 특정 주제를 직접 점검하거나 도메인을 정기 점검할 때 | 기본 호출은 미처리 머지를, `--topic`은 지정 주제를 점검합니다. `--periodic`은 머지·결정·위키 변경과 코드·문서 순회 결과를 함께 점검합니다. 반영할 내용이 있으면 위키 PR로 제안합니다. |

## 새 이슈에서 이어받기

1. 원래 문의와 요청자가 기다리는 결과를 확인합니다. 일반 질문은 답변, 원인 조사 요청은 조사 결과에서 끝냅니다. 개발 요청은 기존 Jira가 있는지 확인해 연결합니다. 이미 이슈가 있으면 키와 맡길 작업부터 지정할 수 있습니다.
2. 계획이 필요한 경우 Jira 본문에 완료 조건과 담당·검증 환경을 적습니다. 영역 검토와 독립 판정이 끝난 조건부터 맡깁니다. 정책 선택이 남으면 질문과 회신을 연결하고, 확정 정책의 위키 반영은 `agent-wiki:add`로 맡깁니다. 바뀐 조건에 의존하는 계획·검토·기존 배정만 조정합니다. [Jira 계획과 검토 양식](./auto-flow/references/plan-record.md)
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
