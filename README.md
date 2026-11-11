# my-claude-plugin-market

argon1025의 개인 Claude Code·Codex 플러그인 마켓플레이스입니다.

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install better-communication@my-claude-plugin-market
/plugin install pr-workflow@my-claude-plugin-market
/plugin install plan-workflow@my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [better-communication](./better-communication/README.md) | 간결하고 이해하기 쉬운 한국어 응답 규칙을 세션에 자동 주입 | `python3` |
| [pr-workflow](./pr-workflow/README.md) | PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종(create·review·fix), 스킬 호출 시에만 동작 | `gh`·`glab`·PR 호스트 MCP 중 1종 |
| [plan-workflow](./plan-workflow/README.md) | 항목별 요구사항 인터뷰·합의 후 계획 승인·별도 실행을 제공하는 planning·execute 스킬, 기록은 `.ai-docs/workspace/{slug}/` | `python3`, `git` |
| [agent-wiki](./agent-wiki/README.md) | 에이전트 위키 | `git`, `python3` |


## Codex 설치

Codex CLI 또는 데스크톱 앱에서 사용합니다. 로컬 개발판은 먼저 저장소 루트에서 등록합니다.

~~~bash
codex plugin marketplace add .
codex plugin add better-communication@my-claude-plugin-market
codex plugin add pr-workflow@my-claude-plugin-market
codex plugin add plan-workflow@my-claude-plugin-market
codex plugin add agent-wiki@my-claude-plugin-market
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
- 계획 플러그인의 Codex 훅은 SessionStart만 사용합니다. 최종 승인·스냅샷·인계는 공통 planning 스킬이 담당하며, 도구 호출을 사용자 승인으로 판정하지 않습니다.
- hooks·git·bash·python3가 있는 로컬 실행 환경이 대상입니다. Cloud·웹과 Windows 셸 호환성은 검증 범위 밖입니다.
- 자동 검사: python3 -m unittest discover -s tests -p 'test_*.py'
- 실제 Codex 로더 검사(모델 호출 없음): python3 tests/check_codex.py
- 실제 클라이언트 검증과 한계는 [검증 기록](.ai-docs/workspace/codex-plugin-support/validation.md)에 있습니다. 설치 성공을 전체 업무·원격 게시 성공으로 간주하지 않습니다.

## 라이선스

[MIT](./LICENSE)
