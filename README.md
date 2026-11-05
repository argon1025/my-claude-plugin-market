# my-claude-plugin-market

argon1025의 개인 Claude Code 플러그인 마켓플레이스입니다.

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

## 라이선스

[MIT](./LICENSE)
