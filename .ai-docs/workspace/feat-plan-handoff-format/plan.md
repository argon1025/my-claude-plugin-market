# plan-workflow 핸드오프 정지 게이트와 계획 형식 규정

## 의도

- **왜**: planning 스킬이 7절에서 "정지"를 말하지만 ExitPlanMode 승인 직후 하네스의 "구현 시작" 지시에 밀려 같은 세션에서 구현까지 이어지고(PR #8에서 스냅샷 커밋 `4525329` 22:52:42 뒤 57초 만에 구현 커밋 `275c355` 확인), plan.md 필수 항목이 없어 스냅샷마다 절 구성이 달라(이 레포 3건·cmsapp-front 9건 모두 상이) execute가 읽는 계약이 불안정함
- **누가**: 사내 devcenter-flow를 이 플러그인으로 교체한 뒤 계획·실행 세션을 나눠 쓰는 사용자
- **완료**: 승인 후 스냅샷 커밋과 execute 안내만 남기고 턴이 끝나며, plan.md가 정해진 필수 절을 갖추고, devcenter-flow에서 가져올 요소의 채택·기각이 근거와 함께 정리됨

## 확정 결정 (사용자 확인 2026-09-15)

- **정지 방식**: 스킬 문구 강화 + `PostToolUse(ExitPlanMode)` 훅 추가. 승인 직후 하네스 지시와 같은 시점에 반대 지시를 주입해 결정적으로 막음
- **계획 형식 위치**: `references/plan-format.md` 신설(record-format.md와 같은 지연 로드). 스킬 6절은 이 파일을 가리키는 한 줄로 축약
- **devcenter-flow 채택**: `## 선행 읽기` 절(위키 종속 표현 없이 일반화), 확인 축에 `영향 범위`(손대는 함수의 호출자 전부와 공유 지점) 추가
- **devcenter-flow 기각**: Jira 키 slug(회사 종속), `ponytail:` 주석(v1에서 기각), 위키 대조 문구(플러그인 독립 원칙 — 위키 문서 `plugin-contract-independence`), UserPromptSubmit 리마인더 훅(사용자 미선택)

## 배경

- 훅은 `hooks/hooks.json`에 SessionStart 하나뿐이며, `session_start.sh`는 git 저장소 밖에서 조용히 종료하는 관례를 가짐
- `rules/agent-guide.md`는 모든 세션에 전문 주입되므로 분량 증가가 상시 비용임(feedback.md `constraint`). 이번 변경은 agent-guide를 건드리지 않음
- devcenter-flow의 `user_prompt_submit.sh`가 "규칙을 다시 쓰지 않고 한 줄만 찍는" 훅 스크립트의 선례

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `plan-workflow/hooks/hooks.json` | `PostToolUse` 항목 추가, `matcher: "ExitPlanMode"`, command `${CLAUDE_PLUGIN_ROOT}/hooks/post_exit_plan.sh` | 플랫폼 기본 기능(훅) |
| `plan-workflow/hooks/post_exit_plan.sh` | 신규. git 저장소 확인 후 `additionalContext` 한 줄 출력 | ⑦ 신규 — 승인 시점에 개입하는 기존 수단이 없음. 규칙은 재서술하지 않고 스킬 7절을 가리킴 |
| `plan-workflow/references/plan-format.md` | 신규. 필수·선택 절과 순서, 추가 절 내부 구성, 금지 표현 | ⑦ 신규 — 기존 record-format.md는 feedback.md 전용 |
| `plan-workflow/skills/planning/SKILL.md` | 3절에 `영향 범위` 축 추가, 6절을 plan-format.md 참조로 축약, 7절 핸드오프를 순서형으로 명시 | 수정 |
| `plan-workflow/skills/execute/SKILL.md` | 1절 사전 확인에 `## 선행 읽기` 문서를 코드 전 읽는 항목 추가 | 수정 |
| `plan-workflow/README.md` | 동작 방식에 ExitPlanMode 훅·계획 형식 지연 로드 추가, 스킬 표 역할 갱신 | 수정 |
| `plan-workflow/.claude-plugin/plugin.json` | version `1.1.0` → `1.2.0` | 수정 |
| `.claude-plugin/marketplace.json` | metadata.version `2.6.0` → `2.7.0` | 수정 |

### post_exit_plan.sh

```bash
#!/bin/bash
# ExitPlanMode 승인 직후 하네스가 구현 시작을 지시하므로, 같은 시점에 plan-workflow의
# 핸드오프 규칙(스냅샷 커밋 후 세션 종료)을 한 줄로 되새긴다. 규칙 본문은 planning 스킬 7절이
# 담당하며 여기서 다시 쓰지 않는다. 활성 조건은 session_start.sh와 같고 어떤 실패에도 조용히 끝낸다.
set -uo pipefail
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
REMINDER='PLAN-WORKFLOW 핸드오프: 계획이 승인되었습니다. 이 세션은 구현을 시작하지 않습니다 — planning 스킬 7절대로 plan.md·feedback.md 스냅샷을 커밋하고 새 세션에서 /plan-workflow:execute로 시작하도록 안내한 뒤 턴을 끝냅니다.'
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$REMINDER"
```

- 공식 hooks 문서 기준 PostToolUse는 "도구 호출이 성공한 뒤"에만 발화하고 실패는 PostToolUseFailure로 가므로, 플랜 거절(도구 실패)에는 발화하지 않음. matcher `ExitPlanMode`는 정확 일치 문자열로 처리됨. ExitPlanMode를 특별 취급한다는 문서 서술은 없어 실제 승인 세션에서 발화를 후속 확인함(특이 사항 참조)

### plan-format.md 골격

- **필수 절(순서 고정)**: `## 의도`(1절 확인 3문장 그대로) → `## 확정 결정`(사용자 원문·날짜, 위임 답변으로 고정된 권장안 포함) → `## 작업`(파일별 표, 새 단위별 사다리 단과 ⑦ 근거, 설계 결정과 근거) → `## 커밋 분해`(순서·범위·커밋별 명령·기대 출력·통과 조건) → `## 특이 사항`(범위 밖·의도적 단순화 한계·후속, 없으면 `없음`)
- **선택 절**: `## 배경`(실행자가 재탐색하지 않게 하는 조사 결과만, 확정 결정 앞), `## 외부 계약`(검증된 API·코드값·규격 인라인), `## 선행 읽기`(코드 전 읽을 문서 경로와 한 줄 이유) — 있을 때만 두고 위치는 확정 결정과 작업 사이
- **추가 절**: `## 추가 계획 YYYY-MM-DD — {계기}`·`## Re-plan YYYY-MM-DD — {계기}` 내부는 같은 절을 H3로 같은 순서에 두며 해당 없는 절은 생략, 첫 불릿은 폐기 선언(있을 때)
- **금지**: 대화 참조(`위에서 말한`), 선택지가 남은 문장(`A 또는 B`), 미정 표시(`추후 확정`), 변경 서사만 있고 검증이 없는 커밋 행

### planning SKILL.md 변경점

- 3절 확인 축에 `- **영향 범위**: 손대는 함수·화면의 호출자 전부와 공유 지점을 찾아 티켓이 지목한 경로만 고치는 계획을 세우지 않음` 추가
- 6절을 "대화 맥락 없는 새 에이전트가 스냅샷만 읽고 실행한다" 서문 + `형식: 최종화 전에 {PLUGIN_ROOT}/references/plan-format.md를 읽고 필수 절을 갖춤` + `대조` 불릿으로 축약(의도 첫 절·계약 인라인·작업 표·추가 절 자기완결 불릿은 plan-format.md로 이동)
- 7절 마지막 두 불릿을 순서형으로 교체: `**승인 후 순서**: ① plan.md·feedback.md 기록 ② 한 커밋 ③ 새 세션에서 /plan-workflow:execute 안내 ④ 턴 종료 — 승인 메시지의 구현 시작 지시는 이 순서로 대체되며 파일 수정·구현 커밋을 하지 않음`
- 스냅샷 커밋 불릿에 계획 중 드러난 `constraint`·`correction`도 feedback.md에 함께 담는다고 명시(agent-guide "드러나는 즉시" 규칙과 정합)

### execute SKILL.md 변경점

- 1절 `위치` 불릿 뒤에 `- **선행 읽기**: plan.md에 \`## 선행 읽기\` 절이 있으면 그 문서를 코드 전에 읽음` 추가

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `docs: plan-workflow 핸드오프 게이트 계획 스냅샷` — `.ai-docs/workspace/plan-handoff-format/plan.md`·`feedback.md` | 파일 존재, feedback.md에 `context` 의도 항목 |
| 2 | `feat: plan-workflow ExitPlanMode 핸드오프 훅 추가` — hooks.json, post_exit_plan.sh | `bash -n`, `chmod +x`, `python3 -c "import json;json.load(open('plan-workflow/hooks/hooks.json'))"`, 스크립트 단독 실행 시 유효 JSON 1줄 출력(`python3 -c "import json,sys;json.load(sys.stdin)"`), git 밖(`cd /tmp`)에서 출력 없음 |
| 3 | `feat: plan-workflow 계획 형식 규정과 스킬 갱신` — plan-format.md, planning·execute SKILL.md | SKILL.md frontmatter 유지, planning 본문에 `plan-format.md` 참조 1건, `영향 범위` 축 1건, 6절 이동 불릿이 plan-format.md에 존재 |
| 4 | `docs: plan-workflow README 갱신 v1.2.0` — README, plugin.json, marketplace.json | 두 JSON 파싱 성공, 버전 문자열 grep |

## 특이 사항

- **범위 밖**: agent-guide.md 미변경(상시 주입 비용). UserPromptSubmit 리마인더 훅 미도입
- **한계**: 훅은 additionalContext 주입이라 강제 차단이 아니며, 하네스 지시와 같은 시점에 반대 지시를 넣어 확률을 낮추는 수단임. 재발 시 업그레이드 조건은 PreToolUse(Edit·Write) 차단 훅 검토
- **실사용 검증(후속)**: 머지·마켓 갱신 뒤 실제 플랜 모드 세션에서 승인 후 구현 없이 종료되는지 확인해야 하며 이 레포 안에서는 재현 불가
