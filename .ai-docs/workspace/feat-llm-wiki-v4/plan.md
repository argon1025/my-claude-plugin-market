# llm-wiki 4.0.0 — 그래프 스키마 개편과 현행 합의 모델

## Context

- **배경**: llm-wiki 3.0.0은 노드 스키마·주입 형상·조사 절차·합의 모델(등급·출처·verified·낡음·inbox)이 무거워 주입 토큰과 운영 부담이 큼
- **목표**: 노드·간선 스키마 개편, 레포 지도 중심 주입, 4레인 조사, 그래프 화면, 등급을 없앤 현행 합의 모델을 4.0.0으로 반영
- **합의 범위**: 합의 모델(등급·출처·verified·낡음·inbox 제거, update 무인 전역 시간순)까지 전부, 노드 `project`는 GitHub owner URL, view.py·graph.html 포함, 위키 데이터 이관은 README 안내만

## 변경 대상

- **스키마 개편**: 노드 `remote`·`defaultBranch`·`responsibilities`(평문 배열)·`hosts`(환경별 1개)·`project`, `domains.{d}.repos.{slug}` 중첩, `deps.{from}[]` 그룹 맵·`contracts[]`, `excluded`→`dormant`
- **스키마 단일 정본**: `graph.py schema --for survey|facts --lane --domain`, 스킬 프롬프트의 상수 직기재 제거
- **주입 재편**: 레포 지도·의존 3묶음, `graph.py repo {slug}`·`render`·`map`, 경유 1홉 간선, contracts 형식 경고
- **조사 개편**: register 4레인 병렬 + 2.5장 메인 검증, `survey.py` 증거 인벤토리
- **그래프 화면**: `scripts/view.py`, `templates/graph.html`
- **합의 모델**: frontmatter description만, 등급·출처·inbox·낡음 제거, update.py 전역 시각 순 `--max-merges 40`·`domains` 서브커맨드 삭제, doc-contract 7장 판정 넷
- **저장소 절차**: 스킬 시작 `git pull --ff-only`, 끝 `git pull --rebase && git push`, 건너뛴 사실은 스킬 최종 보고의 `| 주제 | 위치 | 기존 값 | 새 값·사유 |` 표
- **GitHub owner**: `project`는 `https://{host}/{owner}`, 접근 좌표 `GitHub {owner}`, clone 패턴 `{host}/{owner}/{slug}`, register 정본 remote는 upstream → origin

## 검증

- **정적**: `python3 -m py_compile llm-wiki/scripts/*.py`
- **픽스처 위키**: 도메인 1, `project: https://github.com/argon1025`, 레포 2, 간선 1로 아래 명령이 에러 0·기대 출력

```
python3 llm-wiki/scripts/graph.py check --wiki $FIX
python3 llm-wiki/scripts/catalog.py --check --root $FIX/knowledge $FIX/registry.json $FIX/deps.json
python3 llm-wiki/scripts/graph.py render --wiki $FIX --domain argon1025-side --slug my-claude-plugin-market
python3 llm-wiki/scripts/graph.py schema --for survey --lane http
python3 llm-wiki/scripts/view.py --wiki $FIX --no-open
```

- **훅**: `LLM_WIKI_ROOT=$FIX CLAUDE_PROJECT_DIR=$PWD bash llm-wiki/hooks/session_start.sh </dev/null`이 JSON을 내고 접근 좌표 `GitHub argon1025`, clone 패턴 `github.com/argon1025/{slug}`, 위키 부재 시 `/llm-wiki:init` 안내
