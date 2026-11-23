"""Publish a private qualification with direct case fields and shared contract examples."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from common_fixtures import builder, prepare, write
from case_field import validate_case_field
from written_content import canonical

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/case-grading.json').read_text(encoding='utf-8'))
FIELDS = [
    {'label': field['id'], 'explanation': '形式検査用の解説', 'rubric': ['解答を確認'],
     **field, **({'choices': FIXTURE['choices']} if 'correctChoiceIds' in field else {})}
    for field in FIXTURE['fields']
]
CASE = {
    'id': 'fixture-case', 'qualificationId': 'fixture', 'examPartId': 'written', 'topicId': 'a',
    'version': 1, 'status': 'reviewed', 'title': '合成大問', 'source': '合成テスト',
    'body': '共通本文。', 'sourceImages': [], 'bodyFigures': [],
    'items': [{'id': field['id'], 'label': field['label'], 'prompt': '回答してください。', 'fields': [field]}
              for field in FIELDS],
}


def reject(operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError('Invalid field was accepted')


def check_contract():
    import jsonschema

    schema = json.loads((ROOT / 'schemas/case-field.v1.json').read_text(encoding='utf-8'))
    validator = jsonschema.Draft202012Validator(schema)
    for field in FIELDS:
        validator.validate(field)
        validate_case_field(field)
    for row in FIXTURE['invalid']:
        base = next(field for field in FIELDS if field['id'] == row['field'])
        invalid = {**base, **row['patch']}
        reject(lambda: validate_case_field(invalid))
        if row.get('schemaRejects'):
            assert not validator.is_valid(invalid), invalid


def check_browser(root):
    import shutil
    import threading
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from browser_storage import open_written_case
    from playwright.sync_api import expect, sync_playwright

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(root))) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=shutil.which('chromium'))
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}/fixture/?part=written')
                open_written_case(page, CASE['id'])
                page.locator('[data-written-key="one--one"] input[value=pine]').check()
                page.locator('[data-action=written-submit]').click()
                expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
                expect(page.locator('.reference-answer')).to_have_text('マツ（ロ）')

                page.locator('.written-item-nav [data-id=all]').click()
                page.locator('input[data-answer-set-choice][value=pine]').check()
                page.locator('[data-action=written-submit]').click()
                expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
                expect(page.locator('.correct-choice')).to_contain_text('ロ')

                page.locator('.written-item-nav [data-id=fixed]').click()
                page.get_by_role('combobox', name='a').select_option('oak')
                page.get_by_role('combobox', name='b').select_option('cedar')
                page.locator('[data-action=written-submit]').click()
                expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
                page.reload()
                expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')

                page.locator('.written-item-nav [data-id=words]').click()
                entries = page.locator('input[data-answer-set-entry]')
                expect(entries).to_have_count(1)
                entries.first.fill('スギ')
                page.locator('[data-action=written-set-add]').click()
                expect(entries).to_have_count(2)
                entries.last.fill('ナラ')
                page.locator('[data-action=written-submit]').click()
                expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()


def main():
    browser = '--browser' in sys.argv
    if not browser:
        check_contract()
    with tempfile.TemporaryDirectory(prefix='hitomon-case-grading-') as directory:
        root = Path(directory)
        config, _, _ = prepare(root)
        source = root / 'content/fixture'
        config.update(caseSource='content/fixture/cases.json', caseReviewSource='content/fixture/case-reviews.json',
                      examParts=[{'id': 'objective', 'label': '選択式', 'practiceAvailable': True},
                                 {'id': 'written', 'label': '記述式', 'practiceAvailable': True, 'unit': 'cases'}])
        write(source / 'qualification.json', config)

        def publish(case):
            write(source / 'cases.json', [case])
            write(source / 'case-reviews.json', [
                {'caseId': case['id'], 'status': 'approved', 'author': 'synthetic-author',
                 'reviewer': 'synthetic-reviewer', 'canonicalCaseSHA256': hashlib.sha256(canonical(case)).hexdigest(),
                 'assetHashes': {}, 'sourceHashes': {}}
            ])
            builder.build(root)

        broken = {**CASE, 'items': [{**CASE['items'][0], 'fields': [{**FIELDS[0], 'correctChoiceIds': ['bad']}]}]}
        reject(lambda: publish(broken))
        publish(CASE)
        bank = root / 'data/qualifications/fixture'
        manifest = json.loads((bank / 'manifest.json').read_text(encoding='utf-8'))
        assert 'answerSets' not in manifest['cases']
        assert json.loads((bank / manifest['cases']['url']).read_text(encoding='utf-8'))['cases'] == [CASE]
        if browser:
            check_browser(root)
    print('PASS direct case authoring, invalid authoring rejected, and ' + ('browser / reload' if browser else 'schema / runtime fixture parity'))


if __name__ == '__main__':
    main()
