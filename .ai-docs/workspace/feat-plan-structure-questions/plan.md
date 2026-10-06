# plan-workflow planning 구조 질문 선행과 기존 코드 판정

## 의도

- **왜**: planning 스킬이 기존 코드 유지를 기본값으로 두고 구조 분기점(폴더·모듈 배치, 기존 구조 유지·재편)을 묻지 않으며, 선택지에 어디가 어떻게 바뀌는지가 없고, 앞 답에 따라 무의미해질 질문을 한꺼번에 물어 구현 후 구조가 이상해 Re-plan이 반복됨
- **누가**: 플랜 모드로 계획을 세우는 plan-workflow(사내판 devcenter-flow 포함) 사용자가, 특히 새 구조를 도입하거나 기존 코드를 재편할 수 있는 작업에서 겪음
- **완료**: planning 스킬 본문이 (a) 구조 질문을 먼저 하고 (b) 재편·삭제로 유지할 코드가 줄면 지울 범위와 함께 후보로 올리며 (c) 선택지마다 바뀌는 위치와 변경 후 형태를 보이고 (d) 앞 답에 따라 필요성이 바뀌는 질문은 같은 라운드에 넣지 않도록 규정되고, 본문 분량 증가는 최소이며, 사내판 devcenter-flow까지 같은 본문·같은 버전으로 반영됨

## 배경

- **유지 편향 원인**: `plan-workflow/skills/planning/SKILL.md` 4절 사다리가 "새 코드 단위마다" 적용되어 추가 코드만 정당화 부담을 지고 기존 코드 유지는 무비용으로 취급되며, ② "코드베이스에 이미 있음"이 기존 재사용을 상위 단으로 둠
- **구조 축 부재**: 3절 확인 축 7개에 폴더·모듈 배치와 기존 구조 유지 여부가 없고, 5절 `확인 선행`의 "도출되는 것은 묻지 않음"과 겹쳐 기존 코드 형태가 질문 없이 답으로 처리됨
- **위치 설명 누락**: 5절 `선택형`이 변경 위치·변경 후 형태를 요구하지 않으며, 과거 planning 세션 질문 선택지 1,508개 중 preview 사용은 46개(3%), 설명 중앙값 63자임
- **분기 기준 협소**: 5절 `독립 라운드`의 기준이 "문구가 바뀌는 질문"이라 문구는 같고 필요성만 사라지는 질문을 거르지 못함
- **Re-plan 근거**: 계획 파일 25개의 Re-plan·추가 계획 51절 중 17절이 제목상 구조 재편·불필요 코드 제거 계기이며, `onestore-devcenter-front`의 `terms-of-service-migration`은 v2 폴더 분리부터 v1 배선 재사용 없는 재구성까지 하루 4절이 이어짐

## 확정 결정 (사용자 확인 2026-10-06)

- **변경 구조**: 3절에 무엇을 물을지(`구조` 축), 4절에 무엇이 최소인지(`기존 코드` 판정)를 분리해 각각 불릿 1개로 추가함 — 3절 통합안은 4절 비대칭이 남아 기각
- **질문 규정**: 5절 `선택형`에 현재 상태·후보별 바뀌는 위치·변경 후 형태(AskUserQuestion preview)를, `독립 라운드`에 설계를 가르는 질문 우선과 필요 여부·선택지 기준을 넣어 두 불릿을 교체함
- **정리 방식**: 재편·삭제는 에이전트가 자율 수행하지 않고 지울 범위와 함께 후보로 올려 사용자가 결정함
- **범위**: 개인판 plan-workflow와 사내판 devcenter-flow 미러링까지 이번 계획에 포함함
- **제외**: `plan.md` 결과 구조 절 신설, execute 스킬·`rules/agent-guide.md`·`references/plan-format.md`·README 변경은 하지 않음

## 외부 계약

- **사내판 위치**: `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-flow/`, 기본 브랜치 `master`에 직접 커밋하는 것이 기존 미러링 관례(e14d0ae)임
- **사내 고유 파일**: devcenter-flow의 `.claude-plugin/plugin.json`·`README.md`·`config.json` 3종은 rsync로 덮어쓰지 않으며, 현재 개인판과 다른 파일은 이 3종뿐임
- **사내판 버전 키**: `.claude-plugin/marketplace.json`의 최상위 `version`(현재 `5.2.0`)과 `plugins[name=devcenter-flow].version`(현재 `3.3.0`), 그리고 devcenter-flow `plugin.json`의 `version`(현재 `3.3.0`)
- **개인판 버전 키**: `plan-workflow/.claude-plugin/plugin.json`의 `version`(현재 `3.3.0`)과 `.claude-plugin/marketplace.json`의 `metadata.version`(현재 `4.5.0`)이며, 개인판 marketplace에는 플러그인별 version이 없음
- **버전 이력**: `3.4.0`은 개인판 plan-workflow·사내판 devcenter-flow 모두 사용 이력이 없음

## 선행 읽기

- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/my-claude-plugin-market/plugin-authoring.md`: 버전 상향 시 plugin.json과 marketplace metadata.version을 함께 올리는 규칙
- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/internal-plugin-mirror.md`: 사내판 rsync 대상·사내 고유 파일·대응 플러그인 동일 버전 규칙

## 작업

| 파일 | 변경 | 사다리 |
| --- | --- | --- |
| `plan-workflow/skills/planning/SKILL.md` | 불릿 2개 추가, 2개 교체, frontmatter description 한 구절 교체 | ⑥ 한 줄(불릿 단위) |
| `plan-workflow/.claude-plugin/plugin.json` | version `3.3.0` → `3.4.0` | ① 값 변경만 |
| `.claude-plugin/marketplace.json` | metadata.version `4.5.0` → `4.6.0` | ① 값 변경만 |
| 사내판 `plugins/devcenter-flow/` | 개인판 공통 본문 rsync(변경 파일은 planning SKILL.md 1개), plugin.json version `3.4.0` | ② 기존 rsync 미러링 절차 |
| 사내판 `.claude-plugin/marketplace.json` | devcenter-flow 항목 version `3.4.0`, 최상위 version `5.3.0` | ① 값 변경만 |

### planning SKILL.md

frontmatter `description`의 `minimum-code ladder per new unit`을 `minimum-code ladder for new and touched code`로 바꿈.

3절 확인 축의 `- **범위**:` 불릿 바로 앞에 추가함.

```
- **구조**: 새 코드의 폴더·모듈 배치와 손대는 기존 구조의 유지·재편 여부를 정하며, 기존 코드의 형태는 현재 상태일 뿐 유지 근거가 아니므로 코드로 답이 있다고 보지 않음
```

4절 사다리의 `- **신규 근거**:` 불릿 뒤, `- **금지**:` 불릿 앞에 추가함.

```
- **기존 코드**: 손대는 기존 코드에도 같은 원칙을 적용해 살려서 고치는 안과 재편·삭제하는 안을 변경 후 유지할 코드 양으로 비교하고, 재편 쪽이 적으면 지울 범위와 함께 후보로 올림
```

5절 `선택형` 불릿 전체를 교체함.

```
- **선택형**: 질문마다 현재 상태를 밝히고 권장안·근거·대안·트레이드오프를 갖춘 이름 붙은 후보로 제시하되 후보마다 바뀌는 파일·위치와 변경 후 형태(폴더 트리·시그니처 등, AskUserQuestion은 preview)를 보이며, 권장안이 문서나 작업 기록에 남은 팀 결정과 충돌하면 권장 대신 충돌을 드러냄
```

5절 `독립 라운드` 불릿 전체를 교체함.

```
- **독립 라운드**: 구조처럼 설계를 가르는 질문을 먼저 묻고 다른 답에 따라 필요 여부나 선택지가 바뀌는 질문은 다음 라운드로 미루며, 해석 사이에서 조용히 고르지 않음
```

- **정합**: 3절 서문 "요청·코드로 이미 답이 있는 축만 생략"과 `구조` 불릿의 "코드로 답이 있다고 보지 않음"은 의도된 예외이며, 4절 `금지`(요청 없는 추상화)는 `기존 코드` 불릿이 후보 제시에 그치므로 충돌하지 않음
- **공통 본문 제약**: 추가 문구에 플러그인 이름·사내 경로·개인판 경로 상수를 넣지 않으며, AskUserQuestion·Explore 같은 하네스 도구명은 기존 본문 관례상 허용됨

### 사내판 미러링

개인판 커밋 1·2가 끝난 뒤 아래 dry-run으로 변경 대상이 planning SKILL.md 하나인지 확인하고, 같은 명령에서 `-n`을 빼고 실행함.

```
rsync -a -n -i --delete \
  --exclude '/.claude-plugin/plugin.json' --exclude '/README.md' --exclude '/config.json' \
  /Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market/plan-workflow/ \
  /Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/devcenter-flow/
```

이어서 사내판 devcenter-flow `plugin.json` version을 `3.4.0`, 사내판 `marketplace.json`의 devcenter-flow 항목 version을 `3.4.0`, 최상위 version을 `5.3.0`으로 바꿈.

## 커밋 분해

| # | 범위 | 검증 |
| --- | --- | --- |
| 0 | `docs: plan-workflow 구조 질문 개선 계획 스냅샷` — `feat/plan-structure-questions` 브랜치 생성 후 `.ai-docs/workspace/feat-plan-structure-questions/plan.md`·`feedback.md` (계획 세션에서 수행) | 두 파일 존재, `feedback.md`에 `context` 항목 1개 이상 |
| 1 | `feat: plan-workflow planning 구조 축 선행·기존 코드 판정·질문 위치 표시` — `plan-workflow/skills/planning/SKILL.md` | 아래 커밋 1 검증 명령 전부 통과 |
| 2 | `chore: plan-workflow 3.4.0, 마켓플레이스 4.6.0` — plugin.json, marketplace.json | 아래 커밋 2 검증 명령 출력이 `3.4.0 4.6.0` |
| 3 | 사내판 레포 `feat(devcenter-flow): 계획 질문 구조 선행·기존 코드 판정 미러링, 3.4.0, 마켓플레이스 5.3.0` — devcenter-flow 공통 본문, plugin.json, marketplace.json | 아래 커밋 3 검증 명령 전부 통과 |

커밋 1 검증 (레포 루트에서 실행, 기대값은 주석).

```
F=plan-workflow/skills/planning/SKILL.md
grep -c '^- \*\*구조\*\*: ' $F                 # 1
grep -c '^- \*\*기존 코드\*\*: ' $F            # 1
grep -c 'AskUserQuestion은 preview' $F         # 1
grep -c '필요 여부나 선택지가 바뀌는 질문' $F  # 1
grep -c '문구가 바뀌는 질문' $F                # 0
grep -c 'per new unit' $F                      # 0
grep -c 'for new and touched code' $F          # 1
awk '/^- \*\*구조\*\*/{a=NR} /^- \*\*범위\*\*/{b=NR} /^- \*\*신규 근거\*\*/{c=NR} /^- \*\*기존 코드\*\*/{d=NR} /^- \*\*금지\*\*/{e=NR} END{print (a<b && c<d && d<e) ? "order ok" : "order fail"}' $F   # order ok
head -2 $F | tail -1                           # name: planning
wc -c < $F                                     # 7900 이하
```

커밋 2 검증.

```
python3 -c "import json; print(json.load(open('plan-workflow/.claude-plugin/plugin.json'))['version'], json.load(open('.claude-plugin/marketplace.json'))['metadata']['version'])"
```

커밋 3 검증 (사내판 레포 루트에서 실행).

```
diff -rq /Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market/plan-workflow plugins/devcenter-flow
# plugin.json·README.md·config.json 3줄만 출력
python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); p=json.load(open('plugins/devcenter-flow/.claude-plugin/plugin.json')); print(p['version'], [x['version'] for x in m['plugins'] if x['name']=='devcenter-flow'][0], m['version'])"
# 3.4.0 3.4.0 5.3.0
git status --short
# plugins/devcenter-flow/skills/planning/SKILL.md, plugins/devcenter-flow/.claude-plugin/plugin.json, .claude-plugin/marketplace.json 3개만 변경
```

## 특이 사항

- **행동 검증 한계**: 검증은 문구·순서·버전의 정적 확인까지이며, 질문 순서·preview 사용 같은 실제 행동 변화는 이후 planning 세션에서만 관찰됨
- **질문 증가**: `구조` 축 추가로 소규모 작업에서도 질문이 늘 수 있으나, 재편 후보는 유지할 코드가 줄어드는 경우에만 오르므로 발생 빈도는 제한됨
- **미러 재동기화**: 개인판 PR 리뷰로 planning SKILL.md 문구가 바뀌면 사내판에 같은 rsync를 다시 실행해야 함
- **push·PR**: 두 레포 모두 로컬 커밋까지만 하며 push와 PR 생성은 사용자 요청 시에만 함
- **효과 확인**: 후속으로 이후 계획 파일의 Re-plan·추가 계획 계기 중 구조 재편·불필요 코드 제거 비율이 줄었는지 확인함
