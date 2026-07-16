# my-claude-plugin-market

argon1025의 개인 Claude Code 플러그인 마켓플레이스예요.

## 설치

Claude Code에서 마켓플레이스를 등록하고 원하는 플러그인을 설치해요.

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install communication-rules@my-claude-plugin-market
/plugin install pull-request-workflow@my-claude-plugin-market
```

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [communication-rules](./communication-rules/README.md) | 사용자 대면 산출물(최종 응답·PR 본문·문서) 작성 규칙을 세션 시작 시 자동 주입 | `python3` |
| [pull-request-workflow](./pull-request-workflow/README.md) | GitHub PR 생성·AI 리뷰·리뷰 코멘트 반영 스킬 3종 | `gh` CLI 설치 + 로그인(`gh auth status`) |

### communication-rules

최종 응답, PR 본문, 문서 파일 같은 사용자 대면 산출물에 일관된 작성 규칙을 적용해요. 세션 시작 시 실질 규칙(내용 구성)과 문체 규칙을 컨텍스트로 주입하고, 매 턴마다 핵심 규칙 리마인더를 반복해요.

### pull-request-workflow

GitHub PR 워크플로를 스킬 3종으로 지원해요. 모두 `gh` CLI 기반이라 별도 MCP 서버가 필요 없어요.

- `/pull-request-workflow:create-pull-request` — 완성된 기능 브랜치로 PR 생성 (리뷰어·본문 컨벤션 자동 파악)
- `/pull-request-workflow:review-pull-request` — 파일 단위 AI 코드 리뷰 + 반증 검증, 승인 후 코멘트 게시
- `/pull-request-workflow:resolve-review-comments` — 미해결 리뷰 코멘트 트리아지·수정·답글을 배치로 처리

## 라이선스

[MIT](./LICENSE)
