#!/usr/bin/env python3
"""레포 그래프 — registry.json의 노드와 deps.json의 간선에서 주입 블록·도메인 지도를 파생한다.

노드(레포의 스택·소관·책임·호스트)는 registry.json `domains.{d}.repos.{slug}`에, 간선은
deps.json `deps.{from}[]`에 있고 그 둘이 정본이다. 레포 지도(도메인별 레포와 책임·소관,
owner)와 좌표 패턴(미러 경로·clone URL의 공통 규칙과 예외)은 저장하지 않고
매번 여기서 계산한다 — 같은 사실을 사람이 쓰는 문서에도 두면 갱신 규칙이 하나 더 늘고 두
값이 갈린다.

세션 주입(render_session)·`repo` 출력(render_repo)·`map` 출력(render_map)이 같은 파생
함수를 쓰기 때문에, 훅이 보여준 것과 에이전트가 명령으로 다시 본 것이 어긋나지 않는다.
`render` 서브커맨드가 훅과 같은 함수를 CLI로 내므로 주입 형상은 명령 하나로 확인된다.
세션에는 지도와 현재 레포 기준 간선만 싣고, 스택·호스트·remote·문서 목록처럼 작업마다
필요하지 않은 것은 `repo {slug}`로 넘긴다.

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
from pathlib import Path

import catalog

DEFAULT_WIKI = os.environ.get("LLM_WIKI_ROOT", "~/.ai-docs/wiki")

REGISTRY_NAME = "registry.json"
DEPS_NAME = "deps.json"

DOMAIN_RE = re.compile(r"^[a-z0-9]+-[a-z0-9-]+$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
# 간선 끝점은 `{도메인}/{레포}` 꼴이라 도메인을 나눠도 파급 조회가 끊기지 않는다.
ENDPOINT_RE = re.compile(r"^[a-z0-9]+-[a-z0-9-]+/[a-z0-9-]+$")
# owner URL(`https://{host}/{owner}`). 마지막 경로 요소가 owner라 경로는 정확히 한 단계다.
PROJECT_RE = re.compile(r"^https?://[^\s/]+/[^\s/]+$")

DOMAIN_KEYS = ("description", "repos")
REPO_KEYS = ("project", "remote", "defaultBranch", "status", "stack", "summary",
             "responsibilities", "hosts")
# dormant는 신규 개발이 없을 뿐 소비처가 남아 있을 수 있어, 지식 필드를 비우지 않는다.
REPO_STATUS = ("active", "dormant")
SUMMARY_LIMIT = 80
# 책임 문장. 목표는 30자 내외이고 이 값은 두 사실이 한 줄에 눌렸는지 가르는 상한이다.
RESP_LIMIT = 40
# 책임 문장 건수에는 상한을 두지 않는다 — 레포가 맡은 일의 수는 레포마다 다르고, 큰 API
# 레포는 실제로 십수 건을 맡는다. 숫자로 끊으면 사실을 버리는 쪽이 먼저다.
# 스택은 코드로 확인되는 사실이라 전수가 아니라 감만 잡는다.
STACK_MAX = 5

HOST_ENVS = ("qa", "stg", "prod")

# 간선은 from 기준 그룹 맵이라 from은 그룹 키가 지고 항목에는 적지 않는다.
EDGE_KEYS = ("to", "kind", "contracts")
# 방향 의미는 종류와 무관하게 하나다 — from이 to의 계약에 의존하고, to를 바꾸면 from이
# 파급 대상이다. 메시지는 리스너를 가진 쪽이 to이고, 큐·익스체인지 이름에는 소유 레포
# 정보가 없으므로 상대는 후보 레포의 소비 설정을 열어 정한다.
EDGE_KINDS = ("library", "http", "message", "data")
# 의존 하나에 적는 계약 식별자 수. 넘으면 접두나 묶음 표현으로 접는다 — 라우트가 늘 때마다
# 간선을 갱신하지 않기 위함이다.
CONTRACT_MAX = 3

# contracts 한 줄의 kind별 정본 형식. 규약 10장 표가 여기서 나오고 check가 경고로 낸다.
# 에러가 아닌 것은 기존 간선 대부분이 형식 밖이라, 에러로 두면 전수 재조사가 머지되기 전까지
# catalog.py --check가 실패해 update·add가 막히기 때문이다. 재조사 머지 뒤 에러로 올린다.
CONTRACT_FORMS = {
    "library": (re.compile(r"^(?:[\w.\-]+:[\w.\-]+|(?:@[\w.\-]+/)?[\w.\-]+) — .+$"),
                "`{group}:{artifact} — {왜}`, npm은 `{name} — {왜}`"),
    "http": (re.compile(r"^(?:GET|POST|PUT|PATCH|DELETE|ANY) /\S* — .+$"),
             "`{METHOD} {경로 접두}* — {왜}`"),
    "message": (re.compile(r"^\S+ / \S+ (?:발행|소비) — .+$"),
                "`{익스체인지} / {라우팅 키} 발행|소비 — {왜}`"),
    "data": (re.compile(r"^\S+\.\S+ 조회 — .+$"), "`{스키마}.{테이블 접두}* 조회 — {왜}`"),
}


# --- 로드 ---------------------------------------------------------------


def load_registry(wiki_root: Path) -> dict:
    """`{"domains": {...원본...}, "repos": {slug: {**노드, "domain": d}}}`.

    파일은 `domains.{d}.repos.{slug}` 중첩이고, 파생·판정 함수는 slug 하나로 노드를 찾는다.
    여기서 한 번 평탄화해 두 모양의 변환을 한 자리에 가둔다 — 노드에 `domain` 필드를 다시
    넣어 주므로 아래 함수들은 중첩을 몰라도 된다. 객체가 아닌 항목은 버린다.
    """
    data = catalog.load_json(Path(wiki_root) / REGISTRY_NAME, {})
    if not isinstance(data, dict):
        data = {}
    raw = data.get("domains")
    domains = (
        {name: info for name, info in raw.items() if isinstance(info, dict)}
        if isinstance(raw, dict) else {}
    )
    repos: dict[str, dict] = {}
    for name in sorted(domains):
        section = domains[name].get("repos")
        if not isinstance(section, dict):
            continue
        for slug, node in section.items():
            # slug 충돌은 check_repos가 에러로 낸다. 먼저 온 도메인을 남겨 파생이 흔들리지 않게 한다.
            if isinstance(node, dict) and slug not in repos:
                repos[slug] = {**node, "domain": name}
    return {"domains": domains, "repos": repos}


def load_edges(wiki_root: Path) -> list[dict]:
    """deps.json의 간선을 `from`을 되살린 평면 목록으로.

    파일은 from 기준 그룹 맵이고 파생 함수는 끝점 두 개를 한 행에서 본다. 끝점이
    `{도메인}/{레포}` 꼴이 아닌 행은 버린다 — 모양 검사는 check_errors가 한다.
    """
    data = catalog.load_json(Path(wiki_root) / DEPS_NAME, {})
    groups = data.get("deps") if isinstance(data, dict) else None
    if not isinstance(groups, dict):
        return []
    rows = []
    for origin, items in groups.items():
        if not isinstance(origin, str) or not ENDPOINT_RE.match(origin.strip()):
            continue
        if not isinstance(items, list):
            continue
        for edge in items:
            if not isinstance(edge, dict):
                continue
            target = edge.get("to")
            if not isinstance(target, str) or not ENDPOINT_RE.match(target.strip()):
                continue
            rows.append({**edge, "from": origin.strip(), "to": target.strip()})
    return rows


def is_dormant(info: dict) -> bool:
    return (info.get("status") or "active") == "dormant"


def endpoint_domain(endpoint: str) -> str:
    return endpoint.split("/", 1)[0]


def label_for(endpoint: str, current_domain: str) -> str:
    """현재 도메인 안이면 slug만, 밖이면 `{domain}/{slug}` — 도메인 이름이 파급 판단의 신호다."""
    domain, _, slug = endpoint.partition("/")
    return slug if domain == current_domain else endpoint


def text_list(value, limit: int = 0) -> list[str]:
    """문자열 배열을 공백 없는 값만 남겨 돌려준다. limit이 있으면 앞에서 자른다."""
    if not isinstance(value, list):
        return []
    rows = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return rows[:limit] if limit else rows


# --- 파생 ---------------------------------------------------------------


def domain_repos(registry: dict, domain: str) -> list[tuple[str, dict]]:
    """그 도메인 노드를 slug 정렬로. 휴면 노드도 포함한다 — 소비처가 남아 있을 수 있다."""
    return sorted(
        (slug, info) for slug, info in registry["repos"].items()
        if info.get("domain") == domain
    )


def project_owner(info: dict) -> str:
    """노드 `project` URL의 마지막 경로 요소 — 레포가 속한 owner(사용자·조직)."""
    return str(info.get("project") or "").strip().rstrip("/").rsplit("/", 1)[-1]


def owner_label(url: str) -> str:
    """접근 좌표·도메인 머리글의 owner 표기. github.com이면 `GitHub`, 아니면 호스트명을 앞에 붙인다."""
    host = normalize_host(url).split("/", 1)[0]
    owner = url.rstrip("/").rsplit("/", 1)[-1]
    return f"GitHub {owner}" if host == "github.com" else f"{host} {owner}"


def domain_projects(registry: dict, domain: str) -> list[tuple[str, str]]:
    """[(owner, owner URL)] — 소속 레포 `project`의 distinct.

    손으로 유지하던 도메인 접근 좌표를 노드에서 파생한다. 마지막 경로 요소가 owner라
    자연어에서 추출할 필요가 없다.
    """
    seen: dict[str, str] = {}
    for _, info in domain_repos(registry, domain):
        url = str(info.get("project") or "").strip().rstrip("/")
        if url and url not in seen:
            seen[url] = url.rsplit("/", 1)[-1]
    return sorted(((key, url) for url, key in seen.items()), key=lambda row: (row[0], row[1]))


def responsibility_rows(registry: dict, domain: str) -> list[str]:
    """`- {slug} — 문장 · 문장` 행. 요구 낱말에서 레포로 가는 경로다.

    영역 키에서 파생하던 역인덱스를 대신한다 — 문장에는 그룹핑 키가 없으므로 표를 만들지
    않고 레포마다 한 줄로 싣고, 걸린 문장의 행위 낱말이 수정할 층을 가른다.
    """
    rows = []
    for slug, info in domain_repos(registry, domain):
        lines = text_list(info.get("responsibilities"))
        if not lines:
            continue
        head = f"{slug} (휴면)" if is_dormant(info) else slug
        rows.append(f"- {head} — " + " · ".join(lines))
    return rows


def project_host(info: dict) -> str:
    """노드 `project` URL의 호스트. clone 패턴의 호스트가 여기서 나온다."""
    return normalize_host(str(info.get("project") or "")).split("/", 1)[0]


def mirror_path(wiki: str | Path, slug: str) -> Path:
    """위키 전용 bare 미러 경로. update.py·훅·render가 같은 규칙을 쓴다."""
    return Path(wiki) / ".local" / "mirrors" / f"{slug}.git"


def remote_pattern(registry: dict) -> tuple[str, str, dict[str, str]]:
    """(clone 패턴의 호스트, 단일 owner 또는 빈 문자열, {패턴을 벗어난 slug: remote}).

    remote는 전수가 `{host}/{owner}/{slug}` 꼴이다. 호스트는 노드 `project`에서 가장 흔한 것을
    쓰고, 그 규칙으로 만든 값과 remote가 다른 노드만 remote를 그대로 낸다. owner가 전 노드에서
    하나뿐이면 패턴에 그 값을 그대로 싣는다.
    """
    hosts: dict[str, int] = {}
    for info in registry["repos"].values():
        host = project_host(info)
        if host:
            hosts[host] = hosts.get(host, 0) + 1
    if not hosts:
        return "", "", {}
    host = max(sorted(hosts), key=hosts.__getitem__)
    odd: dict[str, str] = {}
    for slug, info in sorted(registry["repos"].items()):
        remote = str(info.get("remote") or "").strip()
        if remote and normalize_remote(remote) != f"{host}/{project_owner(info).lower()}/{slug}":
            odd[slug] = remote
    owners = {project_owner(info) for info in registry["repos"].values() if info.get("project")}
    return host, (owners.pop() if len(owners) == 1 else ""), odd


def edge_groups(edges: list[dict], domain: str, slug: str) -> tuple[list[dict], list[dict], list[dict]]:
    """(이 레포가 의존, 이 레포에 의존, 도메인의 다른 의존).

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


# --- 렌더 ---------------------------------------------------------------


def edge_row(edge: dict, hide: str = "", domain: str = "") -> str:
    """`- {kind} {from} → {to} — {계약}`. 끝점은 domain 안이면 slug만, 밖이면 `{domain}/{slug}`.

    hide는 비울 끝점이다 — 두 묶음에서 현재 레포 쪽을 지우는데, 그때는 화살표도 함께 지운다.
    방향은 묶음 머리글이 이미 말하고, 남은 화살표는 계약 구분자 ` — `와 붙어 읽히기 때문이다.
    """
    kind = str(edge.get("kind") or "?").strip()
    if hide:
        row = f"- {kind} {label_for(edge['from' if hide == 'to' else 'to'], domain)}"
    else:
        row = f"- {kind} {label_for(edge['from'], domain)} → {label_for(edge['to'], domain)}"
    contracts = text_list(edge.get("contracts"))
    if contracts:
        row += " — " + " · ".join(contracts)
    return row


def via_rows(edges: list[dict], domain: str, slug: str, incoming: list[dict]) -> list[str]:
    """`- {kind} {from} (경유 {lib})` — 내게 들어오는 간선의 `from`을 library로 쓰는 레포, 1홉.

    간선은 선언 위치로 저장하므로 공용 라이브러리를 거쳐 나를 부르는 레포에는 나와의 저장
    간선이 없다. 파급 확인에서 그 레포가 빠지지 않게 파생만 하고, 계약은 경유 레포의 직접
    간선이 진다.
    """
    me = f"{domain}/{slug}" if domain and slug else ""
    if not me or not incoming:
        return []
    direct = {edge["from"] for edge in incoming}
    users: dict[str, list[str]] = {}
    for edge in edges:
        if str(edge.get("kind") or "").strip() == "library":
            users.setdefault(edge["to"], []).append(edge["from"])
    found: dict[tuple[str, str], str] = {}
    for edge in incoming:
        via = edge["from"]
        kind = str(edge.get("kind") or "?").strip()
        for origin in users.get(via, []):
            if origin == me or origin in direct:
                continue
            found.setdefault((origin, via), kind)
    return [f"- {kind} {label_for(origin, domain)} (경유 {label_for(via, domain)})"
            for (origin, via), kind in sorted(found.items())]


def edge_blocks(outgoing: list[dict], incoming: list[dict], domain: str,
                edges: list[dict], slug: str) -> list[str]:
    """현재 레포 기준 두 묶음의 행. 머리글은 짧게 두고 무엇을 할지는 규약이 말한다.

    render_session·render_repo가 함께 쓰므로 경유 파생도 여기 한 곳에 둔다.
    """
    lines: list[str] = []
    if outgoing:
        lines.append(f"# 이 레포가 의존 {len(outgoing)}건 — 선행 조건")
        lines.extend(edge_row(edge, hide="from", domain=domain) for edge in outgoing)
    via = via_rows(edges, domain, slug, incoming)
    if incoming:
        head = f"# 이 레포에 의존 {len(incoming)}건 — 파급 대상"
        lines.append(head + (f" (경유 {len(via)}건 포함)" if via else ""))
        lines.extend(edge_row(edge, hide="to", domain=domain) for edge in incoming)
        lines.extend(via)
    return lines


def other_edge_rows(others: list[dict], domain: str) -> list[str]:
    """현재 레포가 끝점이 아닌 도메인 간선을 `- {from} → {to} {kind} · …`로 from 기준 묶음.

    계약은 싣지 않는다 — 여러 레포에 걸친 작업의 수정 순서를 가르는 데는
    방향과 종류면 충분하고, 계약은 `map`이 전수를 낸다.
    """
    groups: dict[str, list[str]] = {}
    for edge in others:
        kind = str(edge.get("kind") or "?").strip()
        groups.setdefault(label_for(edge["from"], domain), []).append(
            f"{label_for(edge['to'], domain)} {kind}"
        )
    return [f"- {origin} → " + " · ".join(items) for origin, items in groups.items()]


def access_block(registry: dict, domain: str) -> list[str]:
    """접근 좌표 행. 소속 레포 `project`에서 파생하므로 손으로 유지하는 자리가 없다."""
    return [f"- {owner_label(url)} — {url}" for _, url in domain_projects(registry, domain)]


def domain_heading(registry: dict, name: str, current: bool) -> str:
    """레포 지도의 도메인 머리글 — 설명과 owner를 한 줄에."""
    info = registry["domains"].get(name) or {}
    description = str(info.get("description") or "").strip()
    owners = "·".join(owner_label(url) for _, url in domain_projects(registry, name))
    row = f"## {name}"
    if description:
        row += f" — {description}"
    if owners:
        row += f" · {owners}"
    if current:
        row += " (현재)"
    return row


def map_block(registry: dict, domain: str, slug: str, wiki: str | Path) -> str:
    """레포 지도 — 도메인별 레포 전수와 좌표 패턴. 도메인이 없으면 도메인 목록만.

    현재 도메인을 먼저 두고 그 행에는 책임 문장을, 다른 도메인 행에는 소관 한 줄을 싣는다.
    휴면 노드는 값이 없어도 이름을 남긴다 — 소비처로 남아 있을 수 있어 파급 확인에 든다.
    미러 경로·remote는 헤더의 패턴 한 줄로 갈음하고 remote가 패턴을 벗어난 레포만 행 끝에 적는다.
    """
    domains = sorted(registry["domains"])
    if not domains:
        return ""
    head = f"# 레포 지도 · 도메인 {len(domains)}개"
    if not domain:
        rows = []
        for name in domains:
            description = str((registry["domains"][name] or {}).get("description") or "").strip()
            rows.append(f"- {name} — {description}" if description else f"- {name}")
        return "\n".join([head, *rows])

    head += f" · 현재 {domain}/{slug}"
    host, owner, remote_odd = remote_pattern(registry)
    patterns = [f"미러 {mirror_path(wiki, '{slug}')}"]
    if host:
        patterns.append(f"clone https://{host}/{owner or '{owner}'}/{{slug}}.git")
    header = [head, "# " + " · ".join(patterns)]

    blocks = ["\n".join(header)]
    for name in [domain, *(other for other in domains if other != domain)]:
        rows = [domain_heading(registry, name, name == domain)]
        for repo_slug, info in domain_repos(registry, name):
            row = f"- {repo_slug}"
            if is_dormant(info):
                row += " (휴면)"
            text = " · ".join(text_list(info.get("responsibilities"))) if name == domain else ""
            text = text or str(info.get("summary") or "").strip()
            if text:
                row += f" — {text}"
            if repo_slug in remote_odd:
                row += f" · remote {remote_odd[repo_slug]}"
            rows.append(row)
        blocks.append("\n".join(rows))
    return "\n\n".join(blocks)


def render_session(registry: dict, edges: list[dict], domain: str, slug: str,
                   wiki: str | Path) -> str:
    """훅이 헤더와 문서 목록 사이에 끼우는 블록. 도메인이 없으면 도메인 목록까지만."""
    blocks: list[str] = []
    block = map_block(registry, domain, slug, wiki)
    if block:
        blocks.append(block)
    if not domain:
        return "\n\n".join(blocks)

    outgoing, incoming, others = edge_groups(edges, domain, slug)
    lines = edge_blocks(outgoing, incoming, domain, edges, slug)
    if others:
        lines.append(f"# 도메인의 다른 의존 {len(others)}건 — from → to kind, 계약은 `graph.py map`")
        lines.extend(other_edge_rows(others, domain))
    if lines:
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_repo(registry: dict, edges: list[dict], slug: str, wiki: str | Path,
                knowledge: Path) -> str:
    """`repo` 출력 — 노드 전 필드, 그 레포 기준 두 묶음 간선, 레포 문서 목록."""
    info = registry["repos"].get(slug)
    if not isinstance(info, dict):
        known = ", ".join(sorted(registry["domains"])) or "없음"
        return (f"# 레포 {slug}가 registry.json에 없음 — 등록된 도메인: {known}, "
                "레포 전수는 `graph.py map --domain`")

    domain = str(info.get("domain") or "")
    state = (f"휴면 — {str(info.get('reason') or '').strip() or '사유 미기재'}"
             if is_dormant(info) else "active")
    rows = [f"# {domain}/{slug} · {state}"]

    def field(label: str, value: str) -> None:
        if value:
            rows.append(f"- {label}: {value}")

    hosts = info.get("hosts") if isinstance(info.get("hosts"), dict) else {}
    envs = [*(env for env in HOST_ENVS if env in hosts), *sorted(set(hosts) - set(HOST_ENVS))]
    remote = str(info.get("remote") or "").strip()
    branch = str(info.get("defaultBranch") or "").strip()
    mirror = mirror_path(wiki, slug)

    field("소관", str(info.get("summary") or "").strip())
    field("스택", " · ".join(text_list(info.get("stack"))))
    field("책임", " · ".join(text_list(info.get("responsibilities"))))
    field("호스트", " · ".join(f"{env} {str(hosts[env]).strip()}" for env in envs if str(hosts[env]).strip()))
    field("저장소", " · ".join(part for part in (remote, f"브랜치 {branch}" if branch else "") if part))
    field("미러", str(mirror) if mirror.is_dir() else f"없음 — update.py mirror --repo {slug}")
    blocks = ["\n".join(rows)]

    outgoing, incoming, _ = edge_groups(edges, domain, slug)
    lines = edge_blocks(outgoing, incoming, domain, edges, slug)
    if lines:
        blocks.append("\n".join(lines))

    # 폴더가 없으면 catalog.build가 0건 목록을 낸다 — 문서 없음도 답이다.
    blocks.append(catalog.build(Path(knowledge) / domain / slug, f"레포 {slug}"))
    return "\n\n".join(blocks)


def render_map(registry: dict, edges: list[dict], domain: str) -> str:
    """`map` 출력. 세션에 주입되지 않는 도메인을 에이전트가 한 번에 볼 때 쓴다."""
    if domain not in registry["domains"]:
        known = ", ".join(sorted(registry["domains"])) or "없음"
        return f"# 도메인 {domain}가 registry.json에 없음 — 등록된 도메인: {known}"

    description = str((registry["domains"][domain] or {}).get("description") or "").strip()
    blocks = [f"# {domain} 지도" + (f" — {description}" if description else "")]

    rows = access_block(registry, domain)
    if rows:
        blocks.append("\n".join([
            "## 접근 좌표", "", "clone은 각 레포 remote로 `https://{remote}.git`", "", *rows,
        ]))

    nodes = domain_repos(registry, domain)
    if nodes:
        rows = []
        for slug, info in nodes:
            state = f"휴면 — {str(info.get('reason') or '').strip() or '사유 미기재'}" if is_dormant(info) else "active"
            stack = " · ".join(text_list(info.get("stack"))) or "—"
            summary = str(info.get("summary") or "").strip() or "—"
            rows.append(f"| {slug} | {state} | {stack} | {summary} |")
        blocks.append("\n".join(
            ["## 레포 구성", "", "| 레포 | 상태 | 스택 | 소관 |", "|---|---|---|---|", *rows]
        ))

    rows = responsibility_rows(registry, domain)
    if rows:
        blocks.append("\n".join([f"## 레포 책임 {len(rows)}개 레포", "", *rows]))

    touching = sorted(
        (edge for edge in edges
         if domain in (endpoint_domain(edge["from"]), endpoint_domain(edge["to"]))),
        key=lambda edge: (edge["from"], edge["to"], str(edge.get("kind") or "")),
    )
    if touching:
        blocks.append("\n".join([
            f"## 의존 간선 {len(touching)}건 (kind from → to — 계약 식별자, from이 to에 의존)",
            "",
            *(edge_row(edge, domain=domain) for edge in touching),
        ]))

    return "\n\n".join(blocks)


# --- 검사 ---------------------------------------------------------------


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
        if "repos" not in info:
            errors.append((REGISTRY_NAME, f"{label}: repos 없음 — 레포가 없으면 빈 객체"))
        elif not isinstance(info["repos"], dict):
            errors.append((REGISTRY_NAME, f"{label}: repos는 `{{slug: 노드}}` 객체"))


def check_repo(domain: str, slug: str, info: dict, domains: set[str],
               errors: list[tuple[str, str]]) -> None:
    """노드 하나. 도메인이 다르면 같은 이름의 검사가 두 번 나가므로 라벨에 도메인을 붙인다."""
    label = f"레포 {domain}/{slug}"
    if not SLUG_RE.match(slug):
        errors.append((REGISTRY_NAME, f"{label}: slug는 소문자·숫자·하이픈만"))

    status = info.get("status")
    dormant = status == "dormant"
    missing = [key for key in REPO_KEYS if key not in info]
    if missing:
        errors.append((REGISTRY_NAME, f"{label}: 필수 키 없음: {', '.join(missing)}"))
    allowed = set(REPO_KEYS) | ({"reason"} if dormant else set())
    unknown = sorted(set(info) - allowed)
    if unknown:
        errors.append((REGISTRY_NAME, f"{label}: 허용되지 않는 키: {', '.join(unknown)}"))
    if status not in REPO_STATUS:
        errors.append((REGISTRY_NAME, f"{label}: status는 {'·'.join(REPO_STATUS)} 중 하나 (현재 {status!r})"))

    raw_project = info.get("project")
    project = raw_project.strip() if isinstance(raw_project, str) else ""
    if "project" in info and not project:
        errors.append((REGISTRY_NAME, f"{label}: project 없음 — owner URL(`https://{{host}}/{{owner}}`)"))
    elif project and not PROJECT_RE.match(project):
        errors.append((REGISTRY_NAME,
                       f"{label}: project {project!r}가 owner URL이 아님 — "
                       "`https://{host}/{owner}` 꼴"))

    raw_remote = info.get("remote")
    remote = raw_remote.strip() if isinstance(raw_remote, str) else ""
    if raw_remote is not None and not isinstance(raw_remote, str):
        errors.append((REGISTRY_NAME, f"{label}: remote는 정본 하나를 담은 문자열"))
    elif remote and "://" in remote:
        errors.append((REGISTRY_NAME, f"{label}: remote에 scheme이 있음 — `{normalize_remote(remote)}` 꼴로 적음"))
    elif remote and normalize_remote(remote) != remote:
        errors.append((REGISTRY_NAME, f"{label}: remote가 정규화 꼴이 아님 — `{normalize_remote(remote)}`"))
    elif "remote" in info and not remote:
        errors.append((REGISTRY_NAME, f"{label}: remote 없음 — /llm-wiki:register --resurvey"))

    branch = info.get("defaultBranch")
    if not isinstance(branch, str) or not branch.strip():
        errors.append((REGISTRY_NAME, f"{label}: defaultBranch 없음"))

    summary = info.get("summary") if isinstance(info.get("summary"), str) else ""
    if info.get("summary") is not None and not isinstance(info.get("summary"), str):
        errors.append((REGISTRY_NAME, f"{label}: summary는 한 줄 문자열"))
    elif len(summary) > SUMMARY_LIMIT:
        errors.append((REGISTRY_NAME, f"{label}: summary가 {len(summary)}자 — 상한 {SUMMARY_LIMIT}자"))
    elif status == "active" and not summary.strip():
        errors.append((REGISTRY_NAME, f"{label}: summary 없음 — /llm-wiki:register --resurvey"))

    # stack·summary·responsibilities는 휴면 노드에 비우라고도 채우라고도 하지 않는다 —
    # 휴면 레포가 여전히 소비 중일 수 있어 무엇이었는지가 필요하고, 조사할 사람이 없는
    # 레포에 값을 요구하면 등록 자체가 막힌다. 값을 요구하는 것은 active뿐이다.
    stack = info.get("stack")
    if "stack" in info and (
        not isinstance(stack, list)
        or any(not isinstance(item, str) or not item.strip() for item in stack)
    ):
        errors.append((REGISTRY_NAME, f"{label}: stack은 빈 값이 없는 문자열 배열"))
    else:
        rows = text_list(stack)
        if len(rows) > STACK_MAX:
            errors.append((REGISTRY_NAME,
                           f"{label}: stack이 {len(rows)}개 — 상한 {STACK_MAX}개, "
                           "주 언어·프레임워크만 버전을 남기고 나머지는 이름만"))
        if not rows and status == "active":
            errors.append((REGISTRY_NAME, f"{label}: stack 없음 — /llm-wiki:register --resurvey"))

    duties = info.get("responsibilities")
    if "responsibilities" in info and (
        not isinstance(duties, list)
        or any(not isinstance(item, str) or not item.strip() for item in duties)
    ):
        errors.append((REGISTRY_NAME,
                       f"{label}: responsibilities는 빈 값이 없는 문자열 배열 — "
                       "`{업무 대상} {이 레포가 하는 일}` 평문 문장"))
    else:
        rows = text_list(duties)
        for line in rows:
            if len(line) > RESP_LIMIT:
                errors.append((REGISTRY_NAME,
                               f"{label}: 책임 {line!r}가 {len(line)}자 — 상한 {RESP_LIMIT}자, "
                               "두 사실이면 두 줄로 나눔"))
            if "/" in line:
                errors.append((REGISTRY_NAME,
                               f"{label}: 책임 {line!r}에 `/` — 도메인 접두는 폐지됨, 문장만 적음"))
        if not rows and status == "active":
            errors.append((REGISTRY_NAME, f"{label}: responsibilities 없음 — /llm-wiki:register --resurvey"))

    hosts = info.get("hosts")
    if "hosts" in info and not isinstance(hosts, dict):
        errors.append((REGISTRY_NAME, f"{label}: hosts는 `{{환경: 호스트}}` 객체"))
    elif isinstance(hosts, dict):
        for env, value in sorted(hosts.items()):
            if env not in HOST_ENVS:
                errors.append((REGISTRY_NAME,
                               f"{label}: hosts 환경 {env!r}가 {'·'.join(HOST_ENVS)} 밖 — HOST_ENVS로 넓힘"))
            if not isinstance(value, str) or not value.strip():
                errors.append((REGISTRY_NAME, f"{label}: hosts.{env}는 주소 하나를 담은 문자열"))
            elif normalize_host(value) != value.strip():
                errors.append((REGISTRY_NAME,
                               f"{label}: 호스트 {value}가 정규화 꼴이 아님 — `{normalize_host(value)}`"))

    if dormant:
        reason = info.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append((REGISTRY_NAME, f"{label}: status dormant인데 reason 없음"))


def check_repos(domains_raw: dict, errors: list[tuple[str, str]]) -> None:
    """도메인 중첩을 훑으며 노드를 검사하고, slug가 위키 전체에서 유일한지 본다."""
    names = set(domains_raw)
    owner: dict[str, str] = {}
    for domain in sorted(domains_raw):
        section = domains_raw[domain].get("repos") if isinstance(domains_raw[domain], dict) else None
        if not isinstance(section, dict):
            continue
        for slug, info in sorted(section.items()):
            if not isinstance(info, dict):
                errors.append((REGISTRY_NAME, f"레포 {domain}/{slug}: 항목이 객체가 아님"))
                continue
            first = owner.setdefault(slug, domain)
            if first != domain:
                errors.append((REGISTRY_NAME,
                               f"레포 {domain}/{slug}: slug가 {first}에도 있음 — "
                               "노드 식별자는 위키 전체에서 유일, register가 `{domain}-{name}`을 제안"))
            check_repo(domain, slug, info, names, errors)


def check_deps(wiki_root: Path, registry: dict | None, errors: list[tuple[str, str]]) -> None:
    path = Path(wiki_root) / DEPS_NAME
    if not path.is_file():
        return
    data = catalog.load_json(path, None)
    if not isinstance(data, dict) or not isinstance(data.get("deps"), dict):
        errors.append((DEPS_NAME, 'JSON을 읽지 못했거나 deps가 객체가 아님 — {"deps": {"{from}": [...]}} 꼴이어야 함'))
        return

    domains = set(registry["domains"]) if registry else set()
    repos = registry["repos"] if registry else {}

    def known(endpoint: str) -> str:
        """등록되지 않은 끝점이면 사유를, 실재하면 빈 문자열을 돌려준다."""
        if not registry:
            return ""
        domain, _, repo = endpoint.partition("/")
        if domain not in domains:
            return f"도메인 {domain}가 registry.json에 없음"
        info = repos.get(repo)
        if not isinstance(info, dict) or info.get("domain") != domain:
            return f"레포 {endpoint}가 registry.json에 없음"
        return ""

    for origin in sorted(data["deps"]):
        items = data["deps"][origin]
        group = f"deps[{origin}]"
        if not ENDPOINT_RE.match(origin.strip()):
            errors.append((DEPS_NAME, f"{group}: 그룹 키 형식이 아님 — {{도메인}}/{{레포}}"))
        else:
            gap = known(origin.strip())
            if gap:
                errors.append((DEPS_NAME, f"{group}: 그룹 키 {gap}"))
        if not isinstance(items, list):
            errors.append((DEPS_NAME, f"{group}: 값이 배열이 아님"))
            continue

        seen: dict[tuple[str, str], int] = {}
        for position, edge in enumerate(items, start=1):
            label = f"{group} {position}"
            if not isinstance(edge, dict):
                errors.append((DEPS_NAME, f"{label}: 항목이 객체가 아님"))
                continue

            unknown = sorted(set(edge) - set(EDGE_KEYS))
            if unknown:
                errors.append((DEPS_NAME, f"{label}: 허용되지 않는 키: {', '.join(unknown)}"
                                          + (" — from은 그룹 키가 짐" if "from" in unknown else "")))

            target = edge.get("to").strip() if isinstance(edge.get("to"), str) else ""
            if not target:
                errors.append((DEPS_NAME, f"{label}: to 없음"))
            elif not ENDPOINT_RE.match(target):
                errors.append((DEPS_NAME, f"{label}: to 형식이 아님 ({target}) — {{도메인}}/{{레포}}"))
            else:
                gap = known(target)
                if gap:
                    errors.append((DEPS_NAME, f"{label}: to {gap}"))
                if target == origin.strip():
                    errors.append((DEPS_NAME, f"{label}: 자기 간선"))

            kind = edge.get("kind") if isinstance(edge.get("kind"), str) else ""
            if not kind:
                errors.append((DEPS_NAME, f"{label}: kind 없음"))
            elif kind not in EDGE_KINDS:
                errors.append((DEPS_NAME, f"{label}: kind는 {'·'.join(EDGE_KINDS)} 중 하나 (현재 {kind})"))

            contracts = edge.get("contracts")
            if not isinstance(contracts, list) or any(
                not isinstance(item, str) or not item.strip() for item in contracts
            ):
                errors.append((DEPS_NAME, f"{label}: contracts는 빈 값이 없는 문자열 배열"))
            else:
                rows = text_list(contracts)
                if not rows:
                    errors.append((DEPS_NAME, f"{label}: contracts 없음 — `{{식별자}} — {{왜 쓰는지}}` 1건 이상"))
                elif len(rows) > CONTRACT_MAX:
                    errors.append((DEPS_NAME,
                                   f"{label}: contracts가 {len(rows)}건 — 상한 {CONTRACT_MAX}건, "
                                   "넘으면 접두나 묶음 표현으로 접음"))

            # 같은 두 레포가 http와 message로 함께 이어질 수 있으므로 종류까지 묶어 본다.
            if target and kind:
                pair = (target, kind)
                if pair in seen:
                    errors.append((DEPS_NAME, f"{label}: 중복 — {seen[pair]}번과 같은 (to, kind)"))
                else:
                    seen[pair] = position


def check_warnings(wiki_root: Path) -> list[tuple[str, str]]:
    """(파일, 메시지) 경고 목록 — 고치지 않아도 커밋을 막지 않는 것만 담는다.

    check_errors와 나눠 두는 것은 catalog.py `--check`가 에러만 부르기 때문이다. contracts
    형식을 에러로 올리면 전수 재조사가 머지되기 전까지 update·add가 통째로 막힌다.
    """
    warnings: list[tuple[str, str]] = []
    for edge in load_edges(Path(wiki_root)):
        form = CONTRACT_FORMS.get(str(edge.get("kind") or "").strip())
        if not form:
            continue
        pattern, shape = form
        for line in text_list(edge.get("contracts")):
            if not pattern.match(line):
                warnings.append((DEPS_NAME,
                                 f"deps[{edge['from']}] {edge['to']}: contracts {line!r}가 "
                                 f"형식 밖 — {shape}"))
    return sorted(warnings)


def check_errors(wiki_root: Path) -> list[tuple[str, str]]:
    """(파일, 메시지) 목록. catalog --check가 문서 에러와 함께 내고 graph check가 단독으로도 낸다."""
    wiki_root = Path(wiki_root)
    errors: list[tuple[str, str]] = []

    path = wiki_root / REGISTRY_NAME
    if not path.is_file():
        return [(REGISTRY_NAME, f"{path} 없음 — /llm-wiki:init")]

    raw = catalog.load_json(path, None)
    if not isinstance(raw, dict):
        errors.append((REGISTRY_NAME, 'JSON을 읽지 못했거나 객체가 아님 — {"domains": {}} 꼴이어야 함'))
        raw = {}

    if "domains" in raw and not isinstance(raw["domains"], dict):
        errors.append((REGISTRY_NAME, "domains가 객체가 아님"))
    domains_raw = raw.get("domains") if isinstance(raw.get("domains"), dict) else {}
    unknown = sorted(set(raw) - {"domains"})
    if unknown:
        errors.append((REGISTRY_NAME, f"최상위에 허용되지 않는 키: {', '.join(unknown)}"))

    check_domains(domains_raw, errors)
    check_repos(domains_raw, errors)
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


def normalize_host(value: str) -> str:
    """호스트를 비교 가능한 꼴로 줄인다. scheme·자격증명·끝 슬래시·대소문자를 지운다.

    경로는 남긴다 — `apps.example.com/admin`처럼 한 호스트에 여러 레포가 붙는 곳에서
    경로가 레포를 가른다.
    """
    text = value.strip().lower()
    _, separator, rest = text.partition("://")
    text = rest if separator else text
    text = text.split("@", 1)[-1]
    return text.strip("/")


def slug_from_remote(url: str) -> str:
    """remote URL의 마지막 경로 요소에서 slug를 만든다."""
    tail = normalize_remote(url).rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^a-z0-9-]", "-", tail).strip("-")


def resolve_repo(registry: dict, remote: str, common_dir: str) -> tuple[str, str | None]:
    """(slug, domain)을 돌려준다. 등록되지 않았으면 domain이 None이다.

    등록 매칭은 정규화한 remote가 노드의 `remote`와 같은지로 하고, 못 찾으면 slug로 한 번
    더 본다. owner를 slug에 넣지 않기 때문에 포크와 원본이 같은 slug로 모이고, 워크트리도
    본 저장소와 같은 slug가 된다 — 노드에 정본 remote만 적어도 포크에서 연 세션이 걸린다.
    """
    repos = registry.get("repos", {}) if isinstance(registry, dict) else {}

    if remote:
        target = normalize_remote(remote)
        for slug, info in repos.items():
            candidate = info.get("remote")
            if isinstance(candidate, str) and candidate.strip() and normalize_remote(candidate) == target:
                return slug, info.get("domain")
        slug = slug_from_remote(remote)
    elif common_dir:
        slug = re.sub(r"[^a-z0-9-]", "-", Path(common_dir).parent.name.lower()).strip("-")
    else:
        return "", None

    info = repos.get(slug)
    return slug, info.get("domain") if info else None


# --- 스키마 -------------------------------------------------------------

SCHEMA_KINDS = ("survey", "facts")
# register의 조사 레인. 한 에이전트가 전량 스키마를 받으면 자기 몫 밖까지 채워 레인 간
# 대조가 무의미해지므로, 레인마다 맡는 키와 간선 종류만 남긴다.
SURVEY_LANES = ("library", "http", "message", "responsibilities")
LANE_KINDS = {"library": ("library",), "http": ("http",), "message": ("message", "data")}
KIND_HINTS = {
    "library": "빌드 의존은 `library`",
    "http": "HTTP 클라이언트·Feign은 `http`",
    "message": "큐·토픽 발행과 소비는 `message`",
    "data": "타 레포 스키마 직접 조회는 `data`",
}


def schema_block(kind: str, registry: dict | None = None, domain: str = "",
                 lane: str = "") -> str:
    """서브에이전트 프롬프트에 그대로 붙일 출력 스키마.

    수치와 열거를 이 모듈의 상수에서 전개한다 — 스킬 프롬프트가 같은 값을 따로 적어 두면
    상수를 고칠 때 한쪽만 남고, 그 프롬프트를 받은 에이전트는 옛 상한에 맞춘 값을 만들어
    check에서 막힌다. 정본은 상수 하나다.

    survey(register의 레포 조사)와 facts(update의 머지 추출)는 근거 키만 다르다 — 전자는
    코드 위치를, 후자는 근거 머지를 댄다. survey에 `lane`을 주면 그 레인이 맡는 키와 간선
    종류만 남는다.
    """
    survey = kind == "survey"
    lane = lane if survey and lane in SURVEY_LANES else ""
    ground = ('"evidence": "경로 또는 파일#심볼"' if survey
              else '"shas": ["근거 머지 sha7 — 1개 이상"]')
    envs = "|".join(HOST_ENVS) + ("|미상" if survey else "")
    node = lane in ("", "responsibilities")
    deps = lane != "responsibilities"
    kinds = LANE_KINDS.get(lane, EDGE_KINDS)

    fields: list[str] = []
    if survey and lane in ("", "library"):
        fields.append(f' "stack": ["주 언어·프레임워크는 버전까지, 나머지는 이름만 — {STACK_MAX}개 이내"]')
    if survey and node:
        fields.append(f' "summary": "{SUMMARY_LIMIT}자 이내 소관 한 줄, 업무 낱말 우선"')
    if node:
        fields.append(f' "responsibilities": [{{"text": "{{업무 대상}} {{이 레포가 하는 일}} — {RESP_LIMIT}자 이내",\n'
                      f"                       {ground}}}]")
        fields.append(f' "hosts": [{{"env": "{envs}", "value": "이 레포가 서빙하는 호스트", {ground}}}]')
        if survey:
            fields.append(' "hosts_missing": true 또는 false')
    if deps:
        fields.append(' "deps": [{"target": "등록 레포는 slug · registry 밖 시스템은 ~{host} · 모르면 빈 문자열",\n'
                      f'           "kind": "{"|".join(kinds)}", "from_me": true 또는 false,\n'
                      f'           "contracts": ["{{식별자}} — {{왜 쓰는지}}, {CONTRACT_MAX}건 이내"], {ground}}}]')

    rows = [f"## 출력 스키마 — {lane} 레인" if lane else "## 출력 스키마 — 그래프 3키",
            "",
            "아래 키를 그 이름 그대로 출력 객체에 담으세요. 빈 항목은 `[]`로 두세요.",
            "",
            "```json", "{", ",\n".join(fields), "}", "```", "",
            "### 값 규칙", ""]

    if node:
        rows.append(
            "- **책임 문장**: 주어는 언제나 이 레포입니다. `{업무 대상} {이 레포가 하는 일}` 꼴로 "
            "이 레포가 맡은 일을 빠짐없이, 행위 낱말이 층을 말하게 적으세요 — `제공`(API·라이브러리)·`화면`·"
            "`발행`/`소비`·`배치`·`중계`·`검증`·`관리`(정본 보유). 등록된 다른 레포의 이름은 간선 몫이니 넣지 말고, "
            "우리가 고치지 못하는 외부 시스템(외부 결제·타 조직 시스템)은 간선이 없으므로 그 이름을 문장에 "
            "남기세요. `화면`·`연동 처리` 같은 범주어만으로도 적지 마세요.")
        rows.append(
            "- **리터럴만**: `hosts`의 값은 설정·코드에서 읽은 리터럴이어야 합니다. 프로퍼티 **키 이름**과 "
            "`${...}` 플레이스홀더는 값이 아닙니다 — 플레이스홀더를 만나면 같은 파일군(`application-{env}.yml`·"
            "`.env.example`)에서 실제 값을 찾고, 찾지 못하면 그 항목을 넣지 마세요.")
        if survey:
            rows.append("- **hosts_missing**: 컨트롤러·라우트가 있는데 서빙 호스트 리터럴을 찾지 못했으면 참으로 두세요.")
    if deps:
        rows.append(
            "- **선언 위치**: 이 레포 안에 선언(호출·발행·import)이 실제로 있는 것만 적으세요. 공용 "
            "라이브러리가 선언한 호출을 그 심볼로 부르는 것은 **그 라이브러리로의 `library` 의존일 뿐**이라 "
            "여기에 적지 않습니다.")
        if len(kinds) > 1:
            rows.append("- **간선 종류**: " + ", ".join(KIND_HINTS[item] for item in kinds) + "입니다.")
        note = "- **from_me**: `from`이 `to`의 계약에 의존한다는 뜻이고, 참이면 이 레포가 `from`입니다."
        plain = [item for item in kinds if item != "message"]
        if plain:
            note += f" `{'`·`'.join(plain)}`는 이 레포가 남의 계약을 쓰는 것이라 항상 참입니다."
        if "message" in kinds:
            note += (" `message`는 **이 레포가 발행하면 참, 소비(리스너 보유)하면 거짓**입니다 — 리스너를 가진 "
                     "쪽이 `to`입니다.")
        rows.append(note)
        rows.append(
            "- **target 값**: 패키지 좌표의 artifactId, Feign `name`, 호스트 앞머리처럼 식별자에 상대 레포 "
            "이름이 들어 있으면 그 slug를, 우리 레포가 아닌 외부 시스템이면 `~{host}`를, 큐·익스체인지 "
            "이름처럼 소유 레포를 알 수 없으면 **빈 문자열을 두고 `contracts`에 식별자만 남기세요**. 추측으로 "
            "채우지 마세요 — 상대는 메인이 후보 레포 코드를 열어 정합니다.")
        rows.append(
            f"- **contracts**: 한 줄이 `{{식별자}} — {{왜 쓰는지}}`이고 의존당 {CONTRACT_MAX}건 이내입니다. "
            "라우트를 전수 나열하지 말고 넘으면 접두(`/v1/notices*`)나 묶음으로 접으세요. Feign `name`·호스트·"
            "프로퍼티 키는 식별자가 아니며 kind마다 아래 형식을 지키세요.")
        rows += ["", "| kind | 형식 |", "|---|---|"]
        rows += [f"| {item} | {CONTRACT_FORMS[item][1].replace('|', chr(92) + '|')} |" for item in kinds]
        rows.append("")
    rows.append("- **근거 없음**: 근거를 찾지 못한 항목은 넣지 마세요. 사전 지식으로 공백을 채우지 마세요.")

    if registry is not None and domain and node:
        samples: list[str] = []
        for slug, info in domain_repos(registry, domain):
            for line in text_list(info.get("responsibilities")):
                samples.append(f"- {line} ({slug})")
        if samples:
            rows += ["",
                     f"### {domain}의 기존 책임 문장",
                     "",
                     "같은 층을 두 낱말로 부르지 않도록 행위 낱말을 맞추고, 같은 문장을 그대로 다시 적지 마세요.",
                     "",
                     *samples]

    return "\n".join(rows)


# --- CLI ----------------------------------------------------------------


def cmd_schema(args) -> int:
    registry = None
    if args.domain:
        registry = load_registry(Path(args.wiki).expanduser())
    print(schema_block(getattr(args, "for"), registry, args.domain or "",
                       getattr(args, "lane", "") or ""))
    return 0


def cmd_map(args) -> int:
    wiki = Path(args.wiki).expanduser()
    print(render_map(load_registry(wiki), load_edges(wiki), args.domain))
    return 0


def cmd_render(args) -> int:
    """훅이 import로 부르는 render_session을 그대로 낸다 — 주입 형상 회귀를 명령 하나로 본다."""
    wiki = Path(args.wiki).expanduser()
    print(render_session(load_registry(wiki), load_edges(wiki), args.domain, args.slug, wiki))
    return 0


def cmd_repo(args) -> int:
    wiki = Path(args.wiki).expanduser()
    print(render_repo(load_registry(wiki), load_edges(wiki), args.slug, wiki, wiki / "knowledge"))
    return 0


def cmd_check(args) -> int:
    wiki = Path(args.wiki).expanduser()
    errors = check_errors(wiki)
    for name, message in errors:
        print(f"에러  {name}: {message}")
    warnings = check_warnings(wiki)
    for name, message in warnings:
        print(f"경고  {name}: {message}")
    registry = load_registry(wiki)
    print(f"# 노드 {len(registry['repos'])}개 · 간선 {len(load_edges(wiki))}건 · 에러 {len(errors)}건"
          f" · 경고 {len(warnings)}건")
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

    repo_cmd = sub.add_parser("repo", parents=[common],
                              help="레포 하나의 노드 전 필드·간선·문서 목록을 낸다")
    repo_cmd.add_argument("slug", metavar="SLUG", help="대상 레포")
    repo_cmd.set_defaults(func=cmd_repo)

    schema_cmd = sub.add_parser("schema", parents=[common],
                                help="서브에이전트 프롬프트에 붙일 그래프 3키 스키마를 낸다")
    schema_cmd.add_argument("--for", metavar="KIND", required=True, choices=SCHEMA_KINDS,
                            help=f"{'·'.join(SCHEMA_KINDS)} 중 하나")
    schema_cmd.add_argument("--domain", metavar="NAME", default="",
                            help="주면 그 도메인의 기존 책임 문장을 함께 낸다")
    schema_cmd.add_argument("--lane", metavar="NAME", default="", choices=("", *SURVEY_LANES),
                            help=f"survey 조사 레인 — {'·'.join(SURVEY_LANES)} (facts는 무시)")
    schema_cmd.set_defaults(func=cmd_schema)

    render_cmd = sub.add_parser("render", parents=[common],
                                help="훅이 주입하는 그래프 블록을 그대로 낸다")
    render_cmd.add_argument("--domain", metavar="NAME", default="", help="현재 도메인 (없으면 도메인 목록만)")
    render_cmd.add_argument("--slug", metavar="SLUG", default="", help="현재 레포")
    render_cmd.set_defaults(func=cmd_render)

    check_cmd = sub.add_parser("check", parents=[common], help="노드·간선을 검사한다. 에러가 있으면 종료 코드 1")
    check_cmd.set_defaults(func=cmd_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
