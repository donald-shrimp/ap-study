"""Review the two rewritten cases inside the real answer feedback flow."""

import os
import shutil

from playwright.sync_api import expect, sync_playwright

from browser_storage import open_written_case, read_written_material

URL = os.getenv('HITOMON_WRITTEN_URL', 'http://127.0.0.1:4173/ap/?part=written')


def item(page, id):
    button = page.locator(f'.written-item-nav [data-id="{id}"]')
    button.click()
    expect(button).to_have_attribute('aria-current', 'step')


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=shutil.which('chromium'))
    context = browser.new_context(viewport={'width': 390, 'height': 844})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL + '&entry=home')
    expect(page.locator('[data-action=written-packs]')).to_be_visible()

    open_written_case(page, 'ap-r04h-pm11')
    item(page, 'q4')
    ef = page.locator('.written-field[data-written-key="q4--ef"]')
    ef.locator('select').nth(0).select_option(label='カ 出荷指図データ')
    ef.locator('select').nth(1).select_option(label='カ 出荷指図データ')
    page.locator('[data-action=written-check-item]').click()
    expect(ef.locator('.written-answer h4')).to_have_text('自動判定：不正解')
    expect(ef.locator('.reference-answer')).to_have_text(['出荷指図データ（カ）', '出荷実績データ（キ）'])
    expect(ef.locator('.explanation')).to_contain_text('8個だけ出荷')
    expect(ef.locator('.written-rubric')).to_have_count(0)
    for width in (320, 390, 1440):
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), width
        expect(ef.locator('.reference-answer').last).to_be_visible()

    gh = page.locator('.written-field[data-written-key="q4--gh"]')
    gh.locator('select').nth(0).select_option(label='ク 倉庫残高データ')
    gh.locator('select').nth(1).select_option(label='エ 在庫データ')
    page.locator('[data-action=written-check-item]').click()
    expect(gh.locator('.written-answer h4')).to_have_text('自動判定：正解')
    assert set(gh.locator('.reference-answer').all_text_contents()) == {'倉庫残高データ（ク）', '在庫データ（エ）'}

    item(page, 'q3')
    page.locator('[data-answer-set-entry]').nth(0).fill('売上データ')
    page.locator('[data-answer-set-entry]').nth(1).fill('出荷指図データ')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.written-rubric summary')).to_have_text('確認ポイント')
    page.locator('.written-rubric summary').click()
    expect(page.locator('.written-rubric p')).to_contain_text('矢印で書き出して')

    item(page, 'q2')
    page.locator('textarea[data-written-key]').fill('営業担当者が売上を訂正できるため')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.written-rubric h4')).to_have_text('自己評価の基準')
    expect(page.locator('.written-rubric li')).to_contain_text('担当者と権限の関係')
    expect(page.locator('[data-action=written-rate]')).to_have_count(4)
    page.locator('[data-action=written-rate][data-outcome=meets]').click()
    expect(page.locator('.written-rubric p')).to_contain_text('要点を満たした')

    page.set_viewport_size({'width': 390, 'height': 844})
    open_written_case(page, 'ap-r05h-pm1', 'exam')
    item(page, 's4-1')
    page.locator('textarea[data-written-key]').fill('ア')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.written-field-status')).to_have_text('回答済み')
    expect(page.locator('.written-answer')).to_have_count(0)
    page.locator('.assessment-menu summary').click()
    page.locator('[data-action=written-review-partial]').click()
    expect(page.locator('.reference-answer')).to_have_text('検知／通報（受付）（ア）')
    page.get_by_role('button', name='図1を見る', exact=True).click()
    figure = page.locator('#written-ref-answer-s4-1--answer')
    expect(figure.locator('figcaption')).to_have_text('図1 一連のインシデント対応フロー')
    expect(figure).to_be_in_viewport()

    page.locator('.sidebar [data-view=home]').click()
    page.locator('[data-action=written-packs]').click()
    page.locator('[data-action=written-pack][data-pack="2023-spring"]').click()
    page.locator('[data-action=offline-open][data-pack="2023-spring"]').click()
    page.locator('[data-offline-save]').click()
    expect(page.locator('#offline-message')).to_contain_text('保存できました', timeout=60000)
    page.locator('[data-offline-close]').click()
    context.set_offline(True)
    page.reload()
    open_written_case(page, 'ap-r05h-pm1')
    item(page, 's1-2')
    page.locator('textarea[data-written-key]').fill('5')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.reference-answer')).to_have_text('インストール（5）')

    # Simulate opening the exercise from an older download, then reconnecting.
    assert page.evaluate("""async () => {
        const {loadCatalog,contentCacheName}=await import(new URL('src/content/catalog.js',document.baseURI));
        const content=await loadCatalog('ap',{requestedPartId:'written'});
        const cache=await caches.open(contentCacheName);
        return cache.delete(new URL('data/qualifications/ap/'+content.manifest.cases.answerSets.url,document.baseURI));
    }""")
    page.reload()
    open_written_case(page, 'ap-r05h-pm1')
    item(page, 's3-3')
    assert read_written_material(page)['version'] == 1
    context.set_offline(False)
    page.reload()
    page.locator('textarea[data-written-key]').fill('ア、ウ')
    page.locator('[data-action=written-submit]').click()
    expect(page.locator('.reference-answer')).to_have_text(['使用された攻撃手法（ア）', '被害を受けた機器の種類（ウ）'])
    expect(page.locator('.written-rubric h4')).to_have_text('自己評価の基準')
    assert read_written_material(page)['version'] == 1
    assert not errors, errors
    browser.close()

print('PASS answer content, optional review point, self assessment, figure jump, exam disclosure, offline, legacy run and 320/390/1440px')
