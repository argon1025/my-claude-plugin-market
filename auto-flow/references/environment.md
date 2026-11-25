# 환경

이슈·PR·대화 도구처럼 환경마다 다른 것을 한곳에 적는 문서입니다. 스킬과 단계 문서는 도구 이름을 직접 적지 않고 이 문서의 절을 가리킵니다. 다른 환경에서 쓰려면 이 파일만 그 환경의 내용으로 바꾸고, 절의 제목과 번호는 그대로 둡니다.

아래 순서로 따릅니다.

1. 실행자의 지침이나 프로젝트 문서가 같은 항목을 정했으면 그것을 따름
2. 정한 것이 없으면 이 문서를 따름. 받은 이슈나 PR이 이 문서의 호스트가 아닌 다른 호스트의 것이면 그 항목에는 이 문서를 적용하지 않고 3번으로 감
3. 어디에도 없는 항목은 세션에 있는 도구로 할 수 있는 범위에서 진행함. 해당 호스트를 다룰 도구가 없으면 시작하지 않고 그 사실을 알리며, 도구 이름을 추측해 호출하지 않음

이 파일의 값은 GitHub를 쓰는 환경 기준입니다.

## 1. 이슈

- **호스트**: GitHub Issues. 이슈는 번호나 URL로 받음
- **도구**: `gh` CLI

  | 하는 일 | 명령 |
  | --- | --- |
  | 읽기 | `gh issue view {번호} --json title,body,labels,state,comments` |
  | 본문 쓰기 | `gh issue edit {번호} --body-file {파일}` |
  | 댓글 | `gh issue comment {번호} --body-file {파일}` |
  | 검색 | `gh issue list --state open --search "{검색어}"` |
  | 라벨 | `gh issue edit {번호} --add-label auto-flow` |
  | 만들기 | `gh issue create --title "{제목}" --body-file {파일} --label auto-flow` |

- **라벨**: 저장소에 `auto-flow` 라벨이 없으면 `gh label create auto-flow`로 만든 뒤 붙임
- **본문 서식**: 마크다운
- **이슈를 만들 곳**: 호출할 때 받은 저장소. 받지 않았으면 현재 체크아웃의 원본 저장소(2절). 이슈 유형은 없음

## 2. PR

- **호스트**: GitHub
- **도구**: `gh` CLI

  | 하는 일 | 명령 |
  | --- | --- |
  | 조회 | `gh pr view {번호} --json state,mergeCommit,headRefOid,baseRefName,comments,reviews` |
  | 코드 줄에 달린 코멘트 | `gh api repos/{owner}/{repo}/pulls/{번호}/comments` |
  | 같은 브랜치의 열린 PR | `gh pr list --head {브랜치} --state open` |
  | 만들기 | `gh pr create --base {베이스} --head {브랜치} --title "{제목}" --body-file {파일}` |
  | 코멘트 | `gh pr comment {번호} --body-file {파일}` |

- **원본 저장소**: `upstream` 리모트가 있으면 `origin`은 개인 fork이고 PR 대상은 `upstream`임. 없으면 `origin`이 원본임
- **베이스 브랜치**: 프로젝트 문서가 정한 브랜치. 없으면 원본 저장소의 기본 브랜치(`gh repo view --json defaultBranchRef`)

## 3. 대화

- **요청 원문을 읽는 곳**: 없음. 호출할 때 받은 글이나 이슈 본문이 원문임
- **확인을 요청하는 수단**: 이슈 댓글. 답할 사람의 GitHub 계정을 알면 댓글에서 멘션함

## 4. 관계자

- **요청자**: 요청한 사람. 다른 사람이 대신 전했으면 원문에 적힌 사람
- **결정할 사람**: 요청 원문이 지목한 사람. 없으면 "미정"
- **대상 서비스의 담당**: 저장소의 `CODEOWNERS`에 전체 경로(`*`)의 소유자가 있으면 그 사람. 없으면 "미정"

## 5. 이슈 상태

- 스킬은 이슈를 닫거나 다시 열지 않음. 이슈가 완료되면 사람이 닫음
