# 위키 게시 절차

update·add 스킬이 위키 원격 호스트와 주고받는 절차만 담습니다. update는 PR로 제안하고(1·2장), add는 PR 없이 기준 브랜치에 바로 올립니다(3장). 위키 원격 호스트를 바꾸면 이 파일만 고칩니다. 현재 절차는 GitHub `gh` CLI 기준이며, 명령은 모두 위키 clone `{tmp}`에서 실행합니다.

## 1. 열린 update PR

update는 시작할 때와 게시 직전에 확인합니다. 준비할 때 위키 clone의 전체 HEAD SHA를 `{base}`로 보관합니다. GitHub에서는 다음과 같이 열린 PR을 마지막 페이지까지 읽습니다. 명령이 실패하면 멈춥니다. 이전 실행 결과를 사용하지 않습니다.

```sh
gh api --paginate --slurp 'repos/{owner}/{repo}/pulls?state=open&per_page=100' > "{work}/open-prs.json" &&
git -C "{tmp}" fetch origin "refs/heads/{baseBranch}:refs/remotes/origin/{baseBranch}" &&
python3 "{PLUGIN_ROOT}/scripts/check_update_publication.py" --wiki "{tmp}" --base "{base}" --base-branch "{baseBranch}" --open-prs "{work}/open-prs.json"
```

게시 직전에는 같은 조회를 다시 하고 마지막 명령에 `--ready`를 붙입니다. 같은 기준 브랜치에 다른 PR(수동 PR, 이전 판의 add가 올린 PR)이 열려 있다면 그 판본의 실제 diff를 읽습니다. 같은 정책의 대상·조건·기존값·새값·원문 판본과 문서 이동을 이번 변경과 대조합니다. 해당 도메인을 건드리지 않았다면 변경 경로만 확인합니다. `{work}/compared.json`에 PR URL을 키로 `{"sha":"조회한 head SHA","overlap":false,"reason":"확인한 파일과 주장"}`을 적고 게시 직전 검사에 `--compared "{work}/compared.json"`을 넘깁니다. 중복되는 행은 `overlap:true`로 표시합니다. 일부만 중복되면 해당 주장과 이에 의존하는 커서를 빼고 남은 독립 변경을 다시 검토할 수 있습니다. 중복 결론을 적용하기 전에 PR 목록과 head를 새로 읽습니다. 판본이 바뀌거나 조회가 실패하면 게시하지 않습니다.

종료 코드 10이면 기존 PR 링크나 변경 없음 사유를 보고하고 종료합니다. 1이면 조회 오류 또는 판본 변경 사유를 보고하며 게시하지 않습니다. 호스트가 다르면 해당 호스트에서 전체 목록을 읽어 `{"complete":true,"pulls":[{"head":"소스","base":"대상","url":"PR 주소","sha":"head SHA"}]}` 형식으로 넘깁니다.

## 2. update의 PR 게시

`{branch}`는 update가 만든 `wiki-update/{domain}-{base 전체 SHA}`이고, 제목은 `update({domain}): {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장`입니다.

게시 직전 검사 후, 같은 저장소·소스·대상의 PR 이력을 먼저 읽습니다. 브랜치가 삭제된 경우에도 닫힌 PR을 확인합니다. 조회가 실패하면 게시를 중단합니다.

```sh
gh pr list --head "{branch}" --base "{baseBranch}" --state all --json number,state,headRefOid,url
```

- 열린 PR이 있으면 링크를 반환합니다. 이미 반영된 제안이면 종료합니다.
- 미병합으로 닫힌 PR은 `refs/pull/{번호}/head`를 fetch해 조회한 `headRefOid`와 일치하는지 확인한 뒤 그 트리를 이번 `HEAD^{tree}`와 비교합니다. 같은 제안은 닫힌 PR 링크를 반환합니다. 결과 트리가 다른 새 제안은 `wiki-update/{domain}-{base 전체 SHA}-after-{닫힌 PR 번호}`를 사용하고 그 브랜치의 이력부터 다시 확인합니다. 여러 건이면 가장 최근에 닫힌 PR을 기준으로 하되 동일한 트리의 이력이 있으면 해당 링크를 반환합니다.
- 해당 소스·대상에 PR 이력이 없으면 원격 브랜치 생성을 시도합니다.

```sh
git -C "{tmp}" push --porcelain "--force-with-lease=refs/heads/{branch}:" -u origin "HEAD:refs/heads/{branch}"
```

push 결과의 대상 ref 표시가 `*`이면 새 브랜치가 생성된 것입니다. `=`(같은 커밋)이거나 기존 ref와 충돌하면 PR 이력을 다시 확인합니다. PR 없이 push만 된 브랜치는 원격 tip을 fetch해 이번 제안과 기준 커밋·결과 트리가 모두 같을 때만 게시를 재개합니다. 원격 조회 실패, 다른 트리, 그 밖의 push 오류는 보고하고 종료합니다.

새 브랜치 생성 또는 게시 재개를 확인한 뒤 PR을 만듭니다. 응답이 유실되면 같은 소스·대상의 PR 이력을 다시 확인합니다.

```sh
gh pr create --base "{baseBranch}" --head "{branch}" --title "{제목}" --body-file "{work}/pr.md"
```

본문이 60,000바이트를 넘으면 본문을 "사실 목록은 첫 코멘트" 한 줄로 바꿔 PR을 만든 뒤 `{work}/pr.md`를 코멘트로 올립니다.

```
gh pr comment {url} --body-file {work}/pr.md
```

실패하면 단계·브랜치 이름·오류 한 줄을 보고합니다.

## 3. add의 바로 반영

add는 PR을 만들지 않습니다. 임시 clone의 `{baseBranch}`에 쌓은 커밋을 원격 기준 브랜치로 바로 올립니다. `{base}`는 add가 clone 직후에 보관한 HEAD SHA입니다.

```sh
git -C "{tmp}" push origin "HEAD:refs/heads/{baseBranch}"
```

원격이 앞서 있어 push가 거부되면 원격을 받아 그사이 들어온 변경을 봅니다.

```sh
git -C "{tmp}" fetch origin "refs/heads/{baseBranch}:refs/remotes/origin/{baseBranch}" &&
git -C "{tmp}" diff --name-only "{base}" "origin/{baseBranch}"
```

- **겹치지 않음**: 들어온 변경이 이번에 고친 문서(`git -C "{tmp}" diff --name-only "{base}" HEAD`)를 건드리지 않았고, 같은 도메인의 다른 문서에 이번 사실과 대상·조건이 같은 정책 문장을 더하거나 고치지도 않았으면 아래 명령으로 원격 위에 다시 올리고 push를 다시 시도함
- **겹침**: 이번에 고친 문서나 같은 정책을 들어온 변경이 건드렸으면 그 문서를 고친 이번 커밋은 다시 올리지 않음. `git -C "{tmp}" reset --hard "origin/{baseBranch}"`로 원격에 맞춘 뒤 겹치지 않는 문서의 커밋만 `git cherry-pick`으로 다시 얹고, 겹친 문서에 배정했던 사실은 `apply.md` 1~5장과 7장을 원격의 새 내용 위에서 다시 실행함. `registry.json`·`deps.json`이 겹치면 `apply.md` 6장을 다시 실행함
- **충돌**: 다시 올리다가 충돌하면 `git -C "{tmp}" rebase --abort`(cherry-pick이면 `--abort`)로 되돌리고 push하지 않은 채 충돌한 문서와 `{tmp}`·`{work}` 경로를 보고함
- **그 밖의 거부**: 권한이나 브랜치 보호로 거부되면 다시 시도하지 않고 원인과 `{tmp}`·`{work}` 경로를 보고함

```sh
git -C "{tmp}" rebase "origin/{baseBranch}"
```

push가 받아들여지면 원격을 다시 읽어 이번 커밋이 기준 브랜치에 들어갔는지 확인하고, 확인한 뒤에만 반영을 보고합니다.

```sh
git -C "{tmp}" fetch origin "refs/heads/{baseBranch}:refs/remotes/origin/{baseBranch}" &&
git -C "{tmp}" merge-base --is-ancestor HEAD "origin/{baseBranch}"
```

## 4. 인증 실패

`gh` 인증 오류면 사용자가 `! gh auth login`을 마친 뒤 스킬을 다시 실행하도록 안내합니다. add의 push가 인증 오류로 거부되면 위키 원격의 git 인증을 마친 뒤 다시 실행하도록 안내합니다.
