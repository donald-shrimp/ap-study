"""Read-only editorial viewer: real records survive browsing and draft inspection."""
import json
import os
import shutil
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from browser_storage import state, READ_STATE

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('HITOMON_TEST_URL', 'http://127.0.0.1:4173/')
VIEWER = urljoin(URL, 'docs/diagnostic-review.html')
bank = json.loads((ROOT/'content/ap/diagnostic-questions.json').read_text())
progress = json.loads((ROOT/'content/ap/diagnostic-progress.json').read_text())
pending = [item for item in progress['items'] if item['status'] == 'awaiting-independent-review']
pending_ids = {item['questionId'] for item in pending}
drafts = []
for path in {item['draftBatchPath'] for item in pending}:
    drafts += [q for q in json.loads((ROOT/path).read_text())['questions'] if q['id'] in pending_ids]
index = json.loads((ROOT/'data/qualifications/ap/manifest.json').read_text())['index']['url']
parents = {q['id']:q for q in json.loads((ROOT/'data/qualifications/ap'/index).read_text())}
with sync_playwright() as p:
    options = {'executable_path':shutil.which('chromium'), 'args':['--no-sandbox']}
    if URL.startswith('https:') and os.getenv('HTTPS_PROXY'):
        options['proxy'] = {'server':os.environ['HTTPS_PROXY'], 'bypass':'127.0.0.1,localhost'}
    browser = p.chromium.launch(**options)
    context = browser.new_context(viewport={'width':390,'height':844})
    context.add_init_script('''
      window.__editorWrites=[];
      for (const [prototype, methods] of [[Storage.prototype,['setItem','removeItem','clear']], [IDBObjectStore.prototype,['put','add','delete','clear']]]) {
        for (const method of methods) { const original=prototype[method]; prototype[method]=function(...args){window.__editorWrites.push(method);return original.apply(this,args);}; }
      }
    ''')
    page = context.new_page(); errors=[]; requests=[]
    page.on('pageerror', lambda error:errors.append(str(error)))
    page.on('request', lambda request:requests.append(request.url))
    if URL.startswith('https:'): page.set_default_timeout(60000)
    page.goto(URL)
    page.get_by_role('button',name='おまかせで1問',exact=True).click()
    page.get_by_role('button',name='回答する',exact=True).wait_for()
    page.get_by_role('button',name='中断',exact=True).click()
    before = state(page)
    storage = page.evaluate('JSON.stringify({...localStorage})')
    assert before['attempts'], 'Seed a real interrupted learning attempt.'
    requests.clear()
    page.goto(VIEWER)
    page.locator('#question-panel').wait_for()
    assert page.locator('#question-list button').count() == len(bank)+len(pending)
    assert page.locator('#result').is_hidden()
    assert not page.locator('#list-panel').evaluate('(el)=>el.open'), 'Mobile starts with compact list.'
    page.locator('#topic').select_option('network')
    assert all('ネットワーク' in text for text in page.locator('#question-list button').all_text_contents())
    page.locator('#reveal').click()
    assert page.locator('#result').is_visible() and page.locator('#reasons li').count() == 4
    page.locator('#original-details > summary').click()
    page.wait_for_function('Array.from(document.querySelectorAll("#original-images img")).every(img=>img.complete&&img.naturalWidth>0)')
    assert page.locator('#original-images img').count() > 0
    page.locator('#original-answer').evaluate('(el)=>el.parentElement.open=true')
    assert page.locator('#original-answer').inner_text() == '公式正解：イ'
    page.locator('#topic').select_option('')
    page.locator('#status').select_option('draft')
    assert page.locator('#question-list button').count() == len(pending)
    if pending:
        assert page.locator('#draft-notice').is_visible()
        page.locator('#search').fill(pending[0]['parentQuestionId'])
        assert page.locator('#question-list button').count() == 1
        page.locator('#choices input').first.check()
        page.locator('#reveal').click()
        assert page.locator('#answer-heading').inner_text().startswith('正解：')
        assert page.locator('#reasons li').count()==4
        page.locator('#search').fill('該当なし-test')
        assert page.locator('#empty').is_visible() and page.locator('#question-panel').is_hidden()
        page.goto(VIEWER+'#'+pending[-1]['questionId'])
        page.locator('#question-panel').wait_for()
        assert pending[-1]['questionId'] in page.locator('#identity').inner_text()
    page.locator('#status').select_option('published')
    assert page.locator('#question-list button').count()==len(bank), 'Archived initial drafts do not appear twice.'
    page.locator('#next').click()
    assert page.locator('#result').is_hidden()
    # Every item, including diagrams and newly authored drafts, can be inspected.
    for q in bank+drafts:
        page.evaluate('(id)=>location.hash=id',q['id'])
        page.wait_for_function('(id)=>document.querySelector("#identity").textContent.startsWith(id)',arg=q['id'])
        assert page.locator('#stem').inner_text()==q.get('stem','')
        page.locator('#choices input').first.check()
        page.locator('#reveal').click()
        correct=next(c['label'] for c in q['choices'] if c['id']==q['correctChoiceId'])
        assert page.locator('#answer-heading').inner_text().startswith('正解：'+correct)
        assert page.locator('#reasons li').count()==4
        page.locator('#original-details').evaluate('(el)=>el.open=true')
        page.wait_for_function('Array.from(document.querySelectorAll("#original-images img, #figures img, #choices img")).every(img=>img.complete&&img.naturalWidth>0)')
        parent=parents[q['parentQuestionId']]
        assert page.locator('#original-answer').text_content()=='公式正解：'+next(c['label'] for c in parent['choices'] if c['id']==parent['correctChoiceId'])
    # Test the actual read-only boundary, not just absence of a save button.
    assert page.evaluate('window.__editorWrites') == []
    assert page.evaluate('JSON.stringify({...localStorage})') == storage
    assert not any(('googleapis.com' in url or '/src/storage/' in url or '/src/sync/' in url or 'firebase' in url) for url in requests)
    # Read the real adapter through the correct app base without navigating/app writes.
    snapshot_reader = READ_STATE.replace("new URL('.',document.baseURI)", "new URL('../',location.href)")
    assert page.evaluate(snapshot_reader) == before
    for width, scale in [(320,1),(390,1),(900,1),(320,2)]:
        page.set_viewport_size({'width':width,'height':900})
        page.evaluate('(scale)=>document.documentElement.style.fontSize=(16*scale)+"px"',scale)
        page.locator('#list-panel').evaluate('(el)=>el.open=true')
        if page.locator('#result').is_hidden(): page.locator('#reveal').click()
        for details in page.locator('#question-panel details').all(): details.evaluate('(el)=>el.open=true')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (width,scale)
    assert not errors, errors
    context.close(); browser.close()
print('Editorial viewer passed: filters, drafts, original/answers, layout and real learning-record isolation.')
