---
name: init
description: Use when the wiki repo is not present on this machine or exists without registry.json ("위키 초기화", "위키 세팅", "위키 클론", session header says 위키가 없음) — clones the shared wiki into the wiki root, or git-inits a new one and asks for the remote, and writes the skeleton (registry.json, deps.json, state/, knowledge/, .gitignore) with a first commit. Registers nothing and writes no facts. NOT for registering the current repo (/llm-wiki:register).
disable-model-invocation: true
---

위키 저장소를 이 머신에 놓습니다. 위키 경로는 `LLM_WIKI_ROOT`이며 기본값은 `~/.ai-docs/wiki`입니다. 초기화 여부는 `{WIKI_ROOT}/registry.json` 유무로 판정하며, 이 스킬은 레포를 등록하지 않고 사실을 쓰지 않습니다.

## 1. 판정

- **registry.json 있음**: `git -C {WIKI_ROOT} pull --ff-only` 후 "이미 초기화됨 — 레포 등록은 `/llm-wiki:register`"로 끝 — 충돌·분기는 멈추고 보고
- **디렉터리만 있음**: 빈 원격을 clone한 경우를 포함해 registry.json이 없으면 3장 골격 생성으로
- **디렉터리 없음**: 2장으로

## 2. 저장소 — 정지점 하나

- **질문**: AskUserQuestion으로 원격 URL(기존 위키 clone) 또는 "새로 만들기" 중 하나를 물음 — 새로 만들기면 연결할 원격 URL도 같은 라운드에 받음(없으면 빈 값 허용)
- **clone**: `git clone {URL} {WIKI_ROOT}` — 빈 저장소면 3장으로, registry.json이 있으면 1장 "있음"으로
- **새로 만들기**: `git init -b main {WIKI_ROOT}`
- **원격 없음 경고**: 원격을 끝내 못 받으면 "다른 머신·팀원과 공유되지 않음"을 보고에 남김

## 3. 골격

- **registry.json**: `{"domains": {}}`
- **deps.json**: `{"deps": {}}`
- **state/.gitkeep**·**knowledge/.gitkeep**: 빈 파일
- **.gitignore**: `.local/` 한 줄 — 스킬의 clean-tree 판정이 통과하는 조건
- **커밋**: `chore(init): 위키 골격` 한 커밋
- **원격**: URL을 받았으면 `git remote add origin {URL}`과 `git push -u origin main`, clone한 저장소면 `git push` — 실패는 로컬 커밋 상태와 함께 보고

## 4. 보고

- **결과**: 위키 경로, clone·신설 여부, 원격 URL 또는 "원격 없음"
- **다음**: 등록할 각 레포에서 `/llm-wiki:register`를 실행하면 도메인과 레포 노드가 생기고 다음 세션부터 규약·레포 지도·의존이 자동 주입됨
