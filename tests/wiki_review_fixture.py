"""Build the offline market wiki, service histories and a mock paged decision-source response."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from textwrap import dedent

DOMAIN = 'market'
GIT_ENV = {
    **os.environ,
    'GIT_CONFIG_NOSYSTEM': '1',
    'GIT_CONFIG_GLOBAL': os.devnull,
    'GIT_AUTHOR_NAME': 'Fixture editor',
    'GIT_AUTHOR_EMAIL': 'editor@example.invalid',
    'GIT_COMMITTER_NAME': 'Fixture editor',
    'GIT_COMMITTER_EMAIL': 'editor@example.invalid',
    'GIT_AUTHOR_DATE': '2026-06-01T09:00:00+00:00',
    'GIT_COMMITTER_DATE': '2026-06-01T09:00:00+00:00',
}


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], env=GIT_ENV, text=True,
                          capture_output=True, check=True, timeout=15).stdout.strip()


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).strip() + '\n', encoding='utf-8')


def json_file(path, value):
    put(path, json.dumps(value, indent=2, ensure_ascii=False))


def init(path):
    path.mkdir(parents=True)
    git(path, 'init', '-q', '-b', 'main')


def commit(path, message):
    git(path, 'add', '.')
    git(path, 'commit', '-qm', message)
    return git(path, 'rev-parse', 'HEAD')


def doc(path, title, description, content):
    put(path, f'---\ndescription: {description}\n---\n\n# {title}\n\n' + dedent(content).strip())


def create_fixture(root):
    """root must be new or empty. Return the original committed wiki and its local remotes."""
    root = Path(root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f'fixture directory must be empty: {root}')
    remotes = root / 'services'
    archive, batch, field = (remotes / slug for slug in ('archive-api', 'batch-api', 'field-console'))
    for repo in (archive, batch, field):
        init(repo)

    put(archive / 'src/archive.py', """
        # GET /archives/{id}/receipt. Contract: specs/receipt-v4.md.
        def receipt_status(days_after_completion):
            return 200 if 0 <= days_after_completion <= 14 else 410

        def admin_receipt_list(receipts):
            return sorted(receipts, key=lambda receipt: receipt['label'])
    """)
    put(archive / 'specs/receipt-v4.md', """
        # 영수증 열람 규격 제4판 §2
        계약 책임자 하은, 승인일 2026-03-10. 외부 파트너가 archive-api에서 완료된 보관 작업의 영수증을
        조회하면 완료 후 14일까지 HTTP 200을, 그 뒤에는 HTTP 410을 반환한다. 대상은 파트너 열람 API다.
    """)
    put(archive / 'tests/test_receipt.py', """
        from src.archive import receipt_status

        def test_last_day():
            assert receipt_status(14) == 200
            assert receipt_status(15) == 410
    """)
    archive_tip = commit(archive, '보관 영수증 발급·조회')

    put(batch / 'src/workflows.py', """
        def refund_accepted(days):
            return days <= 3

        def window_hours(channel):
            return 24 if channel == 'offline' else 72

        def export_batch(rows):
            return flush(normalize(rows))

        def normalize(rows):
            return tuple(rows)

        def flush(rows):
            return len(rows)
    """)
    put(batch / 'specs/delivery.md', """
        # 배송 증빙 재전송 규격 v3 §1
        2026-04-08 배송 운영 책임자 문서윤 승인. v2의 온라인 가맹점 재전송 기한 24시간을
        72시간으로 대체한다. 기산점은 증빙 생성 시각이다. 망분리 오프라인 단말의 별도 부속 규격은 유지한다.
    """)
    put(batch / 'specs/export.md', """
        # 정산 파일 송신 규격 v1 §2
        정산 책임자 한지민 승인. 야간 거래 파일에는 UTF-8 인코딩을 사용한다.
    """)
    put(batch / 'ops/nightly.md', """
        # 야간 송신 당직 인수서 v3
        같은 당직의 야간 송신 및 재처리 작업 절차다. §1 파트너 방화벽 점검이 있는 수요일은
        02:00~03:00에 야간 파일을 보내지 않는다. §2 전용 회선의 재처리는 당직 2인의 승인이 필요하다.
        §3 회선 승인은 유효 증빙으로 보관해야 한다. 이 자료의 파트너 연락망 절은 별도 권한이 필요하다.
    """)
    put(batch / 'specs/refunds.md', """
        # 온라인 환불 접수 규격 v1 §1
        2026-01-15 상품 정책 책임자 오지수 승인. 온라인 주문은 구매 다음 날부터 3일 안에 환불을 접수할 수 있다.
    """)
    base_tip = commit(batch, '정산 배치와 환불 접수')
    git(batch, 'switch', '-qc', 'receipt-notice')
    put(batch / 'specs/notice.md', """
        # 인수 알림 규격 v1 §1
        배송 운영 책임자 문서윤 승인. batch-api는 파트너 인수 알림에 보관함 식별자 lockerId를 반드시 포함한다.
    """)
    put(batch / 'src/notice.py', """
        def receipt_notice(locker_id):
            return {'lockerId': locker_id}
    """)
    commit(batch, '인수 알림 규격 v1 및 송신기')
    git(batch, 'switch', '-q', 'main')
    git(batch, 'merge', '--no-ff', '-qm', '파트너 인수 알림 연동', 'receipt-notice')
    put(field / 'src/terminal.py', """
        def accepts_receipt(age_hours):
            return age_hours <= 24
    """)
    put(field / 'specs/offline.md', """
        # 망분리 단말 부속 규격 v1 §3
        2026-03-20 현장 운영 책임자 박이든 승인. 망분리 오프라인 단말의 배송 증빙 재전송은 생성 후
        24시간까지 허용한다. 온라인 가맹점 기한 개정과 독립된 현장 단말 조항이다.
    """)
    field_tip = commit(field, '오프라인 단말 증빙 송신')

    wiki = root / 'wiki'
    init(wiki)
    knowledge = wiki / 'knowledge' / DOMAIN
    registry = {}
    for repo, description, tip in (
            (archive, '보관 영수증 열람', archive_tip),
            (batch, '정산 파일과 환불 접수', base_tip),
            (field, '현장 단말 배송 증빙 송신', field_tip)):
        registry[repo.name] = {'remote': str(repo), 'defaultBranch': 'main', 'summary': description,
                               'responsibilities': [description], 'hosts': []}
        json_file(wiki / 'state' / f'{repo.name}.json', {'cursor': tip, 'at': '2026-06-01'})
    json_file(wiki / 'registry.json', {'domains': {DOMAIN: {'repos': registry}}})
    json_file(wiki / 'deps.json', {'deps': {}})
    delivery = knowledge / 'delivery-window.md'
    doc(delivery, '배송 증빙 재전송', '온라인 가맹점의 배송 증빙 기한을 확인할 때', """
        ## 적용 대상

        - 온라인 가맹점 배송 증빙.

        ## 규칙

        - 온라인 가맹점은 생성 후 24시간까지 배송 증빙을 재전송할 수 있다. 출처는 배송 증빙 재전송 규격 v2 §1이다.
    """)
    doc(knowledge / 'batch-api' / 'delivery-retry.md', '온라인 증빙 재전송', '정산 배치에서 온라인 증빙을 재전송할 때', """
        ## 규칙

        - 온라인 가맹점은 생성 후 24시간까지 배송 증빙을 재전송할 수 있다. 배송 증빙 재전송 규격 v2 §1.
    """)
    doc(knowledge / 'field-console' / 'delivery-retry.md', '현장 단말 기한', '망분리 단말에서 배송 증빙을 재전송할 때', """
        ## 규칙

        - 망분리 오프라인 단말은 배송 증빙 생성 후 24시간까지 재전송할 수 있다.
          출처는 field-console의 specs/offline.md 망분리 단말 부속 규격 v1 §3이다.
    """)
    doc(knowledge / 'export-encoding.md', '정산 파일 인코딩', '야간 거래 파일의 송신 인코딩을 정할 때', """
        ## 적용 대상

        - 야간 거래 파일을 송신하는 batch-api.

        ## 규칙

        - 야간 거래 파일에는 UTF-8 인코딩을 사용한다. batch-api의 specs/export.md 정산 파일 송신 규격 v1 §2.
    """)
    doc(knowledge / 'batch-api' / 'export-batch.md', '야간 거래 파일 송신', '야간 거래 파일의 당직 송신·재처리를 수행할 때', """
        ## 규칙

        - 야간 거래 파일에는 UTF-8 인코딩을 사용한다. 정산 파일 송신 규격 v1 §2.
        - 파트너 방화벽을 점검하는 수요일 02:00~03:00에는 파일을 송신하지 않는다. 출처는 ops/nightly.md 야간 송신 당직 인수서 v3 §1이다.
        - export_batch는 normalize를 호출한 뒤 flush를 호출한다.
    """)
    doc(knowledge / 'batch-api' / 'export-replay.md', '야간 거래 파일 재처리', '야간 거래 파일의 당직 송신·재처리를 수행할 때', """
        ## 함정

        - 전용 회선의 재처리에는 당직 2인의 승인이 필요하다. 출처는 ops/nightly.md 야간 송신 당직 인수서 v3 §2다.
        - 이번 시연에서는 로컬 JAR demo-3.jar로 재처리를 확인했다.
    """)
    doc(knowledge / 'batch-api' / 'shift-handover.md', '당직 증빙 인계', '야간 당직이 회선 승인 증빙을 넘길 때', """
        ## 절차

        - 회선 승인 증빙을 보관한다. 송신 시각은 [야간 송신](export-batch.md#규칙), 당직 승인 수는 [야간 재처리](export-replay.md#함정)를 따른다. 출처는 ops/nightly.md 야간 송신 당직 인수서 v3 §3이다.
    """)
    doc(knowledge / 'refund-window.md', '온라인 환불 접수', '온라인 주문의 환불 접수 기한을 확인할 때', """
        ## 적용 대상

        - 온라인 주문의 환불 접수.

        ## 규칙

        - 구매 다음 날부터 3일 안에 환불을 접수할 수 있다. 온라인 환불 접수 규격 v1 §1.
    """)
    wiki_baseline = commit(wiki, '기존 운영 위키')
    json_file(wiki / 'state' / 'review' / f'{DOMAIN}.json',
              {'wiki': wiki_baseline, 'docs': 'batch-api/delivery-retry.md'})
    commit(wiki, '직전 문서 점검 위치')
    delivery.write_text(delivery.read_text().replace('24시간', '72시간').replace('규격 v2', '규격 v3'))
    commit(wiki, '온라인 가맹점 재전송 규격 v3')
    config = root / 'config.json'
    json_file(config, {'decisionSources': {DOMAIN: {'refund-board': 'project = MARKET'}}})
    record = {
        'id': 'MARKET-17#42', 'revision': 'r4', 'url': 'https://jira.example.invalid/browse/MARKET-17#42',
        'text': '2026-06-01 09:00 상품 정책 책임자 오지수 최종 결정. 온라인 환불 접수 규격 v1 §1의 3일을 '
                '구매 다음 날부터 8일로 대체한다. 온라인 주문 전체에 적용한다. 시행일 2026-06-01.',
    }
    draft = {
        'id': 'MARKET-17#41', 'revision': 'r3', 'url': 'https://jira.example.invalid/browse/MARKET-17#41',
        'text': '2026-05-31 상담사 이채리 제안. 환불을 20일로 늘리면 어떨까요? 정책 책임자 검토 전.',
    }
    records = [draft, record, {
        'id': 'MARKET-17#43', 'revision': 'r5', 'url': 'https://jira.example.invalid/browse/MARKET-17#43',
        'text': '2026-06-01 09:05 자동화 알림. 이슈 상태가 완료로 변경됨.',
    }]
    json_file(root / 'decisions.json', {'refund-board': {'scope': 'project = MARKET', 'from': None, 'through': 'r5', 'complete': True,
                                                          'records': records}})
    (root / 'workspace').mkdir()
    return root


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(create_fixture(parser.parse_args().directory))
