#!/bin/bash
# 빈 위키 저장소에 골격 파일 4종(registry.json·deps.json·knowledge/.gitkeep·.gitignore)을 작성한다.
# 커밋·push는 호출한 스킬이 git으로 수행하므로 여기서는 파일 작성만 맡는다.
# 기존 파일을 덮어쓰지 않도록 대상이 하나라도 있으면 아무것도 쓰지 않고 1로 끝낸다.
set -euo pipefail

ROOT="${1:?usage: write_skeleton.sh <wiki-root>}"
FILES=(registry.json deps.json knowledge/.gitkeep .gitignore)

for f in "${FILES[@]}"; do
  if [ -e "$ROOT/$f" ]; then
    echo "already exists: $ROOT/$f" >&2
    exit 1
  fi
done

mkdir -p "$ROOT/knowledge"
printf '{"domains": {}}\n' > "$ROOT/registry.json"
printf '{"deps": {}}\n' > "$ROOT/deps.json"
: > "$ROOT/knowledge/.gitkeep"
printf '.local/\n' > "$ROOT/.gitignore"

printf '%s\n' "${FILES[@]}"
