# agent-wiki-update-review 작업 기록

- `context` agent-wiki update 스킬은 llm-wiki `skills/update/SKILL.md`를 이관 검토하며, 요구는 "간결하고 신뢰도 높은 프로세스로 새로 위키를 만들고있음", "추출은 대상 레포에 시간 순으로 머지된 머지 묶음 n개를 대상으로 agent-wiki/references/doc-contract.md 에 맞게 업데이트", "enum 같이 수정된 코드에서 해당 부분만 추출하면 나머지 상태들은 위키에 반영이 안될 수 도 있을듯한데 이를 대비해서 문서 작성 시 데이터 완결성을 보장할 수 있는 방안은 필요"임
  - source: 사용자 확인 2026-09-29
- `constraint` llm-wiki update는 `type` 판정·`catalog.py --check`·`graph.py`(간선 `kind`·`contracts`)·`state/{slug}.json` 커서·wiki-update PR 게시에 기대지만, agent-wiki에는 문서 `type`·문서 검사 스크립트·커서 저장소가 없고 `deps.json` 간선은 `{to, desc}`뿐이며 쓰기는 임시 clone에서 `baseBranch`로 직접 push함
  - evidence: llm-wiki/skills/update/SKILL.md, agent-wiki/skills/register/SKILL.md, agent-wiki/scripts/verify_register_file.py
- `constraint` diff 기반 추출은 diff에 드러난 원소만 사실로 남겨, 코드값 표·상태 목록처럼 닫힌 집합을 다루는 절은 일부 원소만 담긴 채 전체처럼 읽힘 — 집합 밖 사실의 누락은 에이전트가 코드로 돌아가지만, 부분 집합 표는 에이전트가 없는 값을 없다고 판단하게 만듦
- `context` agent-wiki update는 반영 결과를 위키 원격에 `wiki-update/` 브랜치 PR로 게시하고 PR 머지를 승인 지점으로 두며, 레포별 커서는 위키 `state/{slug}.json`에 둠
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki update의 닫힌 집합(코드값 표·상태와 전이·허용 목록) 완결성은 추출 사실의 `set` 표시, 반영 단계의 머지 시점 정의 전 원소 보충, 표 위 `원본:` 줄, 검토 단계의 원소 수 대조로 보장하는 방향으로 합의함
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki update의 추출 대상은 도메인 하나로 한정함 — 사용자 문장 "업데이트 목록 추출 시 특정 도메인만 하도록 지원해야함 전체 도메인 포함이면 너무 많아져서"
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki는 스크립트를 재현성이 필요한 곳에만 두며 위키 파일 수정은 에이전트가 직접 함 — 사용자 문장 "불필요한 스크립트는 최소화 하고싶음 기존 이관 방식도 꼭 필요한 부분만 스크립트 도입임 (예: 파일 수정은 에이전트가 직접 검증만 스크립트가)"이며, update에서는 머지 수집 스크립트 하나만 두고 커서 파일도 에이전트가 씀
  - source: 사용자 확인 2026-09-29
- `why` agent-wiki update는 문서 규약 형식 검사 스크립트를 두지 않고 검토 에이전트가 의미와 형식을 함께 판정함 — 사용자 문장 "해당 문서가 의미론적으로 잘 작성되었는지는 직접읽어봐야함 템플릿만 지켰다고 그게 통과되었다고 생각할 수 있기때문"이며, 대가는 파일명·절 순서 같은 형식 위반도 에이전트 판정에 기댄다는 점이고 PR 리뷰에서 같은 형식 위반이 반복되면 그 항목만 검사하는 스크립트를 도입함
  - source: 사용자 확인 2026-09-29
- `context` agent-wiki update의 커서 없는 레포는 스킬이 시작 지점을 사용자에게 묻고, PR 확인·생성 절차는 `agent-wiki/references/publish.md`에 분리해 회사 위키(Bitbucket) 전환 시 그 파일만 고침
  - source: 사용자 확인 2026-09-29
