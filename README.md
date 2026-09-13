# my-claude-plugin-market

argon1025의 개인 Claude Code 플러그인 마켓플레이스입니다.

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install better-communication@my-claude-plugin-market
/plugin install pr-workflow@my-claude-plugin-market
/plugin install plan-workflow@my-claude-plugin-market
```

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [better-communication](./better-communication/README.md) | 산출물 작성 규약(보고 골격·항목 구조·문장 문체)을 세션 시작 시 자동 주입 | `python3` |
| [pr-workflow](./pr-workflow/README.md) | PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종(create·review·fix), 스킬 호출 시에만 동작 | `gh`·`glab`·PR 호스트 MCP 중 1종 |
| [plan-workflow](./plan-workflow/README.md) | 의도 확인·계획 스냅샷·작업 기록 규약과 현재 브랜치 기록을 세션 시작 시 자동 주입 + planning·execute 스킬 2종, 기록은 `.ai-docs/workspace/{slug}/` | `python3`, `git` |

## 라이선스

[MIT](./LICENSE)
