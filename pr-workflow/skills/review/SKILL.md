---
name: review
description: Use when reviewing a pull request ("PR 리뷰", "PR 리뷰해줘", PR URL 제시) — PR from the open list or a pasted URL, per-file review (버그·사이드이펙트 중심) with stack checklists and a falsify pass, Korean findings graded Blocker/Bug/개선, comments posted only after approval; a re-run re-checks its own prior comments first. Reviewer only — applying comments is /pr-workflow:fix's job. NOT for the local working diff (that is /code-review's job). Run inside the target repo's checkout.
---

## 계약 로드

- `${CLAUDE_PLUGIN_ROOT}/references/pr-protocol.md` — 사전 조건, 저장소·PR 좌표, 승인 게이트, 보고 필수 항목
- `${CLAUDE_PLUGIN_ROOT}/references/review-comment.md` — 코멘트 접두사와 요약 상태 줄
- **페이로드**: 해당 단계에서만 읽음. `${CLAUDE_PLUGIN_ROOT}/references/checklists/*.md`(서브에이전트 전용), `${CLAUDE_PLUGIN_ROOT}/references/subagent-prompts.md`(①리뷰 ②반증 ③재앵커)

## 가드레일

- **승인 후 게시**: 명시 승인 전에는 게시하지 않으며, 코드를 수정하지 않는 리뷰 전용임
- **스냅샷 대상**: 리뷰 대상은 PR 스냅샷(`$REVIEW_SHA`)이고 git 부작용은 `git fetch`만 허용함
- **Strict Focus**: 파이프라인 불변식이며 다른 파일의 발견을 되살리지 않음
- **동일 저장소**: 다른 저장소의 PR은 거절하고 그 체크아웃을 안내함
- **오류 원문**: PR·인증·도구 오류는 원문을 보고하고 중단함
- **무단 생략 금지**: 스킵·절단·앵커 강등·반증 제외를 전부 보고함

## 1. PR·스냅샷 확정

`pr-protocol.md`로 좌표와 PR 번호를 확정하고 호스트 도구로 소스·베이스 브랜치, 상태, 기존 코멘트를 조회합니다.

- **로컬 diff**: `git fetch <remote> <source-branch>` 후 `REVIEW_SHA=FETCH_HEAD`, `BASE`는 페치한 베이스 브랜치와의 merge-base
- **폴백**: 페치 실패, MERGED, DECLINED는 호스트 도구의 PR diff를 사용하고, 절단된 경우 누락 파일을 미리뷰로 보고함
- **파일 목록**: `git diff --find-renames --name-status $BASE $REVIEW_SHA`, 파일별 hunk는 `-- <path>`, 스냅샷은 `git show $REVIEW_SHA:<path>`

## 2. 범위 결정

- **스킵**: 바이너리·이미지·폰트, lockfile, 순수 삭제·개명, 요청 없는 `*.md`, 변경 1,500라인 초과 파일(스킵 후 경고)을 사유와 함께 스킵 표에 적음. 테스트 파일은 리뷰함
- **30파일 초과**: 범위를 먼저 물음
- **델타 스코핑**: 직전 `[AI 코드리뷰]` 요약의 `리뷰 스냅샷: <SHA>`가 있으면 `git diff --name-only <그 SHA> $REVIEW_SHA`의 파일만 팬아웃하고 나머지는 "직전 리뷰 이후 변경 없음"으로 보고함. 요약이 없거나 SHA에 도달할 수 없으면 전체를 리뷰함
- **KNOWN_ISSUES**: AI·사람을 불문하고 코멘트가 있는 파일·주제를 `{KNOWN_ISSUES}`로 묶어 서브에이전트에 전달함

## 3. 적용 룰 결정

- **스택 감지**: 저장소당 1회. 모든 파일에 `checklists/common.md`를 적용하고, `.ts/.tsx/.js/.jsx`는 가장 가까운 `package.json` deps에 react·next가 있으면 `typescript-react.md`, `@nestjs/core`가 있으면 `nestjs.md`를, `.java/.kt`는 `java-spring.md`를 더함
- **절대 경로**: `${CLAUDE_PLUGIN_ROOT}/references/checklists/<name>.md`를 절대 경로로 1회 확장해 `{CHECKLIST_PATHS}`로 전달함
- **보고**: "적용 룰 소스" 헤더에 감지한 스택과 적용 체크리스트를 항상 기재함

## 4. 리뷰

변경 150라인 이하이고 3파일 이하면 같은 스키마와 같은 반증 단계로 직접 1패스합니다. 그 외에는 파일 1개당 general-purpose 서브에이전트 1개, 배치당 최대 5개로 템플릿 ①을 사용해 팬아웃합니다.

## 5. 반증

- **입력**: 발견 사항과 관련 hunk. 서브에이전트는 도구 없이 실행함
- **분할**: 발견 10건 이하면 템플릿 ② 1회, 초과 시 파일별로 나눔. 발견 0건이면 생략함
- **순서**: 앵커링 전에 실행함. 여기서 떨어진 발견은 재앵커 호출 비용을 쓰지 않음. 제외 건수를 보고함

## 6. 앵커

1. `git show $REVIEW_SHA:<path>`에서 `existing_code` 첫 줄을 `grep -nF`로 찾고, 추가 라인 범위 안의 매치만 인정함(복수 매치는 `line_hint`에 가장 가까운 것)
2. 실패 시 템플릿 ③으로 재앵커 1회
3. 그래도 없으면 `anchor 미확정` 표시의 파일 레벨 코멘트로 강등함

diff 밖에는 앵커하지 않습니다.

## 7. 재리뷰 판정

`[AI 리뷰` 코멘트가 없으면 생략합니다. 있으면 각 이전 발견을 `$REVIEW_SHA`에서 해결 / 미해결 / 판정불가로 판정합니다. 반박이 달린 스레드는 근거를 다시 검토해(도구가 필요하면 서브에이전트) 근거와 함께 유지하거나 철회합니다. "N번 다시 봐줘" 요청도 이 단계에서 처리하며, 게시 게이트 앞에 두어 한 실행에 게이트가 한 번만 열리게 합니다.

## 8. 중복 제거·보고

파일·라인 ±2·주제가 기존 코멘트(AI·사람)와 일치하는 발견은 "기존 코멘트와 중복"으로 표시하고 제외합니다.

- **적용 룰 소스**: 감지 스택과 적용 체크리스트
- **등급 절**: Blocker · Bug · 개선. 건별로 `<등급 이모지> **<title>** — `파일:라인` [구분/등급] 규칙·출처` 다음에 제안 1줄과 상세 근거
- **표·건수**: 요약표(파일 | 건수 | 구분 | 최고 등급), 스킵 표, 반증 N건, 중복 N건, 재리뷰 판정
- **권장**: `권장:` 머지 가부 1줄. 의견이며 승인 버튼은 누르지 않음

## 9. 승인 1회·게시

"게시 범위 — 전체 / Blocker·Bug만 / 안 함"을 한 번 묻고, 그 답 하나로 새 인라인 코멘트·7절 답글·요약 코멘트를 함께 처리합니다.

- **양식**: `review-comment.md`. 요약의 `리뷰 스냅샷` 줄은 다음 실행의 입력이므로 생략 불가
- **답글**: 이전 발견 스레드에 답글로 붙임. 해결이면 "해결 확인했습니다", 미해결이면 남은 이유 1줄, 철회면 정정 문장
- **앵커 오류**: API 오류 시 앵커 없이 1회 재시도하고 보고함

## 10. 핸드오프

- **발견 잔존**: 한 줄 `다음 단계: /pr-workflow:fix로 반영`
- **종료 조건**: 이전 `[AI 리뷰]` 발견이 전부 해결이거나 기각이 수용되고 새 Blocker·Bug가 없을 때 review↔fix 루프가 끝남
- **교착**: 3회차에도 수용·기각이 갈리는 항목은 4회차로 가지 않고 양측 근거와 함께 사용자에게 넘김
