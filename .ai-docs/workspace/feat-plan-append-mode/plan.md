# plan-workflow 계획 누적 모드 도입

## Context

계획이 승인되어 `plan.md`가 커밋된 뒤 같은 브랜치에서 추가 요구나 수정건이 생겨 `/plan-workflow:planning`을 다시 부르면, 스킬이 기존 계획을 통째로 지우고 새 계획으로 덮어쓴다. 실물 사례로 `.ai-docs/workspace/feat-llm-wiki/plan.md`는 "앞선 계획(`be484e5` 스냅샷)은 이 문서로 대체되며"라는 문장과 함께 1차 계획을 파일에서 완전히 제거했다.

원인은 planning 스킬 7절에 있다. 충돌 규칙(`plan-workflow/skills/planning/SKILL.md:60`)이 "이번 작업의 스냅샷이 아니면 정지"만 규정해 같은 slug의 계획은 충돌로 걸리지 않고, 스냅샷 커밋 규칙(`:61`)이 "승인된 계획을 그대로 `plan.md`에 쓰고"여서 전체 교체로 해석된다. execute 스킬은 이미 `## Re-plan YYYY-MM-DD` 절을 파일 끝에 덧붙이는 누적 경로를 갖고 있으므로(`plan-workflow/skills/execute/SKILL.md:18`), planning에만 대응 경로가 없는 상태다.

목표는 계획 이력을 파일 안에 보존하는 것이다. 같은 slug에 계획이 이미 있으면 planning이 앞 절을 건드리지 않고 `## 추가 계획` 절을 파일 끝에 덧붙이며, 앞 계획이 무효가 된 경우에도 삭제 대신 폐기 선언을 남긴다.

## 확정된 결정 (사용자 확인 2026-09-14)

| 축 | 결정 |
|---|---|
| 절 헤딩 | 계기별 분리 — planning은 `## 추가 계획`, execute는 기존 `## Re-plan` 유지 |
| 실행 기준점 | execute가 매번 자체 판정 — plan.md 전문과 git log·코드를 대조해 미실행 절을 가림 |
| 전면 개정 | 앞 절을 지우지 않고 추가 절에 폐기 선언을 적어 무효 범위를 밝힘 |
| 트리거 | 같은 slug에 plan.md가 있으면 별도 확인 없이 추가 모드로 자동 전환 |

## 변경 대상

### 1. `plan-workflow/skills/planning/SKILL.md`

**6절 계획 자기완결** — 불릿 하나 추가

- **추가 절 자기완결**: 추가 절도 그 절만 읽고 실행할 수 있어야 하며, 앞 절과 겹치는 계약은 문서 안의 절 이름으로 참조하되 대화 참조는 쓰지 않음

**7절 핸드오프** — `충돌`·`스냅샷 커밋` 불릿 재작성 및 불릿 2종 추가

- **모드 판정**: `.ai-docs/workspace/{slug}/plan.md`가 있으면 추가 모드로 전환해 사용자에게 알리고, 없으면 신규 작성함
- **충돌**: 기존 `plan.md`가 이번 작업과 무관한 다른 주제의 계획이면 덧붙이지 않고 충돌을 보고한 뒤 정지함 (현행 규칙 유지, 조건만 좁힘)
- **추가 절**: 승인된 추가 계획을 `## 추가 계획 YYYY-MM-DD — {한 줄 계기}` 절로 파일 끝에 덧붙이며 앞 절은 한 글자도 고치지 않음
- **폐기 선언**: 앞 절의 결정이 무효가 되면 지우지 않고 추가 절 첫 불릿에 `폐기: {절 이름 또는 항목}`과 근거를 적어 execute가 건너뛰게 함
- **스냅샷 커밋**: 문구를 "쓰고"에서 "신규는 새로 쓰고 추가는 끝에 덧붙이고"로 조정

### 2. `plan-workflow/skills/execute/SKILL.md`

**1절 사전 확인** — 불릿 하나 추가

- **실행 대상 판정**: 절이 여럿이면 앞에서부터 각 절의 커밋 분해가 git log와 코드에 이미 반영됐는지 대조해 미실행 절만 실행하고, 폐기 선언된 절과 항목은 건너뛰며, 완료 여부가 갈리면 멈춰 물음

**2절 실행 루프** — `재계획` 불릿의 헤딩 형식을 추가 절과 맞춤

- `## Re-plan YYYY-MM-DD` → `## Re-plan YYYY-MM-DD — {한 줄 계기}` (같은 날 절이 둘 이상일 때 구분되며 추가 절과 형식이 통일됨)

### 3. `plan-workflow/rules/agent-guide.md`

상시 주입 파일이므로 `계획` 불릿(`:7`) 끝에 한 구절만 덧붙임 — 같은 slug에 계획이 이미 있으면 덮어쓰지 않고 절로 덧붙인다는 사실.

### 4. `plan-workflow/hooks/session_start.sh`

`plan.md` 존재 시 주입 문구(`:38`)를 구현·추가 계획 두 경로가 보이게 고침.

```
- **plan.md**: 있음 — 구현은 `/plan-workflow:execute`, 추가 계획은 `/plan-workflow:planning`(기존 계획 끝에 덧붙임)
```

### 5. `plan-workflow/README.md`

- 스킬 표 planning 행(`:7`): 승인 시 동작에 추가 절 덧붙임 명시
- 산출물 트리 주석(`:33`): `승인된 계획 원문 + `## 추가 계획`·`## Re-plan` 절`
- 기록 규약 요약 `계획 분리` 불릿(`:41`): 계획 파일도 덧붙이기 원칙을 따른다는 점 반영

### 6. 버전

- `plan-workflow/.claude-plugin/plugin.json`: `1.0.0` → `1.1.0`
- `.claude-plugin/marketplace.json`: `metadata.version` `2.4.0` → `2.5.0`

루트 `README.md`는 스킬 구성이 그대로여서 변경하지 않는다.

## 범위 밖

- `.ai-docs/workspace/feat-llm-wiki/plan.md`의 소급 복원 — 이미 머지된 작업 기록이므로 손대지 않음
- 추가 절이 쌓일 때의 파일 크기 관리 — 훅이 `plan.md` 본문을 주입하지 않아 세션 예산에 영향이 없음
- 규약 준수 검사 도구 — 현행 플러그인 방침대로 검사하지 않음

## 작업 순서와 커밋 분해

| 커밋 | 메시지 | 파일 | 검증 |
|---|---|---|---|
| 0 | `docs: plan-workflow 계획 누적 모드 계획 스냅샷` | `.ai-docs/workspace/{slug}/plan.md`, `feedback.md` | 파일 존재 |
| 1 | `feat: plan-workflow 계획 누적 모드 도입` | planning·execute SKILL.md, agent-guide.md, session_start.sh | 아래 훅 검증 + 참조 대조 |
| 2 | `docs: plan-workflow README 갱신 v1.1.0` | plan-workflow/README.md, plugin.json, marketplace.json | JSON 파싱 통과 |

커밋 0 전에 `feat/plan-append-mode` 브랜치를 만든다. 현재 `main`이라 slug가 미확정이며, 브랜치 생성 후 slug는 `feat-plan-append-mode`가 된다.

## 검증

훅 문법과 출력 확인.

```
bash -n plan-workflow/hooks/session_start.sh
```

`plan.md` 존재 분기를 실제로 태우기 위해 스크래치패드에 임시 저장소를 만들어 훅을 직접 실행하고, `plan.md: 있음` 줄의 문구가 바뀐 대로 나오는지 확인한다.

```
TMP=/private/tmp/claude-501/-Users-a1000377-Desktop-Projects-onestorecorp-my-claude-plugin-market/a9404186-2d6b-4b2e-9e6e-697c7d64afd9/scratchpad/hooktest
rm -rf "$TMP" && mkdir -p "$TMP/.ai-docs/workspace/feat-sample"
git -C "$TMP" init -q && git -C "$TMP" checkout -qb feat/sample
printf '# sample\n' > "$TMP/.ai-docs/workspace/feat-sample/plan.md"
CLAUDE_PLUGIN_ROOT="$PWD/plan-workflow" CLAUDE_PROJECT_DIR="$TMP" plan-workflow/hooks/session_start.sh | python3 -m json.tool
```

문서 상호 참조가 남지 않았는지 대조한다.

```
grep -rn --include="*.md" --include="*.sh" -e "Re-plan" -e "추가 계획" -e "덮어" plan-workflow
```

JSON 유효성을 확인한다.

```
python3 -m json.tool plan-workflow/.claude-plugin/plugin.json > /dev/null && python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo OK
```

## feedback.md 추가 항목 (커밋 0)

```
- `context` plan-workflow의 planning 스킬이 같은 브랜치에서 재호출될 때 기존 plan.md를 전면 교체하던 동작을 추가 절 덧붙이기로 바꾸는 작업이며, 사용자 원문은 "기존 계획 내용은 유지하고 add-plan 을 plan.md 하위에 append 하는 방향으로 개선 검토"임
  - source: 사용자 확인 2026-09-14
- `why` 추가 절 실행 여부를 plan.md에 상태 마커나 선행 커밋 해시로 적지 않고 execute가 git log·코드로 매번 판정하게 한 것은, 승인된 스냅샷을 사후에 고치지 않는다는 plan-workflow 원칙을 깨지 않기 위함임
  - source: 사용자 확인 2026-09-14
- `why` planning의 `## 추가 계획`과 execute의 `## Re-plan` 절을 한 이름으로 합치지 않은 것은 신규 요구와 실행 중 현실 괴리가 작성 주체·실행 의미에서 다르기 때문이며, 날짜 뒤 계기 한 줄을 붙이는 형식만 공통으로 둠
  - source: 사용자 확인 2026-09-14
- `constraint` plan-workflow의 rules/agent-guide.md는 SessionStart 훅이 모든 세션에 전문 주입하므로 분량 증가가 상시 비용이며, 상세 규칙은 스킬 본문이나 references로 내림
  - evidence: plan-workflow/hooks/session_start.sh
```
