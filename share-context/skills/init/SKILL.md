---
name: init
description: Clone the configured wiki repo to the wiki root, or fast-forward it if already present.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki.baseRoot`·`wiki.remote`·`wiki.baseBranch`를 읽어 위키를 준비합니다. git 명령은 인증 프롬프트에서 멈추지 않도록 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다.

## 1. 판정

- **경로 없음**: `git clone {remote} {baseRoot}`
- **경로 있음**: `origin` URL이 `remote`와 같고 현재 브랜치가 `baseBranch`일 때만 `git -C {baseRoot} pull --ff-only origin {baseBranch}`
- **불일치**: git 저장소가 아니거나 `origin`·브랜치가 다르면 아무것도 고치지 않고 기대값과 실제값을 보고 후 중단 — 다른 도구가 같은 트리에서 브랜치를 바꿔 둘 수 있으므로 브랜치 전환·stash 금지
- **빈 저장소**: clone 결과에 커밋이 없으면 2절로 진행

## 2. 골격

- **파일**: `registry.json` `{"domains": {}}`, `deps.json` `{"deps": {}}`, `knowledge/.gitkeep` 빈 파일, `.gitignore` `.local/` 4종 작성
- **게시**: `baseBranch`에 첫 커밋 `chore(init): 위키 골격` 후 `git push -u origin {baseBranch}`

## 3. 실패

- **인증·네트워크**: 에러 핵심 한 줄과 함께 사용자가 직접 실행할 `! git clone {remote} {baseRoot}` 안내
- **pull**: 로컬 변경·분기로 실패하면 해소하지 않고 원인 한 줄 보고
- **push**: 로컬 커밋은 남긴 채 실패 원인과 함께 보고

## 4. 보고

위키 경로, 수행 결과(clone·pull·골격 생성), `git -C {baseRoot} log -1 --oneline` 한 줄을 보고합니다.
