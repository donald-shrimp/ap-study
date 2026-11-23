"""Whole-case reflection on the real application with isolated guest records."""
import json
import os
import shutil
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from browser_storage import nav, open_written_case, open_written_field_actions, read_written_material, fill_written_field

ROOT = Path(__file__).resolve().parents[1]
ART = Path(tempfile.mkdtemp(prefix='hitomon-reflection-browser-'))
CASES = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text(encoding='utf-8'))}


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def submit(page, case, *, skipped_first=False):
    active=read_written_material(page)
    assert active['id']==case['id']
    for item_index, item in enumerate(active['items']):
        tab = page.locator(f'.written-item-nav [data-id="{item["id"]}"]')
        tab.click()
        expect(tab).to_have_attribute('aria-current', 'step')
        open_written_field_actions(page)
        for index, field in enumerate(item['fields']):
            key = item['id'] + '--' + field['id']
            slot = page.locator(f'.written-field[data-written-key="{key}"]')
            if skipped_first and item_index == index == 0:
                slot.locator('[data-action=written-skip]').click()
            else:
                fill_written_field(slot, field)
                slot.locator('[data-action=written-submit]').click()
            expect(slot.locator('textarea[readonly], input[readonly], fieldset[disabled], select[disabled]').first).to_be_visible()


def rate(page, case):
    active=read_written_material(page)
    assert active['id']==case['id']
    for item in active['items']:
        page.locator(f'.written-item-nav [data-id="{item["id"]}"]').click()
        for field in item['fields']:
            key = item['id'] + '--' + field['id']
            slot = page.locator(f'.written-field[data-written-key="{key}"]')
            expect(slot).to_be_visible()
            open_answer = slot.locator('[data-action=written-answer]')
            if open_answer.is_visible():
                open_answer.click()
            expect(slot.locator('.written-answer')).to_be_visible()
            rating = slot.locator('[data-outcome=meets]')
            if rating.count() and rating.is_enabled():
                rating.click()
                expect(slot.locator('.written-field-status')).to_contain_text('自己評価')


def open_reflection(page):
    page.locator('.written-reflection-entry button').click()
    expect(page.locator('.written-reflection-toc')).to_be_visible()


def widths(page):
    for width in [320, 390, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        page.evaluate('window.scrollTo(0,0)')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), width
        page.screenshot(path=str(ART / f'reflection-{width}.png'))
    page.set_viewport_size({'width': 320, 'height': 900})
    page.locator('#settings-button').click()
    for _ in range(4):
        page.locator('#text-larger').click()
    expect(page.locator('#text-size')).to_have_text('140%')
    page.get_by_role('button', name='設定を閉じる', exact=True).click()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    expect(page.locator('[data-action=written-reflection-toc]')).to_be_hidden()
    page.locator('.written-reflection-section').last.scroll_into_view_if_needed()
    page.get_by_role('button', name='目次へ').click()
    expect(page.locator('#written-reflection-toc')).to_be_focused()
    page.screenshot(path=str(ART / 'reflection-toc-320-large.png'))


def check_algorithm(page, url):
    case = CASES['ap-r07a-pm3']
    page.goto(url + '&entry=home')
    open_written_case(page, case['id'], 'exam')
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    first = page.locator('.written-field').first
    first.locator('textarea').fill(case['items'][0]['fields'][0]['referenceAnswers'][0])
    first.locator('[data-action=written-submit]').click()
    expect(first.locator('.written-field-status')).to_contain_text('回答済み')
    # The handler must also enforce the gate, independent of button visibility.
    page.locator('.written-items').evaluate('el=>{const b=document.createElement("button");b.dataset.action="written-reflection-open";el.append(b);b.click();b.remove();}')
    expect(page.locator('.written-answer, .written-reflection')).to_have_count(0)
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    page.locator('.assessment-menu > summary').click()
    page.locator('[data-action=written-review-partial]').click()
    expect(first.locator('.written-answer')).to_be_visible()
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    nav(page, 'home')
    open_written_case(page, case['id'], 'exam')
    submit(page, case, skipped_first=True)
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    expect(page.locator('.written-answer')).to_have_count(0)
    page.locator('[data-action=written-review-start]').click()
    expect(page.locator('.written-answer')).to_be_visible()
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    rate(page, case)
    expect(page.locator('.written-reflection-entry button')).to_have_css('background-color', 'rgb(8, 125, 121)')
    open_reflection(page)
    page.locator('[data-action=written-reflection-expand]').click()
    expect(page.locator('.written-reflection .question-table').first).to_be_visible()
    expect(page.locator('.written-reflection .question-code').first).to_be_visible()
    expect(page.locator('.written-reflection-text ul').first).to_be_visible()
    widths(page)
    page.locator('[data-action=written-reflection-answer]').first.click()
    expect(page.locator('.written-answer h4').first).to_be_focused()
    expect(page.locator('.written-layout')).to_be_visible()
    expect(page.locator('.written-reflection-entry')).to_have_count(0)
    page.locator('.written-reflection-return').click()
    expect(page.locator('.written-reflection-toc')).to_be_visible()
    assert page.locator('details[data-reflection-section]').count() == page.locator('details[data-reflection-section][open]').count()
    expect(page.locator('[data-action=written-next]')).to_be_visible()
    jump = page.locator('[data-action=written-reflection-jump]').first
    target = jump.get_attribute('data-id')
    jump.press('Enter')
    section = page.locator(f'details[data-reflection-section="{target}"]')
    expect(section.locator('summary')).to_be_focused()
    page.reload()
    expect(section).to_have_attribute('open', '')
    nav(page, 'history')
    page.locator('[data-action=written-reflection-open]').click()
    expect(section).to_be_visible()


def check_pack_download(page, context, url):
    case = CASES['ap-r07a-pm6']
    page.goto(url + '&entry=home')
    page.wait_for_function('!!navigator.serviceWorker.controller')
    page.locator('[data-action=written-packs]').click()
    page.locator('[data-action=written-pack][data-pack="2025-autumn"]').click()
    page.locator('#main [data-action=offline-open]').click()
    expect(page.locator('[data-offline-group]')).to_have_count(1)
    expect(page.locator('[data-offline-group="cases-ap-r07a-pm1"]')).to_be_checked()
    page.locator('[data-offline-save]').click()
    expect(page.locator('#offline-message')).to_contain_text('保存できました', timeout=60000)
    page.locator('[data-offline-close]').click()
    context.set_offline(True)
    open_written_case(page, case['id'])
    submit(page, case, skipped_first=True)
    rate(page, case)
    open_reflection(page)
    page.locator('[data-action=written-reflection-expand]').click()
    expect(page.locator('.written-reflection pre').filter(has_text='ALTER TABLE')).to_be_visible()
    page.locator('[data-action=written-reflection-study][data-pane=body]').first.click()
    expect(page.locator('.written-body')).to_be_visible()
    page.locator('.written-reflection-return').click()
    expect(page.locator('.written-reflection-toc')).to_be_visible()
    context.set_offline(False)


def check_audit(page, url):
    case = CASES['ap-r05h-pm11']
    page.goto(url + '&entry=home')
    open_written_case(page, case['id'])
    submit(page, case)
    rate(page, case)
    page.route('**/case-explanations-2023-spring.*.json', lambda route: route.abort())
    page.locator('.written-reflection-entry button').click()
    expect(page.get_by_text('大問解説を読み込めませんでした。')).to_be_visible()
    page.unroute('**/case-explanations-2023-spring.*.json')
    page.get_by_role('button', name='再試行', exact=True).click()
    expect(page.locator('.written-reflection-toc')).to_be_visible()
    jump = page.locator('[data-action=written-reflection-jump]').filter(has_text='利用者ID')
    jump.click()
    section = page.locator(f'details[data-reflection-section="{jump.get_attribute("data-id")}"]')
    assert section.locator('[data-action=written-reflection-answer]').count() == 2
    answer = section.locator('[data-action=written-reflection-answer]').last
    answer.scroll_into_view_if_needed()
    position = page.evaluate('window.scrollY')
    answer.click()
    expect(page.locator('.written-answer h4').last).to_be_focused()
    page.locator('.written-reflection-return').click()
    expect(section).to_have_attribute('open', '')
    assert abs(page.evaluate('window.scrollY') - position) <= 1


def check_round(page, url):
    page.goto(url + '&entry=home')
    page.locator('[data-action=written-packs]').click()
    page.locator('[data-action=written-pack][data-pack="2025-autumn"]').click()
    page.locator('[data-action=written-sequence]').click()
    for number in range(1, 12):
        case = CASES[f'ap-r07a-pm{number}']
        expect(page.locator('.case-heading h1')).to_have_text(case['title'])
        expect(page.locator('.case-study-scope')).to_contain_text('番号順')
        submit(page, case)
        rate(page, case)
        expect(page.locator('.written-reflection-entry .primary')).to_be_visible()
        open_reflection(page)
        if number == 5:
            page.reload()
            expect(page.locator('.written-reflection-toc')).to_be_visible()
        if number == 6:
            # The reflection still targets the original c and d fields.
            answer = page.locator('[data-action=written-reflection-answer][data-written-key="q2-1--c"]').first
            section = answer.locator('xpath=ancestor::details[1]')
            if section.get_attribute('open') is None:
                section.locator('summary').click()
            answer.click()
            expect(page.locator('.written-field[data-written-key="q2-1--c"] .written-answer h4')).to_be_focused()
            page.locator('.written-reflection-return').click()
            expect(section).to_have_attribute('open', '')
        next_case = page.locator('[data-action=written-next]')
        if number < 11:
            next_case.click()
        else:
            expect(next_case).to_have_count(0)


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/ap/?part=written'
    try:
        with sync_playwright() as playwright:
            chrome = shutil.which('chromium')
            browser = playwright.chromium.launch(executable_path=chrome, channel=os.getenv('HITOMON_CHROME_CHANNEL'))
            checks = [check_algorithm, check_pack_download, check_audit]
            if os.getenv('HITOMON_TEST_FULL_ROUND') == '1':
                checks.append(check_round)
            for verify in checks:
                ctx = browser.new_context(
                    viewport={'width': 390, 'height': 844},
                    service_workers='block' if verify is check_audit else 'allow',
                )
                page = ctx.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                if verify is check_pack_download:
                    verify(page, ctx, url)
                else:
                    verify(page, url)
                assert not errors, errors
                ctx.close()
            browser.close()
        print(f'Whole-case reflection, {len(checks)} flows and 3 widths: {ART}')
    finally:
        server.shutdown()


if __name__ == '__main__':
    main()
