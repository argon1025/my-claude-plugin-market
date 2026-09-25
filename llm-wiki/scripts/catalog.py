#!/usr/bin/env python3
"""위키 카탈로그 — 문서의 frontmatter를 읽어 세션 주입용 목록을 만들고 규약 위반을 검사한다.

책임은 문서 한 장의 목록과 검사까지다. 레포 노드·의존 간선(registry.json·deps.json)의
파생과 검사는 `graph.py`가 맡고, --check는 그 결과를 파일 이름으로 합쳐 낼 뿐이다.

목록은 도메인 루트(`knowledge/{조직}-{도메인}`, --shallow로 레포 폴더 제외)와 레포 폴더
(`knowledge/{도메인}/{slug}`)마다 따로 만들고, 검사는 `knowledge/` 전체를 한 번에 본다.
어느 쪽을 볼지는 --root가 정한다.

목록 모드의 핵심 규칙: 어떤 경우에도 문서를 목록에서 빼지 않는다. frontmatter 파싱에
실패하면 설명 자리에 실패 이유를 적고 행을 남긴다. 머리의 문서 수는 frontmatter가 아니라
파일 개수로 센다 — 다른 방어가 전부 실패해도 개수는 거짓말하지 않는다. 그리고 어떤
입력에도 종료 코드 0으로 끝난다. 세션 시작 훅이 이 경로를 쓰기 때문에 0이 아닌 값을
내면 카탈로그 주입이 조용히 사라진다.

--check 모드는 에러만 낸다. 경고 층을 두면 규약이 권장으로 적은 기준이 강제가 되거나
반대로 에러가 경고에 묻힌다. 사람이 판단할 것(한 주제인지·조각인지·삭제해도 되는지)은
`references/doc-contract.md`가 정본이고 이 스크립트는 기계가 볼 항목만 본다.

--check에 파일 경로를 붙이면 그 파일들의 위반만 종료 코드에 반영한다. 문서 사이를 보는
검사(description 중복)는 언제나 전체 코퍼스를 대상으로 돌린다. `registry.json`·`deps.json`은
knowledge/ 밖이라 경로 대신 파일 이름으로 받는다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_ROOT = "knowledge"
DEFAULT_LABEL = "위키"

# frontmatter는 이 키만 쓴다. description이 없으면 목록에 올릴 수 없다.
REQUIRED_FIELDS = ("description", "type")

# 문서 유형. 쓰는 쪽(update·add)이 같은 유형 문서에만 사실을 배정하도록 값을 고정한다.
# `adr`은 `adr/` 폴더 문서만 쓰고, 그 밖의 문서는 앞의 5종 중 하나다.
TYPES = ("policy", "domain", "convention", "external", "procedure", "adr")
ADR_TYPE = "adr"

DESCRIPTION_LIMIT = 60

# 규약이 허용하는 위치. knowledge/ 루트 기준 상대 경로가 이 꼴이어야 한다.
# 도메인 폴더는 `{조직}-{도메인}`이라 하이픈이 1개 이상이고, 그 아래 레포 폴더 1층만 허용한다.
# `adr/`은 도메인 루트와 레포 폴더 양쪽에 둘 수 있으며 레포 폴더 이름으로는 쓸 수 없다.
LOCATION_RE = re.compile(
    r"^(?P<domain>[a-z0-9]+-[a-z0-9-]+)(?:/(?!adr/)(?P<repo>[a-z0-9-]+))?(?:/adr)?/[a-z0-9-]+\.md$"
)

# knowledge/ 밖 형제 파일. 경로 대신 이 이름으로 --check 대상에 넣는다.
GRAPH_FILES = ("registry.json", "deps.json")

# 목록이 쓰는 토큰을 어림잡는 나눗셈 값. 한국어 섞인 목록에서 실측에 가깝다.
CHARS_PER_TOKEN = 1.8


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str, bool]:
    """(필드, 실패 이유, 블록이 깨졌는지)를 돌려준다.

    여기서 보는 것은 블록의 구조뿐이다. 파일을 읽지 못했거나, frontmatter가 없거나,
    블록이 닫히지 않은 경우에만 실패 이유가 붙고 세 번째 값이 True가 된다. 필드가
    빠졌는지 값이 규약에 맞는지는 --check가 보고, 목록 모드는 있는 것만 쓴다.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError는 OSError가 아니라 ValueError의 하위 클래스다. 여기서 놓치면
        # CP949로 저장된 문서 한 장이 목록 생성 전체를 트레이스백으로 죽인다.
        return {}, f"읽지 못함 ({type(exc).__name__})", True

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "frontmatter 없음", True

    fields: dict[str, str] = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        key = key.strip().lower()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        fields[key] = value

    if not closed:
        return fields, "frontmatter가 닫히지 않음", True

    return fields, "", False


def body_lines(path: Path) -> list[str]:
    """frontmatter 뒤의 본문 줄을 돌려준다. frontmatter가 없으면 전체를 본문으로 본다."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    if not lines or lines[0].strip() != "---":
        return lines

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[index + 1 :]
    return []


def docs(root: Path, shallow: bool = False) -> list[Path]:
    """목록·검사 대상 문서. `_`로 시작하는 파일은 초안이라 제외한다.

    shallow는 도메인 루트 목록용이다 — `root/*.md`와 `root/adr/*.md`만 모으고 레포 폴더는
    제외한다.
    """
    if shallow:
        files = list(root.glob("*.md")) + list(root.glob("adr/*.md"))
    else:
        files = list(root.rglob("*.md"))
    files = [p for p in files if not p.name.startswith("_")]
    return sorted(files, key=lambda p: sort_key(p, root))


def sort_key(path: Path, root: Path) -> tuple[bool, str]:
    """폴더 문서를 폴더별로 묶어 먼저 내고, 평면 문서를 뒤에 붙인다."""
    return (path.parent == root, path.relative_to(root).as_posix())


def estimate_tokens(text: str) -> int:
    """목록이 쓰는 토큰을 100 단위로 어림잡는다. 100에 못 미치면 0이 나온다."""
    return round(len(text) / CHARS_PER_TOKEN / 100) * 100


def build(root: Path, label: str = DEFAULT_LABEL, shallow: bool = False) -> str:
    """폴더 하나의 목록 텍스트. 경로는 그 폴더 기준 상대 경로다."""
    files = docs(root, shallow)

    rows: list[str] = []
    for path in files:
        name = path.relative_to(root).as_posix()[: -len(".md")]
        fields, reason, _ = parse_frontmatter(path)
        if reason:
            rows.append(f"{name} — !! frontmatter 파싱 실패: {reason}. 직접 읽을 것")
            continue

        description = fields.get("description", "").strip()
        if not description:
            rows.append(f"{name} — !! description 없음. 직접 읽을 것")
            continue

        # type이 없어도 행은 남긴다 — 이관 전 위키에서 목록이 비면 안 된다.
        doc_type = fields.get("type", "").strip() or "?"
        rows.append(f"{name} — [{doc_type}] {description}")

    body = "\n".join(rows)

    # 토큰 추정치를 머리에 늘 적는다. 이 목록은 매 세션과 매 압축마다 다시 주입되므로,
    # 코퍼스가 커지는 비용이 아무 곳에도 안 보이면 아무도 audit을 돌리지 않는다.
    tokens = estimate_tokens(body)
    header = f"# {label} {len(files)}건"
    if tokens:
        header += f" · 약 {tokens:,}토큰"

    if not files:
        return "\n".join([header, "", "(아직 문서가 없음)"])
    return "\n".join([header, "", body])


def in_adr(path: Path, root: Path) -> bool:
    """`adr/` 폴더 문서인지. 위치 자체가 규약 밖이면 False라 type 검사는 위치 에러에 맡긴다."""
    match = LOCATION_RE.match(path.relative_to(root).as_posix())
    return bool(match) and path.parent.name == "adr"


def check_location(path: Path, root: Path, registry: dict | None = None) -> list[str]:
    """knowledge/ 루트 기준 경로가 규약이 허용하는 꼴인지 본다.

    registry가 주어지면 도메인 폴더가 `domains`에, 레포 폴더가 `repos`에 있고 그 domain이
    폴더와 같은지도 본다. registry.json이 없거나 깨졌으면 정규식 검사만 한다.
    """
    relative = path.relative_to(root).as_posix()
    match = LOCATION_RE.match(relative)
    if not match:
        return [
            f"위치가 규약에 없음 ({relative}) — "
            "knowledge/{조직}-{도메인}/ 루트 또는 그 아래 {레포 slug}/ 평면과 각각의 adr/만, "
            "파일명은 kebab-case"
        ]
    errors: list[str] = []
    domain, repo = match.group("domain"), match.group("repo")
    if not registry:
        return errors

    if domain not in (registry.get("domains") or {}):
        errors.append(f"도메인 {domain}가 registry.json에 없음 — /llm-wiki:register")
    if repo:
        info = (registry.get("repos") or {}).get(repo)
        if not isinstance(info, dict) or info.get("domain") != domain:
            errors.append(f"레포 폴더 {repo}가 registry.json에 없거나 도메인이 다름")
    return errors


def check_body(path: Path) -> list[str]:
    """본문 첫 줄이 # 제목인지 본다. 제목은 frontmatter가 아니라 본문에만 둔다."""
    for line in body_lines(path):
        if not line.strip():
            continue
        if not line.startswith("# "):
            return ["본문 첫 줄이 # 제목이 아님"]
        return []
    return ["본문이 비어 있음"]


def check_fields(fields: dict[str, str], adr: bool = False) -> list[str]:
    """frontmatter 필드 값만 본다. adr은 문서가 `adr/` 폴더에 있는지다."""
    errors: list[str] = []

    # 미승인 키 검사는 값이 규약에 어긋나도 그대로 돌린다. `descripton:` 같은 오타는
    # "description 없음"과 함께 나와야 왜 없는지가 보인다.
    unknown = sorted(set(fields) - set(REQUIRED_FIELDS))
    if unknown:
        errors.append(f"허용되지 않은 frontmatter 키: {', '.join(unknown)}")

    for name in REQUIRED_FIELDS:
        if not fields.get(name):
            errors.append(f"{name} 없음")

    description = fields.get("description", "").strip()
    if description and len(description) > DESCRIPTION_LIMIT:
        errors.append(f"description이 {len(description)}자 — 상한 {DESCRIPTION_LIMIT}자")

    doc_type = fields.get("type", "").strip()
    if doc_type and doc_type not in TYPES:
        errors.append(f"type {doc_type}가 규약에 없음 — {', '.join(TYPES)} 중 하나")
    elif doc_type and adr and doc_type != ADR_TYPE:
        errors.append(f"adr/ 문서의 type이 {doc_type} — adr 고정")
    elif doc_type == ADR_TYPE and not adr:
        others = ", ".join(t for t in TYPES if t != ADR_TYPE)
        errors.append(f"type adr은 adr/ 폴더 문서만 — 그 밖은 {others} 중 하나")

    return errors


def inspect(path: Path, root: Path, registry: dict | None = None) -> list[str]:
    errors = check_location(path, root, registry)
    fields, reason, broken = parse_frontmatter(path)

    if broken:
        # 블록 자체가 깨졌으면 필드를 하나도 믿을 수 없어 여기서 멈춘다.
        errors.append(reason)
        return errors

    errors.extend(check_fields(fields, in_adr(path, root)))
    errors.extend(check_body(path))
    return errors


def inspect_across(files: list[Path], root: Path) -> list[tuple[str, tuple[str, ...], str]]:
    """파일 하나만 봐서는 알 수 없는 위반. (출력할 문서, 관련 문서 전부, 메시지).

    관련 문서 전부가 있어야 검사 대상을 일부 파일로 좁혔을 때, 짝이 검사 밖에 있어도
    그 위반을 빠뜨리지 않는다.

    에이전트는 오직 description으로 문서를 열지 말지 정한다. 두 문서가 같은 문장을
    달면 어느 쪽을 열지 정할 수 없어서, 규약이 가장 중요하다고 선언한 속성이 그대로
    무너진다. 정확히 같은 경우만 본다 — 어휘가 비슷한 정도의 중복은 사람이 판단한다.
    """
    findings: list[tuple[str, tuple[str, ...], str]] = []
    seen: dict[str, str] = {}

    for path in files:
        name = path.relative_to(root).as_posix()
        fields, _, broken = parse_frontmatter(path)
        description = "" if broken else fields.get("description", "").strip()
        if not description:
            continue
        owner = seen.setdefault(description, name)
        if owner != name:
            findings.append((
                name,
                (name, owner),
                f"description이 {owner}와 같음 — 트리거가 겹치면 어느 문서를 열지 정할 수 없음",
            ))

    return findings


def selected_names(root: Path, paths: list[str]) -> set[str] | None:
    """검사 대상으로 좁힐 문서 이름 집합. 경로를 주지 않으면 None(전체)."""
    if not paths:
        return None

    names: set[str] = set()
    # registry.json·deps.json은 knowledge/ 밖이라 상대 경로 변환에서 버려진다. 이름으로 따로 받는다.
    graph_files = {(root.parent / name).resolve(): name for name in GRAPH_FILES}
    for raw in paths:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        if resolved in graph_files:
            names.add(graph_files[resolved])
            continue
        try:
            names.add(resolved.relative_to(root.resolve()).as_posix())
        except ValueError:
            # 검사 범위 밖의 파일은 조용히 무시한다. 커밋에는 위키 문서가 아닌
            # 파일이 함께 담기는 것이 정상이다.
            continue
    return names


def check(root: Path, only: set[str] | None = None) -> int:
    files = docs(root)

    # 노드·간선은 문서가 아니라 knowledge/의 형제 파일이라, 문서가 한 장도 없어도 검사한다.
    # graph는 여기서만 쓰므로 함수 안에서 import한다 — graph도 catalog를 쓰기 때문에
    # 모듈 수준에서 서로 import하면 graph.py를 직접 실행할 때 모듈이 두 번 적재된다.
    import graph

    # registry.json은 knowledge/의 형제이고 노드가 도메인 아래 중첩이라, 폴더-등록 대조가
    # 쓰는 평탄화 인덱스는 graph.load_registry가 만든다. 파일이 없으면 빈 인덱스가 온다.
    registry = graph.load_registry(root.parent)
    if not registry["domains"] and not registry["repos"]:
        registry = None

    graph_errors = [
        (name, message) for name, message in graph.check_errors(root.parent)
        if only is None or name in only
    ]

    if not files and not graph_errors:
        print(f"# 검사할 문서가 없음: {root}")
        return 0

    errors: list[tuple[str, str]] = list(graph_errors)
    for path in files:
        name = path.relative_to(root).as_posix()
        if only is not None and name not in only:
            continue
        errors.extend((name, message) for message in inspect(path, root, registry))

    for name, involved, message in inspect_across(files, root):
        if only is None or only & set(involved):
            errors.append((name, message))

    for name, message in errors:
        print(f"에러  {name}: {message}")

    scanned = len(files) if only is None else len(only)
    print(f"# 문서 {scanned}건 · 에러 {len(errors)}건")
    if errors:
        print("# 에러를 고치기 전에는 커밋하지 않는다. --no-verify로 우회하지 않는다.")
        return 1
    return 0


def load_json(path: Path, fallback):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser(
        description="위키 문서 목록을 세션 주입용 텍스트로 출력한다.",
    )
    parser.add_argument("--root", metavar="PATH", default=DEFAULT_ROOT,
                        help=f"문서 디렉토리 (기본값: {DEFAULT_ROOT})")
    parser.add_argument("--label", metavar="TEXT", default=DEFAULT_LABEL,
                        help=f"목록 머리에 붙는 이름 (기본값: {DEFAULT_LABEL})")
    parser.add_argument("--shallow", action="store_true",
                        help="도메인 루트 목록: --root 바로 아래 *.md와 adr/*.md만, 레포 폴더 제외")
    parser.add_argument("--check", action="store_true",
                        help="목록 대신 규약 위반을 검사한다. --root는 knowledge/여야 한다. 에러가 있으면 종료 코드 1.")
    parser.add_argument("paths", nargs="*", metavar="PATH",
                        help="--check 대상을 이 파일들로 좁힌다. 문서 사이 검사는 전체를 본다.")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"# 문서 디렉토리를 찾지 못함: {root}")
        return 1

    if args.check:
        return check(root, selected_names(root, args.paths))

    print(build(root, args.label, args.shallow))
    return 0


if __name__ == "__main__":
    sys.exit(main())
