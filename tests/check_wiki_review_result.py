"""Check a reviewed market fixture clone. Inputs and assertions are separate from the writer."""
import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def relative_links(doc):
    for raw in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', doc.read_text()):
        url = urlsplit(raw.strip('<>'))
        if not url.scheme and not url.netloc:
            yield (doc.parent / unquote(url.path)).resolve() if url.path else doc, unquote(url.fragment)


def check_result(wiki):
    root = (Path(wiki) / 'knowledge' / 'market').resolve()
    docs = {p: p.read_text() for p in root.rglob('*.md')}
    assert docs, f'No market wiki documents in {root}'
    common = {p: body for p, body in docs.items() if p.parent == root}
    combined = '\n'.join(docs.values())

    def matching(contents, *terms):
        return [p for p, body in contents.items() if all(re.search(term, body) for term in terms)]

    # Existing feature and merge-only addition must have independently sourced common contracts.
    assert matching(common, '영수증', '14일', '200', '410', '제4판|v4'), 'Missing approved partner receipt contract'
    assert 'admin_receipt_list' not in combined and '이름순' not in combined, 'Undocumented convenience promoted'
    assert matching(common, 'lockerId', '인수 알림', '규격'), 'Missing contract from unprocessed merge'

    refunds = matching(common, '환불', '8일', 'MARKET-17')
    assert len(refunds) == 1, 'Missing Jira decision or duplicated policy'
    assert '20일' not in combined, 'Unapproved Jira proposal was published'
    assert not re.search(r'3일\s*(안|이내|까지)', docs[refunds[0]]), 'Earlier refund term still presented as current'

    owners = matching(common, '온라인', '배송 증빙', '72시간', 'v3|제3판')
    assert len(owners) == 1, 'Expected a single 72-hour online owner'
    online_doc = root / 'batch-api' / 'delivery-retry.md'
    assert '24시간' not in docs.get(online_doc, ''), 'Online replica kept stale term'
    assert owners[0] in {target for target, _ in relative_links(online_doc)}, 'Missing online owner link'
    assert matching({root/'field-console/delivery-retry.md': docs[root/'field-console/delivery-retry.md']}, '망분리', '24시간', '부속 규격|offline.md'), 'Removed separately scoped exception'

    owners = matching(common, 'UTF-8', '정산 파일 송신 규격|specs/export.md')
    assert len(owners) == 1, 'Missing canonical encoding policy'
    assert sum('UTF-8' in body for body in docs.values()) == 1, 'Duplicated common policy'
    assert 'normalize' not in combined and 'demo-3.jar' not in combined, 'Implementation or one-off result remains'
    transfers = matching(docs, '02:00', '03:00', '수요일', '(2인|2명|두 명)', '야간 송신 당직 인수서|ops/nightly.md')
    assert len(transfers) == 1 and transfers[0].parent.name == 'batch-api', 'Lost one of the two unique constraints'
    assert owners[0] in {target for target, _ in relative_links(transfers[0])}, 'Lost common policy link'
    assert not all((root / 'batch-api' / name).exists() for name in ('export-batch.md', 'export-replay.md')), 'Docs not merged'

    handover = root / 'batch-api' / 'shift-handover.md'
    destinations = {anchor for target, anchor in relative_links(handover) if target == transfers[0]}
    assert len(destinations) == 2 and all(destinations), 'Lost distinct send and replay anchors'
    for doc in docs:
        for target, anchor in relative_links(doc):
            assert target.is_file(), f'Broken link {doc.name} -> {target.name}'
            if anchor:
                slug = lambda s: re.sub(r'[^\w가-힣 -]', '', s.lower()).strip().replace(' ', '-')
                headings = re.findall(r'^#{1,6}\s+(.+)$', target.read_text(), re.M)
                assert anchor in {slug(h) for h in headings}, f'Broken anchor {doc.name} -> {target.name}#{anchor}'
    return len(docs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wiki', type=Path)
    count = check_result(parser.parse_args().wiki)
    print(f'{count} documents checked: contracts, exception, merged constraints and backlinks')
