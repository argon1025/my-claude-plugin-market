---
name: init
description: Use when the wiki repo is not present on this machine or exists without registry.json ("위키 초기화", "위키 세팅", "위키 클론", session header says 위키가 없음) — clones the shared wiki into the wiki root, or git-inits a new one and asks for the remote, and writes the skeleton (registry.json, deps.json, state/, knowledge/, .gitignore) with a first commit. Registers nothing and writes no facts. NOT for registering the current repo (/llm-wiki:register).
disable-model-invocation: true
---

위키 저장소를 이 머신에 놓습니다. 위키 경로는 `LLM_WIKI_ROOT`이며 기본값은 `~/.ai-docs/wiki`이고, 저장소 절차는 `${CLAUDE_PLUGIN_ROOT}/references/publish.md`(시작 전에 Read)를 따릅니다.

## 1. 판정

- **registry.json 있음**: `publish.md` 1장 후 "이미 초기화됨 — 레포 등록은 `/llm-wiki:register`"로 끝
- **디렉터리만 있음**: 3장으로
- **디렉터리 없음**: 2장으로

## 2. 저장소 — 정지점 하나

- **질문**: `publish.md` 저장소 불릿에 clone URL이 없을 때만 AskUserQuestion으로 원격 URL(기존 위키 clone) 또는 "새로 만들기"를 물음 — 새로 만들기면 연결할 원격 URL도 같은 라운드에 받음(빈 값 허용)
- **clone**: `git clone {URL} {WIKI_ROOT}` 뒤 registry.json이 있으면 4장, 없으면 3장
- **새로 만들기**: `git init -b {기준 브랜치} {WIKI_ROOT}`

## 3. 골격

`publish.md` 2장 뒤 아래 파일을 씁니다.

- **registry.json**: `{"domains": {}}`
- **deps.json**: `{"deps": {}}`
- **state/.gitkeep**·**knowledge/.gitkeep**: 빈 파일
- **.gitignore**: `.local/` 한 줄 — 위키 전용 clone과 그래프 화면 같은 로컬 산출물 제외
- **커밋**: `chore(init): 위키 골격` 한 커밋
- **원격**: 새 저장소는 URL을 받았을 때만 `git -C {WIKI_ROOT} remote add origin {URL}` 뒤, 빈 원격 clone은 바로 `git -C {WIKI_ROOT} push -u origin {기준 브랜치}`, 그 밖의 clone은 `publish.md` 3·4장 — 실패는 로컬 커밋 상태와 함께 보고

## 4. 보고

- **결과**: 위키 경로, clone·신설 여부, 원격 URL 또는 "원격 없음 — 다른 머신·팀원과 공유되지 않음"
- **다음**: 등록할 레포마다 `/llm-wiki:register` — 다음 세션부터 레포 지도·문서 목록이 주입됨
