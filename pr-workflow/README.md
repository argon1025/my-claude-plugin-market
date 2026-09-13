# pr-workflow

PR 생성·AI 코드리뷰·리뷰 반영 스킬 3종을 제공하는 플러그인입니다. 훅이 없어 스킬을 호출할 때만 동작합니다.

| 스킬 | 트리거 예 | 역할 |
|---|---|---|
| `/pr-workflow:create` | "PR 생성", "PR 올려줘" | 브랜치 diff에서 배경을 도출해 4절 본문(개요·작업 내역·영향도·검증 결과)을 초안하고, 승인 1회 후 push와 PR 생성을 함께 처리함 |
| `/pr-workflow:review` | "PR 리뷰해줘", PR URL 제시 | PR 스냅샷을 파일별로 리뷰하고 반증 패스를 거쳐 Blocker/Bug/개선으로 판정하며, 승인 후에만 코멘트를 게시함 |
| `/pr-workflow:fix` | "리뷰 반영", "코멘트 반영" | 미해결 코멘트를 수용/기각/이미 해결로 판정받고, 수정 커밋 후 승인 1회 더로 push와 스레드별 답글을 처리함 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install pr-workflow@my-claude-plugin-market
```

## 전제 조건

- **PR 호스트 도구**: `gh` CLI(GitHub), `glab` CLI(GitLab), PR 호스트 MCP 도구 중 1종이 세션에 있어야 하며, `git remote` URL로 호스트를 판별해 해당 도구를 사용함
- **저장소 체크아웃**: 대상 저장소의 체크아웃 안에서 실행해야 하며, review와 fix는 로컬 git 이력으로 diff를 조달함

## 동작 방식

- **승인 게이트**: 스킬당 한 라운드의 외부 쓰기(push·PR 생성·코멘트 게시)를 한 묶음으로 모아 한 번만 승인받으며, 승인 전에는 `git fetch`만 허용함
- **배경 게이트**: create는 diff에서 도출할 수 없는 배경을 창작하지 않고 후보를 제시해 묻고, 얻지 못하면 PR을 만들지 않음
- **리뷰 룰**: 스택을 감지해 `references/checklists/`의 공통·TypeScript/React·NestJS·Java/Spring 체크리스트를 서브에이전트에 절대 경로로 전달함
- **상태 저장**: review와 fix 사이의 상태는 `[AI 리뷰]`·`[AI 코드리뷰]`·`[AI 반영]` 접두사의 PR 코멘트에만 두며, 재리뷰는 직전 요약의 스냅샷 SHA로 변경 파일만 다시 봄
- **금지 행동**: PR approve·decline·merge 호출, force-push, 검증 실패 후 push

## 방법론 출처

리뷰 방법론은 [alibaba/open-code-review](https://github.com/alibaba/open-code-review)의 프롬프트 전략을 이식한 것입니다.

- **파일별 독립 리뷰**: 파일 1개 = 서브에이전트 1개, 다른 파일의 발견은 코멘트 금지(Strict Focus)
- **반증 필터**: 리뷰 후 도구 없는 서브에이전트가 diff만 보고 틀렸다고 확인 가능한 발견만 제거함
- **정밀도 우선**: 재현율을 희생하더라도 노이즈 코멘트보다 놓침을 감수함
