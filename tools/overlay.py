#!/usr/bin/env python3
"""변형 플러그인 생성 — 개인판 플러그인(base)에 오버레이를 얹어 출력 플러그인 폴더를 만든다.

오버레이는 overlay.json(`{"replace": {"원문": "대체문"}}`)과 base와 같은 상대 경로의 교체 파일이다.
교체 파일은 통째로 바꾸고(`.claude-plugin/plugin.json`만 얕은 병합), base에서 온 나머지 텍스트
파일에는 문자열 치환을 건다. 개인판이 버전업하며 파일 이름·문구·절 제목을 바꾸면 오버레이가
조용히 어긋나므로, 그 세 가지 드리프트는 모두 에러로 멈춘다.

치환은 교체 파일과 병합한 plugin.json에 걸지 않는다 — 교체 파일은 이미 변형 표기라, 원문이
대체문 안에 들어 있으면(`LLM_WIKI_` ⊂ `ACME_LLM_WIKI_`) 이중 치환이 생긴다.

출력은 임시 폴더에 전부 만든 뒤 검사가 통과해야 기존 출력과 바꾼다 — 에러가 나면 기존 출력은
그대로다. 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

MANIFEST = ".claude-plugin/plugin.json"
OVERLAY_SPEC = "overlay.json"
SKIP_DIRS = {"__pycache__"}
SKIP_NAMES = {".DS_Store"}


def collect(root: Path) -> dict[str, Path]:
    """상대 경로(POSIX) → 파일. 캐시·OS 부산물은 뺀다."""
    files = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or SKIP_DIRS & set(rel.parts[:-1]) or path.name in SKIP_NAMES or path.suffix == ".pyc":
            continue
        files[rel.as_posix()] = path
    return files


def headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


def load_spec(path: Path, errors: list[str]) -> dict[str, str]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"{OVERLAY_SPEC}: 읽지 못함 — {exc}")
        return {}
    if not isinstance(spec, dict):
        errors.append(f'{OVERLAY_SPEC}: {{"replace": {{...}}}} 꼴의 객체가 아님')
        return {}
    unknown = sorted(set(spec) - {"replace"})
    if unknown:
        errors.append(f"{OVERLAY_SPEC}: 허용되지 않는 최상위 키: {', '.join(unknown)}")
    table = spec.get("replace", {})
    if not isinstance(table, dict) or not all(isinstance(k, str) and k and isinstance(v, str) for k, v in table.items()):
        errors.append(f"{OVERLAY_SPEC}: replace는 빈 문자열이 아닌 원문 → 대체문 문자열 객체")
        return {}
    return table


def check_out(base: Path, overlay: Path, out: Path, errors: list[str]) -> None:
    """출력이 입력을 덮거나 입력 안에 생기지 않고, 지울 기존 폴더가 플러그인일 때만 통과."""
    for name, src in (("base", base), ("overlay", overlay)):
        if out == src or out.is_relative_to(src) or src.is_relative_to(out):
            errors.append(f"--out {out}가 {name} {src}와 같거나 포함 관계")
    if out.exists() and not (out / MANIFEST).is_file():
        errors.append(f"--out {out}가 있으나 {MANIFEST}가 없음 — 플러그인 폴더만 교체함")


def build(base: Path, overlay: Path, tmp: Path, errors: list[str]) -> tuple[int, list[str], dict[str, int]]:
    """tmp에 출력 전체를 쓴다. 파일 수, 교체 파일 목록, 키별 적중 수를 돌려준다."""
    table = load_spec(overlay / OVERLAY_SPEC, errors)
    base_files = collect(base)
    replaced = {rel: path for rel, path in collect(overlay).items() if rel != OVERLAY_SPEC}

    for rel in sorted(set(replaced) - set(base_files)):
        errors.append(f"교체 파일 {rel}이 base에 없음 — 개인판에서 이름이 바뀌었는지 확인")
    for rel in sorted(set(replaced) & set(base_files)):
        if not rel.endswith(".md") or Path(rel).name == "README.md":
            continue
        want = headings(base_files[rel].read_text(encoding="utf-8"))
        got = headings(replaced[rel].read_text(encoding="utf-8"))
        if want != got:
            errors.append(f"교체 파일 {rel}의 `## ` 절 제목이 base와 다름\n  base: {want}\n  overlay: {got}")

    # 긴 키부터 교대 패턴 하나로 한 번에 치환한다 — 키별로 차례로 걸면 앞 치환의 결과를 뒤 키가
    # 다시 치환하는 연쇄가 생긴다.
    hits = dict.fromkeys(table, 0)
    pattern = re.compile("|".join(re.escape(key) for key in sorted(table, key=len, reverse=True))) if table else None

    def substitute(match: re.Match) -> str:
        hits[match.group(0)] += 1
        return table[match.group(0)]

    for rel, src in base_files.items():
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel == MANIFEST and rel in replaced:
            try:
                merged = {**json.loads(src.read_text(encoding="utf-8")),
                          **json.loads(replaced[rel].read_text(encoding="utf-8"))}
            except ValueError as exc:
                errors.append(f"{MANIFEST}: JSON을 읽지 못함 — {exc}")
                continue
            dest.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            shutil.copymode(replaced[rel], dest)
        elif rel in replaced:
            shutil.copy2(replaced[rel], dest)
        else:
            data = src.read_bytes()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                dest.write_bytes(data)
            else:
                dest.write_bytes((pattern.sub(substitute, text) if pattern else text).encode("utf-8"))
            shutil.copymode(src, dest)

    for key, count in hits.items():
        if not count:
            errors.append(f"치환 원문 {key!r}이 base에 한 번도 없음 — 개인판 문구가 바뀌었는지 확인")
    return len(base_files), sorted(set(replaced) & set(base_files)), hits


def main() -> int:
    parser = argparse.ArgumentParser(description="개인판 플러그인에 오버레이를 얹어 변형 플러그인 폴더를 만든다")
    parser.add_argument("--base", required=True, help="개인판 플러그인 폴더")
    parser.add_argument("--overlay", required=True, help=f"{OVERLAY_SPEC}와 교체 파일이 있는 오버레이 폴더")
    parser.add_argument("--out", required=True, help="출력 플러그인 폴더 — 있으면 통째로 교체")
    args = parser.parse_args()
    base, overlay, out = (Path(p).expanduser().resolve() for p in (args.base, args.overlay, args.out))

    errors: list[str] = []
    if not (base / MANIFEST).is_file():
        errors.append(f"--base {base}에 {MANIFEST}가 없음")
    if not (overlay / OVERLAY_SPEC).is_file():
        errors.append(f"--overlay {overlay}에 {OVERLAY_SPEC}가 없음")
    check_out(base, overlay, out, errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{out.name}.", dir=out.parent))
    try:
        shutil.copymode(base, tmp)  # mkdtemp는 0700이라 그대로 두면 출력 폴더가 소유자 전용이 된다
        count, replaced, hits = build(base, overlay, tmp, errors)
    except (OSError, ValueError) as exc:
        errors.append(f"생성 실패 — {exc}")
    if errors:
        shutil.rmtree(tmp, ignore_errors=True)
        print("\n".join(errors), file=sys.stderr)
        return 1

    if out.exists():
        shutil.rmtree(out)
    tmp.replace(out)
    print(f"{out} — 파일 {count}개")
    print(f"교체 파일: {', '.join(replaced) or '없음'}")
    for key, value in hits.items():
        print(f"치환 {key!r}: {value}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
