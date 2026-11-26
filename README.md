# my-claude-plugin-market

argon1025의 개인 Claude Code·Codex 플러그인 마켓플레이스입니다.

## Claude Code 설치

저장소 루트에서 마켓을 등록하고 이슈 루프와 위키 플러그인 두 개를 설치합니다.

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
| [auto-flow](./auto-flow/README.md) | 이슈 하나를 검토중·검토완료·개발완료·완료 순서로 진행하며 계획은 이슈 본문에, 구현 결과와 리뷰는 PR에 기록하는 스킬 7종(create-issue·run-issue·plan-issue·resolve-issue·fix-issue·close-issue·review-issue), 스킬 호출 시에만 동작 | 이슈·PR 호스트 도구(MCP, `gh`, `glab` 등), `git` |
| [agent-wiki](./agent-wiki/README.md) | 에이전트 위키 | `git`, `python3` |


auto-flow는 plan-workflow와 pr-workflow를 설치하지 않은 상태에서 씁니다. plan-workflow의 세션 훅은 계획을 저장소의 `plan.md`에 기록하라고 주입하고, 두 플러그인의 스킬은 같은 요청 문장에 auto-flow의 스킬과 함께 반응합니다. 두 플러그인은 기존 사용자를 위해 그대로 둡니다.

## 이슈 루프

auto-flow는 이슈 하나를 검토중, 검토완료, 개발완료, 완료 순서로 진행합니다. 계획과 진행은 이슈 본문에, 구현 결과와 리뷰는 PR에 기록하므로 다음 실행자는 사람이든 봇이든 이슈와 PR만 읽고 이어 갑니다. 본문 첫 줄의 상태가 누가 본문을 고칠 차례인지를 정하고, 스킬은 자기 상태가 아닌 이슈를 고치지 않습니다. 사람을 기다리는 지점은 미결 사항의 답, 사용자가 하는 단계, PR 머지, 사람이 확인하기로 한 완료 조건 네 곳입니다.

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [create-issue](./auto-flow/skills/create-issue/SKILL.md) | 받은 요청을 이슈로 등록할 때 | 같은 요청의 열린 이슈가 있으면 그 이슈를 알리고, 없으면 템플릿을 적용한 이슈를 만들어 요청 한 줄, 담당자, 관련 자료의 링크를 채운 뒤 멈춥니다. 원하는 결과가 불분명하면 만들지 않고 요청자에게 물을 질문을 돌려줍니다. 결함 제보에서 빠진 정보는 미결 사항에 적습니다. |
| [run-issue](./auto-flow/skills/run-issue/SKILL.md) | 이슈 하나를 한 세션에서 이어 갈 때 | 검토중이면 계획을 쓰고 미결 사항을 세션에서 하나씩 묻습니다. 검토완료면 "진행" 표의 순서대로 구현해 PR을 올리다가 사람을 기다리는 지점에서 멈춥니다. 리뷰는 하지 않습니다. |
| [plan-issue](./auto-flow/skills/plan-issue/SKILL.md) | 검토중인 이슈의 계획을 세우거나 미결 사항의 답을 반영할 때 | 요청을 번호 붙인 완료 조건으로 쓰고, 누가 어떤 순서로 무엇을 하는지와 모든 레포의 계획을 씁니다. 사람의 판단이 필요한 결정은 미결 사항에 적고 멈추며, 미결 사항이 없어지면 검토완료로 바꿉니다. |
| [resolve-issue](./auto-flow/skills/resolve-issue/SKILL.md) | 검토완료인 이슈를 구현할 때 | 계획이 지금도 맞는지 확인하고, "진행" 표의 다음 행을 구현·검증한 뒤 승인 없이 PR을 올립니다. 사람이 직접 할 일은 무엇을 어떤 순서로 실행하는지 적어 요청합니다. 계획이 맞지 않으면 미결 사항에 행을 더해 검토중으로 되돌리고, 마지막 행 뒤 개발완료로 바꿉니다. |
| [fix-issue](./auto-flow/skills/fix-issue/SKILL.md) | 열린 PR에 코멘트가 달렸을 때 | 변경을 요구하는 의견을 이슈와 PR 본문의 맥락, 코드로 검토해 고치거나 이유를 적어 고치지 않고, 그 코멘트에 답합니다. 이슈 본문은 고치지 않습니다. |
| [close-issue](./auto-flow/skills/close-issue/SKILL.md) | 개발완료인 이슈를 마무리할 때 | PR의 머지와 사람의 확인을 본문에 반영하고, 모두 끝났으면 완료로 바꿉니다. 리뷰와 코멘트는 보지 않습니다. |
| [review-issue](./auto-flow/skills/review-issue/SKILL.md) | 한 레포의 PR 리뷰를 직접 요청할 때 | 코드, 완료 조건과 계획, PR 본문의 기록이 사실인지를 점검해 지적을 PR 코멘트로 남깁니다. 다른 스킬이 부르지 않습니다. |

직접 쓸 때는 `run-issue` 하나로 검토와 개발을 이어 갑니다. 봇에게 맡길 때는 계획 봇에 `plan-issue`, 개발 봇에 `resolve-issue`, 수정 봇에 `fix-issue`, 정리 봇에 `close-issue`를 주고 각자의 주기로 돌립니다. 봇끼리 일을 넘기지 않고, 본문의 상태 줄이 차례를 정합니다. 이슈·PR·대화 도구와 담당자를 찾는 곳처럼 환경마다 다른 것은 [환경 문서](./auto-flow/references/environment.md) 한 장에 있으며, 이 배포판의 값은 GitHub 기준입니다. 어떤 이슈를 고를지와 실행 주기는 봇의 지침에 둡니다. 호출 예와 봇 구성은 [auto-flow 안내](./auto-flow/README.md)에, 이슈 본문의 형식은 [이슈 템플릿](./auto-flow/references/issue-template.md)에 있습니다.

## agent-wiki · 정책과 저장소 지식

이슈에는 그 이슈의 진행을 두고 위키에는 여러 이슈에서 다시 쓸 정책·계약·프로젝트 지식을 둡니다. 이슈 루프는 위키를 계획과 리뷰의 근거로 읽기만 합니다. 확정된 결정은 `add`를 따로 호출해 위키에 반영하고, 머지된 코드의 반영은 `update`의 정기 실행에 맡깁니다.

| 스킬 | 언제 호출하는가 | 한 번의 호출 결과 |
| --- | --- | --- |
| [init](./agent-wiki/skills/init/SKILL.md) | 설정한 원격 위키를 처음 준비하거나 로컬 사본을 동기화할 때 | 빈 원격에는 골격을 만들고, 로컬 읽기 전용 사본을 원격 기준 브랜치에 맞춥니다. |
| [register](./agent-wiki/skills/register/SKILL.md) | 현재 저장소를 위키에 등록하거나 의존 관계를 다시 조사할 때 | 코드에서 확인한 저장소 정보와 의존 관계를 위키의 레포 지도에 반영합니다. |
| [add](./agent-wiki/skills/add/SKILL.md) | 규격이나 확정된 결정을 받았을 때 | 출처와 적용 대상을 확인해 공통 정책이나 프로젝트 지식으로 위키 기준 브랜치에 바로 반영합니다. PR은 만들지 않습니다. |
| [update](./agent-wiki/skills/update/SKILL.md) | 미처리 머지를 확인하거나 특정 주제를 직접 점검하거나 도메인을 정기 점검할 때 | 기본 호출은 미처리 머지를, `--topic`은 지정 주제를 점검합니다. `--periodic`은 머지·결정·위키 변경과 코드·문서 순회 결과를 함께 점검합니다. 반영할 내용이 있으면 위키 PR로 제안합니다. |

## Codex 설치

저장소 루트에서 다음 두 플러그인을 설치합니다.

~~~bash
codex plugin marketplace add .
codex plugin add auto-flow@my-claude-plugin-market
codex plugin add agent-wiki@my-claude-plugin-market
~~~

새 세션에서 `$` 선택기로 auto-flow의 스킬을 고르고 이슈 키를 함께 적습니다. 예를 들어 `run-issue`를 고른 뒤 `ABC-123 진행해줘`라고 적습니다.

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
- `agent-wiki`와 `auto-flow`만 설치한 로더는 `python3 tests/check_codex.py --auto-flow-only`로 확인합니다. 이슈 루프의 절차는 과거에 해결된 실제 이슈 넷으로 가상 실행해 점검했으며, 결과는 [계획 기록](.devcenter/workspace/progress/issue-loop-rearchitecture/plan.md)의 `확인한 사실`에 있습니다.
- 실제 클라이언트 검증과 한계는 [검증 기록](.ai-docs/workspace/codex-plugin-support/validation.md)에 있습니다. 설치 성공을 전체 업무·원격 게시 성공으로 간주하지 않습니다.

## 라이선스

[MIT](./LICENSE)
