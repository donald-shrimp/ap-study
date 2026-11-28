"""Exercise all display modes and joint grading on the real written study screen."""

import os
import shutil

from playwright.sync_api import expect, sync_playwright

from browser_storage import nav, open_written_case, read_written_material

URL = os.getenv('HITOMON_WRITTEN_URL', 'http://127.0.0.1:4173/ap/?part=written')


def question(page, case_id, item_id, mode='learning'):
    open_written_case(page, case_id, mode)
    tab = page.locator(f'.written-item-nav [data-id="{item_id}"]')
    tab.click()
    expect(tab).to_have_attribute('aria-current', 'step')
    group = page.locator('.written-field:has([data-answer-set])')
    expect(group).to_be_visible()
    return group


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=shutil.which('chromium'))
    ctx = browser.new_context(viewport={'width': 390, 'height': 844})
    page = ctx.new_page()
    page.set_default_timeout(12000)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(URL + '&entry=home')
    expect(page.locator('[data-action=written-packs]')).to_be_visible()

    choices = question(page, 'ap-r07h-pm2', 'q2-1')
    expect(choices.get_by_role('combobox', name='b', exact=True)).to_be_visible()
    first, second = (choices.locator('select').nth(n) for n in range(2))
    for width in (320, 390, 1440):
        page.set_viewport_size({'width': width, 'height': 900})
        expect(first).to_be_visible()
        expect(second).to_be_visible()
        assert first.bounding_box()['height'] >= 44, width
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), width
    page.set_viewport_size({'width': 390, 'height': 844})
    first.select_option(label='ウ 強み')
    expect(choices.locator('[data-action=written-submit]')).to_be_disabled()
    page.reload()
    expect(first).to_have_value('choice-3')
    second.select_option(label='イ 脅威')
    choices.locator('[data-action=written-submit]').click()
    expect(choices.locator('.written-answer h4')).to_have_text('自動判定：正解')
    assert choices.locator('[data-action=written-rate]').count() == 0

    choices = question(page, 'ap-r07h-pm2', 'q2-1', mode='exam')
    for control in choices.locator('select').all():
        control.select_option(label='イ 脅威')
    choices.locator('[data-action=written-submit]').click()
    expect(choices.locator('.written-field-status')).to_have_text('回答済み')
    assert not choices.locator('.written-answer').count()
    page.locator('.assessment-menu summary').click()
    page.locator('[data-action=written-review-partial]').click()
    expect(choices.locator('.written-answer h4')).to_have_text('自動判定：不正解')

    multiple = question(page, 'ap-r07h-pm8', 'q2')
    expect(multiple.get_by_role('checkbox')).to_have_count(4)
    multiple.get_by_label('開発担当者', exact=True).check()
    multiple.get_by_label('運用担当者', exact=True).check()
    multiple.locator('[data-action=written-submit]').click()
    expect(multiple.locator('.written-answer h4')).to_have_text('自動判定：正解')

    dynamic = question(page, 'ap-r05a-pm8', 'q3-1')
    inputs = dynamic.locator('[data-answer-set-entry]')
    expect(inputs).to_have_count(1)
    inputs.first.fill('処理７')
    dynamic.locator('[data-action=written-set-add]').click()
    expect(inputs.nth(1)).to_be_focused()
    inputs.nth(1).fill('処理2')
    dynamic.locator('[data-action=written-set-add]').click()
    dynamic.get_by_role('button', name='回答 3を削除', exact=True).click()
    expect(inputs).to_have_count(2)
    page.reload()
    expect(inputs).to_have_count(2)
    expect(inputs.first).to_have_value('処理７')
    expect(inputs.nth(1)).to_have_value('処理2')
    for width in (320, 390, 1440):
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), width
    dynamic.locator('[data-action=written-submit]').click()
    expect(dynamic.locator('.written-answer h4')).to_have_text('自動判定：正解')

    fixed = question(page, 'ap-r04h-pm11', 'q3')
    expect(fixed.locator('input[maxlength="10"]')).to_have_count(2)
    assert not fixed.locator('[data-action=written-set-add]').count()
    fixed.locator('input').nth(0).fill('売上データ')
    fixed.locator('input').nth(1).fill('出荷指図データ')
    fixed.locator('[data-action=written-submit]').click()
    expect(fixed.locator('.written-answer h4')).to_have_text('自動判定：正解')
    page.locator('.study-back-button').click()
    page.locator('[data-action=written-packs]').click()
    page.locator('[data-action=written-pack][data-pack="2025-spring"]').click()
    page.locator('[data-action=offline-open][data-pack="2025-spring"]').click()
    page.locator('[data-offline-save]').click()
    expect(page.locator('#offline-message')).to_contain_text('保存できました', timeout=60000)
    page.locator('[data-offline-close]').click()
    ctx.set_offline(True)
    page.reload()
    question(page, 'ap-r07h-pm2', 'q2-1')
    # An older offline download is still usable before the format update arrives.
    assert page.evaluate("""async()=> {
        const {loadCatalog,contentCacheName}=await import(new URL('src/content/catalog.js',document.baseURI));
        const content=await loadCatalog('ap',{requestedPartId:'written'});
        const cache=await caches.open(contentCacheName);
        const url=new URL('data/qualifications/ap/'+content.manifest.cases.answerSets.url,document.baseURI);
        return cache.delete(url.href);
    }""")
    page.reload()
    expect(page.locator('[data-answer-set-entry]')).to_have_count(2)
    open_written_case(page, 'ap-r07h-pm2')
    page.locator('.written-item-nav [data-id="q1-2"]').click()
    page.locator('textarea[data-written-key="q1-2--a"]').fill('シナジー')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
    page.locator('.written-item-nav [data-id="q2-1"]').click()
    expect(page.locator('.written-field[data-written-key="q2-1--bc"] textarea')).to_be_visible()
    assert read_written_material(page)['version'] == 1
    original_id = page.evaluate("""() => {
        const key = Object.keys(localStorage).find(key => key.includes(':ap:written-view'));
        return JSON.parse(localStorage.getItem(key)).currentId;
    }""")
    expect(page.locator('[data-action=written-use-new-fields]')).to_have_count(0)

    ctx.set_offline(False)
    page.reload()
    update = page.get_by_role('button', name='新しい回答欄で続ける', exact=True)
    expect(update).to_be_visible()
    update.click()
    expect(page.get_by_role('combobox', name='b', exact=True)).to_be_focused()
    expect(page.get_by_role('combobox', name='c', exact=True)).to_be_visible()
    assert read_written_material(page)['version'] == 2
    page.locator('.written-item-nav [data-id="q1-2"]').click()
    expect(page.locator('.written-answer h4')).to_have_text('自動判定：正解')
    expect(page.locator('textarea[data-written-key="q1-2--a"]')).to_have_value('シナジー')
    nav(page, 'history')
    page.locator(f'[data-action=written-resume][data-id="{original_id}"]').click()
    expect(page.locator('.written-field[data-written-key="q2-1--bc"] textarea')).to_be_visible()
    assert read_written_material(page)['version'] == 1
    assert not errors, errors
    browser.close()

print('PASS fixed selects, multiple choice, fixed/dynamic text, duplicates, exam disclosure, draft reload, legacy transition and 320/390/1440px')
