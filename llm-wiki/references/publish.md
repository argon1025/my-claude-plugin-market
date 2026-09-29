# 위키 저장소 절차

쓰기 스킬(init·register·add·audit·update)이 위키 사본을 다루는 시작과 끝입니다.

- **사본**: `~/.ai-docs/wiki` — `{WIKI_ROOT}`, 훅·스크립트가 이 값을 읽음
- **저장소**: 고정 없음
- **기준 브랜치**: `main`
- **커밋 링크**: `https://{remote}/commit/{sha}` — `remote`는 registry 노드 값

## 1. 시작

- **동기화**: `git -C {WIKI_ROOT} switch main && git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단
- **열린 update PR**: update는 `--dry-run`이 아니면 `WIKI_ROOT`에서 `gh pr list --state open --json url,headRefName`을 보고 `wiki-update/` PR이 있으면 링크를 보고하고 중단(같은 머지를 두 번 추출함), 명령이 실패해도 오류 한 줄 보고 후 중단

## 2. 브랜치

- **update**: `git -C {WIKI_ROOT} switch -c wiki-update/{YYYYMMDD-HHMM}`
- **그 외**: 브랜치 없이 `main`에서 커밋

## 3. 게시

- **update**: `git -C {WIKI_ROOT} push -u origin {branch}` 후 `WIKI_ROOT`에서 `gh pr create --base main --head {branch} --title "update: {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장" --body-file {본문}` — 실패하면 단계·브랜치 이름·오류 한 줄 보고
- **긴 본문**: 본문이 60,000바이트를 넘으면 `추출 사실` 절을 떼어 본문에 "사실 원장은 첫 코멘트" 한 줄을 두고, PR 생성 뒤 뗀 절을 `gh pr comment {url} --body-file`로 게시
- **그 외**: `git -C {WIKI_ROOT} pull --rebase && git -C {WIKI_ROOT} push` — 실패는 로컬 커밋 상태와 함께 보고
- **커밋 0건**: 게시하지 않음

## 4. 종료

- **복귀**: 브랜치를 만든 실행은 어느 단계에서 끝나든 `git -C {WIKI_ROOT} stash -u && git -C {WIKI_ROOT} switch main`, 커밋 없이 끝난 브랜치는 이어서 `git -C {WIKI_ROOT} branch -D {branch}` — 세션 주입과 다른 쓰기 스킬이 미승인 편집을 읽지 않게 함
- **보고**: push는 "다음 세션 목록에 반영", update는 PR 링크와 "머지 후 다음 세션에 반영"
