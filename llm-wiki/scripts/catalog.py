#!/usr/bin/env python3
"""위키 카탈로그 — 문서의 frontmatter를 읽어 세션 주입용 목록을 만들고 규약 위반을 검사한다.

스페이스(`knowledge/common`, `knowledge/projects/{p}`)마다 목록을 따로 만들고, 검사는
`knowledge/` 전체를 한 번에 본다. 어느 쪽을 볼지는 --root가 정한다.

목록 모드의 핵심 규칙: 어떤 경우에도 문서를 목록에서 빼지 않는다. frontmatter 파싱에
실패하면 설명 자리에 실패 이유를 적고 행을 남긴다. 머리의 문서 수는 frontmatter가 아니라
파일 개수로 센다 — 다른 방어가 전부 실패해도 개수는 거짓말하지 않는다. 그리고 어떤
입력에도 종료 코드 0으로 끝난다. 세션 시작 훅이 이 경로를 쓰기 때문에 0이 아닌 값을
내면 카탈로그 주입이 조용히 사라진다.

--check 모드는 에러만 낸다. 경고 층을 두면 규약이 권장으로 적은 기준이 강제가 되거나
반대로 에러가 경고에 묻힌다. 사람이 판단할 것(한 주제인지·조각인지·삭제해도 되는지)은
`references/doc-contract.md`가 정본이고 이 스크립트는 기계가 볼 항목만 본다.

--check에 파일 경로를 붙이면 그 파일들의 위반만 종료 코드에 반영한다. 문서 사이를 보는
검사(description 중복)는 언제나 전체 코퍼스를 대상으로 돌린다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_ROOT = "knowledge"
DEFAULT_LABEL = "스페이스"
# 마지막 확인이 이 일수를 넘으면 목록에 `!`가 붙는다. 낡음 기준의 유일한 출처다.
STALE_DAYS = 180

# frontmatter는 이 3키만 쓴다. 하나라도 없으면 에러다 — description이 없으면 목록에
# 올릴 수 없고, updated·verified가 없으면 낡았는지 볼 수 없다.
REQUIRED_FIELDS = ("description", "updated", "verified")
DATE_FIELDS = ("updated", "verified")
# 낡음 판정에 쓸 날짜를 이 순서로 찾는다. verified는 "지금도 맞는지 확인한 날"이다.
STALENESS_FIELDS = ("verified", "updated")

DESCRIPTION_LIMIT = 60

# 규약이 허용하는 위치. knowledge/ 루트 기준 상대 경로가 이 꼴이어야 한다.
LOCATION_RE = re.compile(r"^(common|projects/[a-z0-9-]+)(/adr)?/[a-z0-9-]+\.md$")

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


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def staleness_date(fields: dict[str, str]) -> date | None:
    """낡음 판정에 쓸 날짜. verified가 없으면 updated."""
    for name in STALENESS_FIELDS:
        parsed = parse_date(fields.get(name, ""))
        if parsed:
            return parsed
    return None


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


def docs(root: Path) -> list[Path]:
    """목록·검사 대상 문서. `_`로 시작하는 파일은 초안이라 제외한다."""
    files = [p for p in root.rglob("*.md") if not p.name.startswith("_")]
    return sorted(files, key=lambda p: sort_key(p, root))


def sort_key(path: Path, root: Path) -> tuple[bool, str]:
    """폴더 문서를 폴더별로 묶어 먼저 내고, 평면 문서를 뒤에 붙인다."""
    return (path.parent == root, path.relative_to(root).as_posix())


def estimate_tokens(text: str) -> int:
    """목록이 쓰는 토큰을 100 단위로 어림잡는다. 100에 못 미치면 0이 나온다."""
    return round(len(text) / CHARS_PER_TOKEN / 100) * 100


def build(root: Path, today: date, label: str = DEFAULT_LABEL, stale_days: int = STALE_DAYS) -> str:
    """스페이스 하나의 목록 텍스트. 경로는 스페이스 루트 기준 상대 경로다."""
    files = docs(root)

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

        checked = staleness_date(fields)
        mark = "!" if checked and (today - checked).days > stale_days else ""
        rows.append(f"{name}{mark} — {description}")

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


def check_location(path: Path, root: Path) -> list[str]:
    """knowledge/ 루트 기준 경로가 규약이 허용하는 꼴인지 본다."""
    relative = path.relative_to(root).as_posix()
    if LOCATION_RE.match(relative):
        return []
    return [
        f"위치가 규약에 없음 ({relative}) — "
        "common/ 또는 projects/{프로젝트}/ 평면과 그 adr/ 하위만, 파일명은 kebab-case"
    ]


def check_body(path: Path) -> list[str]:
    """본문 첫 줄이 # 제목인지 본다. 제목은 frontmatter가 아니라 본문에만 둔다."""
    for line in body_lines(path):
        if not line.strip():
            continue
        if not line.startswith("# "):
            return ["본문 첫 줄이 # 제목이 아님"]
        return []
    return ["본문이 비어 있음"]


def check_fields(fields: dict[str, str], today: date) -> list[str]:
    """frontmatter 필드 값만 본다."""
    errors: list[str] = []

    # 미승인 키 검사는 값이 규약에 어긋나도 그대로 돌린다. `verifed:` 같은 오타는
    # "verified 없음"과 함께 나와야 왜 없는지가 보인다.
    unknown = sorted(set(fields) - set(REQUIRED_FIELDS))
    if unknown:
        errors.append(f"허용되지 않은 frontmatter 키: {', '.join(unknown)}")

    for name in REQUIRED_FIELDS:
        if not fields.get(name):
            errors.append(f"{name} 없음")

    for name in DATE_FIELDS:
        raw = fields.get(name)
        if not raw:
            continue
        value = parse_date(raw)
        if value is None:
            errors.append(f"{name} 값이 YYYY-MM-DD 형식이 아님 ({raw})")
        elif value > today:
            errors.append(f"{name}가 미래 날짜 ({raw})")

    description = fields.get("description", "").strip()
    if description and len(description) > DESCRIPTION_LIMIT:
        errors.append(f"description이 {len(description)}자 — 상한 {DESCRIPTION_LIMIT}자")

    return errors


def inspect(path: Path, root: Path, today: date) -> list[str]:
    errors = check_location(path, root)
    fields, reason, broken = parse_frontmatter(path)

    if broken:
        # 블록 자체가 깨졌으면 필드를 하나도 믿을 수 없어 여기서 멈춘다.
        errors.append(reason)
        return errors

    errors.extend(check_fields(fields, today))
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
    for raw in paths:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        try:
            names.add(candidate.resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            # 검사 범위 밖의 파일은 조용히 무시한다. 커밋에는 위키 문서가 아닌
            # 파일이 함께 담기는 것이 정상이다.
            continue
    return names


def check(root: Path, today: date, only: set[str] | None = None) -> int:
    files = docs(root)
    if not files:
        print(f"# 검사할 문서가 없음: {root}")
        return 0

    errors: list[tuple[str, str]] = []
    for path in files:
        name = path.relative_to(root).as_posix()
        if only is not None and name not in only:
            continue
        errors.extend((name, message) for message in inspect(path, root, today))

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


def normalize_remote(url: str) -> str:
    """remote URL을 비교 가능한 꼴로 줄인다. scheme·자격증명·`.git`·대소문자를 지운다."""
    text = url.strip().lower()
    _, separator, rest = text.partition("://")
    text = rest if separator else text
    text = text.split("@", 1)[-1]
    if not separator:
        # scp 문법(`host:owner/repo`)의 콜론은 포트가 아니라 경로 구분자다.
        text = text.replace(":", "/", 1)
    text = re.sub(r"\.git$", "", text)
    return text.strip("/")


def slug_from_remote(url: str) -> str:
    """remote URL의 마지막 경로 요소에서 slug를 만든다."""
    tail = normalize_remote(url).rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^a-z0-9-]", "-", tail).strip("-")


def resolve_repo(registry: dict, remote: str, common_dir: str) -> tuple[str, str | None]:
    """(slug, project)를 돌려준다. 등록되지 않았으면 project가 None이다.

    등록 매칭은 정규화한 remote가 `remotes` 배열 중 하나와 같은지로 하고, 못 찾으면
    slug로 한 번 더 본다. owner를 slug에 넣지 않기 때문에 포크와 원본이 같은 slug로
    모이고, 워크트리도 본 저장소와 같은 slug가 된다.
    """
    repos = registry.get("repos", {}) if isinstance(registry, dict) else {}

    if remote:
        target = normalize_remote(remote)
        for slug, info in repos.items():
            for candidate in info.get("remotes", []) or []:
                if normalize_remote(candidate) == target:
                    return slug, info.get("project")
        slug = slug_from_remote(remote)
    elif common_dir:
        slug = re.sub(r"[^a-z0-9-]", "-", Path(common_dir).parent.name.lower()).strip("-")
    else:
        return "", None

    info = repos.get(slug)
    return slug, info.get("project") if info else None


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
                        help=f"목록 머리에 붙는 스페이스 이름 (기본값: {DEFAULT_LABEL})")
    parser.add_argument("--stale-days", metavar="N", type=int, default=STALE_DAYS,
                        help=f"마지막 확인이 며칠 넘으면 낡은 것으로 볼지 (기본값: {STALE_DAYS})")
    parser.add_argument("--check", action="store_true",
                        help="목록 대신 규약 위반을 검사한다. --root는 knowledge/여야 한다. 에러가 있으면 종료 코드 1.")
    parser.add_argument("paths", nargs="*", metavar="PATH",
                        help="--check 대상을 이 파일들로 좁힌다. 문서 사이 검사는 전체를 본다.")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"# 문서 디렉토리를 찾지 못함: {root}")
        return 1
    if args.stale_days < 1:
        print("# --stale-days는 1 이상이어야 한다")
        return 1

    if args.check:
        return check(root, date.today(), selected_names(root, args.paths))

    print(build(root, date.today(), args.label, args.stale_days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
