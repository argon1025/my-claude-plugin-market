#!/usr/bin/env python3
"""레포 그래프 — registry.json의 노드와 deps.json의 간선에서 주입 블록·도메인 지도를 파생한다.

노드(레포의 스택·소관·업무 영역·호스트)는 registry.json `repos.{slug}`에, 간선은 deps.json에
있고 그 둘이 정본이다. 역인덱스·도메인 간 의존 요약·인접 레포 좌표는 저장하지 않고 매번
여기서 계산한다 — 같은 사실을 사람이 쓰는 문서에도 두면 갱신 규칙이 하나 더 늘고 두 값이
갈린다.

세션 주입(render_session)과 `map` 출력(render_map)이 같은 파생 함수를 쓰기 때문에, 훅이
보여준 것과 에이전트가 명령으로 다시 본 것이 어긋나지 않는다.

로드는 관용, 검사는 엄격이다. load_registry·load_edges는 깨진 파일을 빈 값으로 돌려줘
세션 시작을 막지 않고, 필수 키·형식은 check_errors만 본다 — 훅이 종료 코드 0으로 끝나야
주입이 사라지지 않고, 데이터 품질은 스킬이 커밋 전에 check로 보장한다.

표준 라이브러리만 쓴다. 이 모듈은 pip 없는 맨 python3에서 훅이 import하므로 외부 의존을
하나라도 두면 import 실패가 곧 주입 소멸이다.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

import catalog

DEFAULT_WIKI = os.environ.get("LLM_WIKI_ROOT", "~/.ai-docs/wiki")

REGISTRY_NAME = "registry.json"
DEPS_NAME = "deps.json"

DOMAIN_RE = re.compile(r"^[a-z0-9]+-[a-z0-9-]+$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
# 간선 끝점은 `{도메인}/{레포}` 꼴이라 도메인을 나눠도 파급 조회가 끊기지 않는다.
ENDPOINT_RE = re.compile(r"^[a-z0-9]+-[a-z0-9-]+/[a-z0-9-]+$")

DOMAIN_KEYS = ("description", "access")
REPO_KEYS = ("domain", "remotes", "branch", "status", "stack", "summary", "areas", "hosts", "source")
REPO_STATUS = ("active", "excluded")
SUMMARY_LIMIT = 80
ROLE_LIMIT = 40

EDGE_KEYS = ("from", "to", "kind", "note", "source")
EDGE_REQUIRED = ("from", "to", "kind", "source")
# 방향 의미는 종류와 무관하게 하나다 — from이 to의 계약에 의존하고, to를 바꾸면 from이
# 파급 대상이다. 메시지는 발행자가 to이므로 발행자 → 소비자로 그리는 관행과 반대다.
EDGE_KINDS = ("library", "http", "message", "data")

# 출처 줄은 규약 4장과 같은 꼴이다. 등급 2종과 꼬리 날짜만 기계가 본다.
SOURCE_RE = re.compile(r"^(확인|관찰) — .+, \d{4}-\d{2}-\d{2}$")
TAIL_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\s*$")
# 영역 키 유사 중복 판정에서 지우는 문자. 같은 업무를 두 어휘로 부르면 역인덱스가 쪼개진다.
AREA_NOISE_RE = re.compile(r"[\s·/_,.\-–—()\[\]]+")

# 도메인 목록 한 줄에 싣는 영역 이름 수. 나머지는 `외 N`으로 접는다.
AREA_PREVIEW = 5


# --- 로드 ---------------------------------------------------------------


def load_registry(wiki_root: Path) -> dict:
    """`{"domains": {...}, "repos": {...}}` — 객체가 아닌 항목은 버린다.

    파생 함수가 매번 타입을 확인하지 않도록 여기서 한 번만 걸러낸다.
    """
    data = catalog.load_json(Path(wiki_root) / REGISTRY_NAME, {})
    if not isinstance(data, dict):
        data = {}
    result = {}
    for key in ("domains", "repos"):
        section = data.get(key)
        result[key] = (
            {name: info for name, info in section.items() if isinstance(info, dict)}
            if isinstance(section, dict) else {}
        )
    return result


def load_edges(wiki_root: Path) -> list[dict]:
    """deps.json의 간선. 끝점이 `{도메인}/{레포}` 꼴이 아닌 행은 버린다 — 모양 검사는 check_errors가 한다."""
    data = catalog.load_json(Path(wiki_root) / DEPS_NAME, {})
    edges = data.get("edges") if isinstance(data, dict) else None
    if not isinstance(edges, list):
        return []
    rows = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        origin, target = edge.get("from"), edge.get("to")
        if not isinstance(origin, str) or not isinstance(target, str):
            continue
        if not ENDPOINT_RE.match(origin.strip()) or not ENDPOINT_RE.match(target.strip()):
            continue
        rows.append({**edge, "from": origin.strip(), "to": target.strip()})
    return rows


def is_excluded(info: dict) -> bool:
    return (info.get("status") or "active") == "excluded"


def endpoint_domain(endpoint: str) -> str:
    return endpoint.split("/", 1)[0]


def label_for(endpoint: str, current_domain: str) -> str:
    """현재 도메인 안이면 slug만, 밖이면 `{domain}/{slug}` — 도메인 이름이 파급 판단의 신호다."""
    domain, _, slug = endpoint.partition("/")
    return slug if domain == current_domain else endpoint


# --- 파생 ---------------------------------------------------------------


def domain_areas(registry: dict, domain: str) -> list[str]:
    """그 도메인 접두를 가진 업무 영역 이름(접두 제외) 정렬 목록."""
    prefix = f"{domain}/"
    names: set[str] = set()
    for info in registry["repos"].values():
        if is_excluded(info):
            continue
        areas = info.get("areas")
        if not isinstance(areas, dict):
            continue
        for key in areas:
            if isinstance(key, str) and key.startswith(prefix) and key[len(prefix):].strip():
                names.add(key[len(prefix):].strip())
    return sorted(names)


def reverse_index(registry: dict, domain: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """[(업무 영역, [(레포 표시, 역할)])] — 요청의 업무 낱말에서 레포 집합으로 가는 유일한 경로."""
    prefix = f"{domain}/"
    rows: dict[str, list[tuple[str, str]]] = {}
    for slug, info in sorted(registry["repos"].items()):
        if is_excluded(info):
            continue
        areas = info.get("areas")
        if not isinstance(areas, dict):
            continue
        node_domain = info.get("domain") or ""
        label = slug if node_domain == domain else f"{node_domain}/{slug}"
        for key, role in areas.items():
            if not isinstance(key, str) or not key.startswith(prefix):
                continue
            name = key[len(prefix):].strip()
            if not name:
                continue
            rows.setdefault(name, []).append((label, str(role or "").strip()))
    return [(name, rows[name]) for name in sorted(rows)]


def edge_groups(edges: list[dict], domain: str, slug: str) -> tuple[list[dict], list[dict], list[dict]]:
    """(이 레포가 의존, 이 레포에 의존, 도메인의 다른 간선).

    두 묶음을 가르는 이유는 읽는 사람이 할 일이 다르기 때문이다 — 나가는 간선은 코드를
    쓰기 전 선대응 확인이고, 들어오는 간선은 계약을 바꾼 뒤 파급 확인이다.
    """
    me = f"{domain}/{slug}" if domain and slug else ""
    outgoing, incoming, others = [], [], []
    for edge in edges:
        origin, target = edge["from"], edge["to"]
        if me and origin == me:
            outgoing.append(edge)
        elif me and target == me:
            incoming.append(edge)
        elif domain in (endpoint_domain(origin), endpoint_domain(target)):
            others.append(edge)

    def key(edge: dict) -> tuple[str, str, str]:
        return edge["from"], edge["to"], str(edge.get("kind") or "")

    return sorted(outgoing, key=key), sorted(incoming, key=key), sorted(others, key=key)


def domain_links(edges: list[dict], domain: str) -> dict[str, tuple[dict[str, int], dict[str, int]]]:
    """{상대 도메인: (이 도메인이 의존하는 종류별 건수, 상대가 의존하는 종류별 건수)}."""
    links: dict[str, tuple[dict[str, int], dict[str, int]]] = {}
    for edge in edges:
        origin, target = endpoint_domain(edge["from"]), endpoint_domain(edge["to"])
        if origin == target:
            continue
        kind = str(edge.get("kind") or "?")
        if origin == domain:
            counts = links.setdefault(target, ({}, {}))[0]
        elif target == domain:
            counts = links.setdefault(origin, ({}, {}))[1]
        else:
            continue
        counts[kind] = counts.get(kind, 0) + 1
    return links


def adjacent(registry: dict, edges: list[dict], domain: str, slug: str,
             paths: dict, knowledge: Path) -> list[str]:
    """두 묶음 간선의 상대 레포를 여는 좌표 행. 로컬 경로가 없으면 remote로 clone한다."""
    me = f"{domain}/{slug}" if domain and slug else ""
    if not me:
        return []
    endpoints = {edge["to"] for edge in edges if edge["from"] == me}
    endpoints |= {edge["from"] for edge in edges if edge["to"] == me}

    rows = []
    for endpoint in sorted(endpoints):
        other_domain, _, other_slug = endpoint.partition("/")
        label = label_for(endpoint, domain)
        info = registry["repos"].get(other_slug)
        if not isinstance(info, dict) or info.get("domain") != other_domain:
            rows.append(f"- {label} — registry.json에 없음 — /llm-wiki:register")
            continue
        stack = str(info.get("stack") or "").strip() or "스택 미기재"
        summary = str(info.get("summary") or "").strip() or "소관 미기재"
        local = paths.get(other_slug) if isinstance(paths, dict) else None
        remotes = info.get("remotes")
        remote = str(remotes[0]).strip() if isinstance(remotes, list) and remotes else ""
        folder = Path(knowledge) / other_domain / other_slug
        count = len(catalog.docs(folder)) if folder.is_dir() else 0
        rows.append(
            f"- {label} — {stack} · {summary} · 로컬 {local or '없음'}"
            f" · {remote or 'remote 없음'} · 문서 {count}건"
        )
    return rows


def edge_stale(edge: dict, today: date, stale_days: int = catalog.STALE_DAYS) -> bool:
    """source 꼬리 날짜가 낡음 기준을 넘었는지. 날짜를 읽지 못하면 낡지 않은 것으로 본다."""
    match = TAIL_DATE_RE.search(str(edge.get("source") or ""))
    if not match:
        return False
    checked = catalog.parse_date(match.group(1))
    return bool(checked and (today - checked).days > stale_days)


# --- 렌더 ---------------------------------------------------------------


def edge_row(edge: dict, today: date, hide: str = "") -> str:
    """`- {kind} {from} → {to} — {note}`. hide는 비울 끝점 — 두 묶음에서 현재 레포 쪽을 지운다."""
    kind = str(edge.get("kind") or "?").strip()
    origin = "" if hide == "from" else edge["from"]
    target = "" if hide == "to" else edge["to"]
    head = " ".join(part for part in (kind, origin) if part)
    row = f"- {head} → {target}".rstrip()
    note = str(edge.get("note") or "").strip()
    if note:
        row += f" — {note}"
    if edge_stale(edge, today):
        row += " !"
    return row


def domain_line(registry: dict, edges: list[dict], name: str, against: set[str]) -> str:
    """도메인 목록 한 줄. against는 의존 집계를 낼 상대 도메인 이름 집합이다."""
    info = registry["domains"].get(name) or {}
    description = str(info.get("description") or "").strip()

    extras = []
    areas = domain_areas(registry, name)
    if areas:
        shown = areas[:AREA_PREVIEW]
        tail = f" 외 {len(areas) - len(shown)}" if len(areas) > len(shown) else ""
        extras.append("영역: " + ", ".join(shown) + tail)

    links = domain_links(edges, name)
    for other in sorted(against):
        out, inbound = links.get(other, ({}, {}))
        if out:
            extras.append(f"{other}에 의존 " + " · ".join(f"{k} {n}" for k, n in sorted(out.items())))
        if inbound:
            extras.append(f"{other}가 의존 " + " · ".join(f"{k} {n}" for k, n in sorted(inbound.items())))

    row = f"- {name}"
    if description:
        row += f" — {description}"
    if extras:
        row += (" · " if description else " — ") + " · ".join(extras)
    return row


def render_session(registry: dict, edges: list[dict], domain: str, slug: str,
                   paths: dict, knowledge: Path, today: date) -> str:
    """훅이 헤더와 문서 목록 사이에 끼우는 블록. 도메인이 없으면 도메인 목록까지만."""
    blocks: list[str] = []

    domains = sorted(registry["domains"])
    if domains:
        head = f"# 도메인 {len(domains)}개"
        if domain:
            head += f" · 현재 {domain}"
        rows = [
            domain_line(registry, edges, name, {domain} if domain and name != domain else set())
            for name in domains
        ]
        blocks.append("\n".join([head, *rows]))

    if not domain:
        return "\n\n".join(blocks)

    access = (registry["domains"].get(domain) or {}).get("access")
    if isinstance(access, list):
        rows = [f"- {str(item).strip()}" for item in access if str(item).strip()]
        if rows:
            blocks.append("\n".join([f"# 접근 좌표 · {domain}", *rows]))

    index = reverse_index(registry, domain)
    if index:
        rows = [
            f"- {area} — " + " · ".join(f"{label}({role})" if role else label for label, role in members)
            for area, members in index
        ]
        blocks.append("\n".join([
            f"# 역인덱스 · {domain} {len(index)}영역 (영역 — 레포(역할), 타 도메인 레포는 {{domain}}/{{slug}})",
            *rows,
        ]))

    outgoing, incoming, others = edge_groups(edges, domain, slug)
    lines: list[str] = []
    if outgoing:
        lines.append(f"# 이 레포가 의존 — 선행 조건 {len(outgoing)}건 (to 레포 계약이 새로 필요하면 선대응 확인)")
        lines.extend(edge_row(edge, today, hide="from") for edge in outgoing)
    if incoming:
        lines.append(f"# 이 레포에 의존 — 파급 대상 {len(incoming)}건 (변경 시 from 레포 소비 여부 확인)")
        lines.extend(edge_row(edge, today, hide="to") for edge in incoming)
    if others:
        lines.append(f"# 도메인의 다른 간선 {len(others)}건")
        lines.extend(edge_row(edge, today) for edge in others)
    if lines:
        blocks.append("\n".join(lines))

    rows = adjacent(registry, edges, domain, slug, paths, knowledge)
    if rows:
        blocks.append("\n".join([
            f"# 인접 레포 좌표 {len(rows)}건 (slug — 스택 · 소관 · 로컬 경로 · remote · 문서 건수)",
            *rows,
        ]))

    return "\n\n".join(blocks)


def render_map(registry: dict, edges: list[dict], domain: str, today: date) -> str:
    """`map` 출력. 세션에 주입되지 않는 도메인을 에이전트가 한 번에 볼 때 쓴다."""
    if domain not in registry["domains"]:
        known = ", ".join(sorted(registry["domains"])) or "없음"
        return f"# 도메인 {domain}가 registry.json에 없음 — 등록된 도메인: {known}"

    others = set(registry["domains"]) - {domain}
    blocks = [f"# {domain} 지도\n\n" + domain_line(registry, edges, domain, others)]

    access = (registry["domains"].get(domain) or {}).get("access")
    rows = [f"- {str(item).strip()}" for item in access if str(item).strip()] if isinstance(access, list) else []
    if rows:
        blocks.append("\n".join(["## 접근 좌표", "", *rows]))

    index = reverse_index(registry, domain)
    if index:
        rows = [
            f"- {area} — " + " · ".join(f"{label}({role})" if role else label for label, role in members)
            for area, members in index
        ]
        blocks.append("\n".join([f"## 역인덱스 {len(index)}영역 (영역 — 레포(역할))", "", *rows]))

    nodes = sorted(
        (slug, info) for slug, info in registry["repos"].items() if info.get("domain") == domain
    )
    active = [(slug, info) for slug, info in nodes if not is_excluded(info)]
    if active:
        rows = [
            f"| {slug} | {str(info.get('stack') or '').strip() or '—'} "
            f"| {str(info.get('summary') or '').strip() or '—'} |"
            for slug, info in active
        ]
        blocks.append("\n".join(["## 레포 구성", "", "| 레포 | 스택 | 소관 |", "|---|---|---|", *rows]))

    touching = sorted(
        (edge for edge in edges
         if domain in (endpoint_domain(edge["from"]), endpoint_domain(edge["to"]))),
        key=lambda edge: (edge["from"], edge["to"], str(edge.get("kind") or "")),
    )
    if touching:
        blocks.append("\n".join([
            f"## 의존 간선 {len(touching)}건 (kind from → to — 계약 식별자, from이 to에 의존)",
            "",
            *(edge_row(edge, today) for edge in touching),
        ]))

    excluded = [(slug, info) for slug, info in nodes if is_excluded(info)]
    if excluded:
        rows = [f"| {slug} | {str(info.get('reason') or '').strip() or '—'} |" for slug, info in excluded]
        blocks.append("\n".join(["## 제외 레포", "", "| 레포 | 사유 |", "|---|---|", *rows]))

    return "\n\n".join(blocks)


# --- 검사 ---------------------------------------------------------------


def normalize_area(name: str) -> str:
    """영역 이름을 비교 가능한 꼴로 줄인다. 공백·구두점을 지우고 소문자로 만든다."""
    return AREA_NOISE_RE.sub("", name).lower()


def check_domains(raw: dict, errors: list[tuple[str, str]]) -> None:
    for name, info in sorted(raw.items()):
        label = f"도메인 {name}"
        if not isinstance(info, dict):
            errors.append((REGISTRY_NAME, f"{label}: 항목이 객체가 아님"))
            continue
        if not DOMAIN_RE.match(name):
            errors.append((REGISTRY_NAME, f"{label}: 이름이 `{{조직}}-{{도메인}}` 꼴이 아님"))
        unknown = sorted(set(info) - set(DOMAIN_KEYS))
        if unknown:
            errors.append((REGISTRY_NAME, f"{label}: 허용되지 않는 키: {', '.join(unknown)}"))
        description = info.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append((REGISTRY_NAME, f"{label}: description 없음"))
        elif "\n" in description:
            errors.append((REGISTRY_NAME, f"{label}: description은 한 줄"))
        access = info.get("access")
        if access is not None and (
            not isinstance(access, list)
            or any(not isinstance(item, str) or not item.strip() for item in access)
        ):
            errors.append((REGISTRY_NAME, f"{label}: access는 빈 값이 없는 문자열 배열"))


def check_repos(raw: dict, domains: set[str], errors: list[tuple[str, str]]) -> None:
    hosts_owner: dict[str, str] = {}
    area_owner: dict[tuple[str, str], str] = {}

    for slug, info in sorted(raw.items()):
        label = f"레포 {slug}"
        if not isinstance(info, dict):
            errors.append((REGISTRY_NAME, f"{label}: 항목이 객체가 아님"))
            continue
        if not SLUG_RE.match(slug):
            errors.append((REGISTRY_NAME, f"{label}: slug는 소문자·숫자·하이픈만"))

        status = info.get("status")
        excluded = status == "excluded"
        missing = [key for key in REPO_KEYS if key not in info]
        if missing:
            errors.append((REGISTRY_NAME, f"{label}: 필수 키 없음: {', '.join(missing)}"))
        allowed = set(REPO_KEYS) | ({"reason"} if excluded else set())
        unknown = sorted(set(info) - allowed)
        if unknown:
            errors.append((REGISTRY_NAME, f"{label}: 허용되지 않는 키: {', '.join(unknown)}"))

        domain = info.get("domain")
        if not isinstance(domain, str) or domain not in domains:
            errors.append((REGISTRY_NAME, f"{label}: domain {domain!r}가 domains에 없음"))
        remotes = info.get("remotes")
        if not isinstance(remotes, list) or any(
            not isinstance(item, str) or not item.strip() for item in remotes
        ):
            errors.append((REGISTRY_NAME, f"{label}: remotes는 빈 값이 없는 문자열 배열"))
        branch = info.get("branch")
        if not isinstance(branch, str) or not branch.strip():
            errors.append((REGISTRY_NAME, f"{label}: branch 없음"))
        if status not in REPO_STATUS:
            errors.append((REGISTRY_NAME, f"{label}: status는 {'·'.join(REPO_STATUS)} 중 하나 (현재 {status!r})"))

        stack = info.get("stack") if isinstance(info.get("stack"), str) else ""
        summary = info.get("summary") if isinstance(info.get("summary"), str) else ""
        areas = info.get("areas") if isinstance(info.get("areas"), dict) else {}
        hosts = info.get("hosts") if isinstance(info.get("hosts"), list) else []
        if len(summary) > SUMMARY_LIMIT:
            errors.append((REGISTRY_NAME, f"{label}: summary가 {len(summary)}자 — 상한 {SUMMARY_LIMIT}자"))

        # 제외 노드는 주입·무인 갱신에서 빠지므로 지식 필드가 남아 있으면 아무도 갱신하지
        # 않는 값이 된다. 양쪽을 다 본다 — active인데 비어 있는 것도 조사 누락이다.
        if excluded:
            reason = info.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append((REGISTRY_NAME, f"{label}: status excluded인데 reason 없음"))
            if stack or summary:
                errors.append((REGISTRY_NAME, f"{label}: excluded 노드는 stack·summary가 빈 문자열"))
            if areas:
                errors.append((REGISTRY_NAME, f"{label}: excluded 노드는 areas가 빈 객체"))
            if hosts:
                errors.append((REGISTRY_NAME, f"{label}: excluded 노드는 hosts가 빈 배열"))
        elif status == "active":
            if not stack.strip():
                errors.append((REGISTRY_NAME, f"{label}: stack 없음 — /llm-wiki:register --resurvey"))
            if not summary.strip():
                errors.append((REGISTRY_NAME, f"{label}: summary 없음 — /llm-wiki:register --resurvey"))

        for key, role in sorted(areas.items()):
            if not isinstance(key, str) or key.count("/") != 1:
                errors.append((REGISTRY_NAME, f"{label}: 영역 키 {key!r}가 `{{domain}}/{{영역}}` 꼴이 아님"))
                continue
            key_domain, _, name = key.partition("/")
            if not name.strip():
                errors.append((REGISTRY_NAME, f"{label}: 영역 키 {key}의 영역 이름이 비었음"))
                continue
            if key_domain not in domains:
                errors.append((REGISTRY_NAME, f"{label}: 영역 키 {key}의 도메인이 domains에 없음"))
            if not isinstance(role, str) or not role.strip():
                errors.append((REGISTRY_NAME, f"{label}: 영역 {key}의 역할 없음"))
            elif len(role) > ROLE_LIMIT:
                errors.append((REGISTRY_NAME, f"{label}: 영역 {key}의 역할이 {len(role)}자 — 상한 {ROLE_LIMIT}자"))
            owner = area_owner.setdefault((key_domain, normalize_area(name)), key)
            if owner != key:
                errors.append((REGISTRY_NAME, f"{label}: 영역 키 {key}가 {owner}와 구두점·공백만 다름 — 하나로 통합"))

        for host in hosts:
            if not isinstance(host, str) or not host.strip():
                errors.append((REGISTRY_NAME, f"{label}: hosts에 빈 값"))
                continue
            owner = hosts_owner.setdefault(host.strip(), slug)
            if owner != slug:
                errors.append((REGISTRY_NAME, f"{label}: 호스트 {host}가 {owner}와 중복 — 무인 간선 매핑이 갈림"))

        source = info.get("source")
        if not isinstance(source, str) or not SOURCE_RE.match(source.strip()):
            errors.append((REGISTRY_NAME, f"{label}: source 형식이 아님 — `확인 — {{자료·결정}}, YYYY-MM-DD`"))


def check_deps(wiki_root: Path, registry: dict | None, errors: list[tuple[str, str]]) -> None:
    path = Path(wiki_root) / DEPS_NAME
    if not path.is_file():
        return
    data = catalog.load_json(path, None)
    if not isinstance(data, dict) or not isinstance(data.get("edges"), list):
        errors.append((DEPS_NAME, 'JSON을 읽지 못했거나 edges가 배열이 아님 — {"edges": [...]} 꼴이어야 함'))
        return

    domains = set(registry["domains"]) if registry else set()
    repos = registry["repos"] if registry else {}

    seen: dict[tuple[str, str, str], int] = {}
    for position, edge in enumerate(data["edges"], start=1):
        if not isinstance(edge, dict):
            errors.append((DEPS_NAME, f"간선 {position}: 항목이 객체가 아님"))
            continue

        ends = {key: (edge.get(key).strip() if isinstance(edge.get(key), str) else "") for key in ("from", "to")}
        kind = edge.get("kind") if isinstance(edge.get("kind"), str) else ""
        label = f"간선 {position}: {ends['from'] or '?'} → {ends['to'] or '?'}"

        unknown = sorted(set(edge) - set(EDGE_KEYS))
        if unknown:
            errors.append((DEPS_NAME, f"{label} 허용되지 않는 키: {', '.join(unknown)}"))
        for key in EDGE_REQUIRED:
            value = edge.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append((DEPS_NAME, f"{label} {key} 없음"))
        if kind and kind not in EDGE_KINDS:
            errors.append((DEPS_NAME, f"{label} kind는 {'·'.join(EDGE_KINDS)} 중 하나 (현재 {kind})"))

        for key, value in ends.items():
            if value and not ENDPOINT_RE.match(value):
                errors.append((DEPS_NAME, f"{label} {key} 형식이 아님 ({value}) — {{도메인}}/{{레포}}"))
            elif value and registry:
                domain, _, repo = value.partition("/")
                if domain not in domains:
                    errors.append((DEPS_NAME, f"{label} {key} 도메인 {domain}가 registry.json에 없음"))
                info = repos.get(repo)
                if not isinstance(info, dict) or info.get("domain") != domain:
                    errors.append((DEPS_NAME, f"{label} {key} 레포 {value}가 registry.json에 없음"))

        source = edge.get("source")
        if isinstance(source, str) and source.strip() and not SOURCE_RE.match(source.strip()):
            errors.append((DEPS_NAME, f"{label} source 형식이 아님 — `관찰 — {{식별자}}, YYYY-MM-DD`"))

        if ends["from"] and ends["from"] == ends["to"]:
            errors.append((DEPS_NAME, f"{label} 자기 간선"))
        elif ends["from"] and ends["to"]:
            # 같은 두 레포가 http와 message로 함께 이어질 수 있으므로 종류까지 묶어 본다.
            triple = (ends["from"], ends["to"], kind)
            if triple in seen:
                errors.append((DEPS_NAME, f"{label} 중복 — 간선 {seen[triple]}과 같은 (from, to, kind)"))
            else:
                seen[triple] = position


def check_errors(wiki_root: Path) -> list[tuple[str, str]]:
    """(파일, 메시지) 목록. catalog --check가 문서 에러와 함께 내고 graph check가 단독으로도 낸다."""
    wiki_root = Path(wiki_root)
    errors: list[tuple[str, str]] = []

    path = wiki_root / REGISTRY_NAME
    if not path.is_file():
        return [(REGISTRY_NAME, f"{path} 없음 — /llm-wiki:init")]

    raw = catalog.load_json(path, None)
    if not isinstance(raw, dict):
        errors.append((REGISTRY_NAME, 'JSON을 읽지 못했거나 객체가 아님 — {"domains": {}, "repos": {}} 꼴이어야 함'))
        raw = {}

    for key in ("domains", "repos"):
        if key in raw and not isinstance(raw[key], dict):
            errors.append((REGISTRY_NAME, f"{key}가 객체가 아님"))
    domains_raw = raw.get("domains") if isinstance(raw.get("domains"), dict) else {}
    repos_raw = raw.get("repos") if isinstance(raw.get("repos"), dict) else {}

    check_domains(domains_raw, errors)
    check_repos(repos_raw, set(domains_raw), errors)
    check_deps(wiki_root, load_registry(wiki_root), errors)
    return errors


# --- 레포 판정 ----------------------------------------------------------


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
    """(slug, domain)을 돌려준다. 등록되지 않았으면 domain이 None이다.

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
                    return slug, info.get("domain")
        slug = slug_from_remote(remote)
    elif common_dir:
        slug = re.sub(r"[^a-z0-9-]", "-", Path(common_dir).parent.name.lower()).strip("-")
    else:
        return "", None

    info = repos.get(slug)
    return slug, info.get("domain") if info else None


# --- CLI ----------------------------------------------------------------


def cmd_map(args) -> int:
    wiki = Path(args.wiki).expanduser()
    print(render_map(load_registry(wiki), load_edges(wiki), args.domain, date.today()))
    return 0


def cmd_check(args) -> int:
    wiki = Path(args.wiki).expanduser()
    errors = check_errors(wiki)
    for name, message in errors:
        print(f"에러  {name}: {message}")
    registry = load_registry(wiki)
    print(f"# 노드 {len(registry['repos'])}개 · 간선 {len(load_edges(wiki))}건 · 에러 {len(errors)}건")
    if errors:
        print("# 에러를 고치기 전에는 커밋하지 않는다. --no-verify로 우회하지 않는다.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="registry.json 노드와 deps.json 간선에서 도메인 지도를 파생하고 검사한다.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--wiki", metavar="PATH", default=DEFAULT_WIKI,
                        help=f"위키 저장소 (기본값: {DEFAULT_WIKI})")
    sub = parser.add_subparsers(dest="command", required=True)

    map_cmd = sub.add_parser("map", parents=[common], help="도메인 하나의 지도를 마크다운으로 낸다")
    map_cmd.add_argument("--domain", metavar="NAME", required=True, help="대상 도메인")
    map_cmd.set_defaults(func=cmd_map)

    check_cmd = sub.add_parser("check", parents=[common], help="노드·간선을 검사한다. 에러가 있으면 종료 코드 1")
    check_cmd.set_defaults(func=cmd_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
