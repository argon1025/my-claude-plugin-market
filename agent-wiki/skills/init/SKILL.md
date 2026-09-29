---
name: init
description: Clone the configured wiki repo to the wiki root, or fast-forward it if already present.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`baseRoot`·`remote`·`baseBranch`)을 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다.

## 1. 저장소 준비

`baseRoot`가 없으면 clone합니다.

```
git clone {remote} {baseRoot}
```

이미 있으면 `origin`이 `remote`와 같은지 확인하고, 다르면 중단 후 보고합니다. 같으면 상태를 확인합니다.

```
git -C {baseRoot} fetch origin {baseBranch}
git -C {baseRoot} status --short --branch
```

브랜치가 `baseBranch`가 아니거나 미커밋 변경·로컬 커밋(`ahead`)이 있으면 그 출력을 보고하고 AskUserQuestion(`변경 버리고 진행`·`중단`)으로 묻습니다. 깨끗하거나 진행을 고르면 최신화합니다.

```
git -C {baseRoot} checkout -f -B {baseBranch} origin/{baseBranch}
git -C {baseRoot} clean -fd
```

원격에 `baseBranch`가 없어 fetch가 실패하면(빈 저장소) 최신화 없이 2절로 넘어갑니다.

## 2. 스켈레톤 생성

위키 저장소가 비어 있으면 초기 구성을 진행 후 커밋합니다.

```
bash ${CLAUDE_PLUGIN_ROOT}/scripts/write_skeleton.sh {baseRoot}
git -C {baseRoot} add -A
git -C {baseRoot} commit -m "chore(init): 위키 골격"
git -C {baseRoot} branch -M {baseBranch}
git -C {baseRoot} push -u origin {baseBranch}
```

종료 코드 1이면 기존 파일이 있다는 의미이므로 중단 후 보고합니다.

## 3. 실패 처리

인증·네트워크 오류면 사용자가 `! git clone {remote} {baseRoot}`를 직접 실행하도록 안내합니다. fetch·push 실패는 해소하지 않고 원인만 보고합니다.

## 4. 보고

위키 경로, 수행 결과, `git -C {baseRoot} log -1 --oneline`을 보고합니다.
