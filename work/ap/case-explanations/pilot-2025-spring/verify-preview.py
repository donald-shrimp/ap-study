"""Exercise the local editorial HTML at mobile/desktop sizes; no app writes."""
import json
import shutil
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = Path(tempfile.mkdtemp(prefix='hitomon-explanation-preview-'))

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/{HERE.relative_to(ROOT)}/preview.html'
checks = []
linked_checks = []
mapping = json.loads((HERE / 'explanation-links.json').read_text())
bank = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text())}
try:
    with sync_playwright() as w:
        browser = w.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(url)
        for cid in mapping:
            page.locator(f'.preview-nav a[href="#{cid}"]').click()
            assert page.locator('.preview-case:visible').count() == 1
            assert page.locator('.preview-case:visible').get_attribute('id') == cid
            for target in mapping[cid]:
                anchor = cid+'--'+target['id']
                page.locator('.preview-case:visible details').evaluate_all('(nodes)=>nodes.forEach(n=>n.open=false)')
                page.locator(f'.preview-question-link[href="#{anchor}"]').click()
                page.wait_for_function('(id)=>document.activeElement.id===id', arg=anchor)
                heading = page.locator('[id="'+anchor+'"]')
                assert heading.is_visible() and heading.inner_text() == target['heading']
                assert heading.evaluate('(el)=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==="DETAILS"&&!p.open)return false;return true;}')
                if heading.evaluate('(el)=>el.tagName') == 'SUMMARY':
                    assert heading.evaluate('(el)=>el.tabIndex') == 0
                    page.keyboard.press('Enter')
                    assert heading.evaluate('(el)=>!el.parentElement.open')
                    page.keyboard.press('Enter')
                    assert heading.evaluate('(el)=>el.parentElement.open')
                context = heading.locator('xpath=following-sibling::*[1]')
                source = context.locator('.preview-source-question').first
                source.locator('summary').click()
                item = next(i for i in bank[cid]['items'] if i['id'] == target['itemId'])
                text = source.inner_text()
                assert ''.join(item['prompt'].split()) in ''.join(text.split()), (cid, target['id'])
                page.reload()
                page.wait_for_function('(id)=>document.activeElement.id===id', arg=anchor)
                assert page.locator('.preview-case:visible').get_attribute('id') == cid
                section = page.locator('[id="'+anchor+'"]').locator('xpath=ancestor::*[contains(concat(" ",normalize-space(@class)," ")," preview-section ")][1]')
                section.locator('.preview-return').click()
                page.wait_for_function('(id)=>document.activeElement.id===id', arg=cid+'--questions')
                linked_checks.append({'caseId': cid, 'itemId': target['itemId'], 'fieldIds': target['fieldIds'], 'anchor': anchor, 'openJumpPromptReloadReturn': True})
            page.locator('#expand').click()
            assert page.locator('.preview-case:visible details:not([open])').count() == 0
            assert page.locator('.preview-case:visible h2').count() == 3
            for width in [320, 390, 1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (cid, width)
                assert page.locator('h1:visible').is_visible()
                checks.append({'caseId': cid, 'width': width, 'pageOverflow': False})
            page.locator(f'.preview-nav a[href="#{cid}"]').click()
            page.reload()
            assert page.locator('.preview-case:visible').get_attribute('id') == cid
            page.locator('.preview-case:visible details').first.locator(':scope > summary').focus()
            page.keyboard.press('Enter')
            assert page.locator('.preview-case:visible details').first.evaluate('(el)=>el.open')
        # In-page history, cross-case deep links and repeating the same link.
        a = 'ap-r07h-pm6--q2-c-from'
        b = 'ap-r07h-pm6--q2-d-join'
        page.goto(url+'#'+a)
        page.wait_for_function('(id)=>document.activeElement.id===id', arg=a)
        page.locator('.preview-question-link[href="#'+b+'"]').click()
        page.wait_for_function('(id)=>document.activeElement.id===id', arg=b)
        page.go_back()
        page.wait_for_function('(id)=>document.activeElement.id===id', arg=a)
        page.go_forward()
        page.wait_for_function('(id)=>document.activeElement.id===id', arg=b)
        page.locator('[id="'+b+'"]').evaluate('(el)=>el.closest("details.preview-section").open=false')
        page.locator('.preview-question-link[href="#'+b+'"]').click()
        assert page.locator('[id="'+b+'"]').is_visible()
        page.locator('.preview-nav a[href="#ap-r07h-pm6"]').click()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(ART / 'db-390.png'))
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.screenshot(path=str(ART / 'db-1440.png'))
        assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--navy").trim()') == '#142d4e'
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

result = {'status': 'passed', 'checks': checks, 'explanationLinks': linked_checks, 'switchAndReload': True, 'deepLinksAndHistory': True, 'sameFragmentReopensSection': True, 'nativeDetailsKeyboard': True, 'consoleErrors': errors, 'screenshots': str(ART), 'scope': 'editorial preview only; no app integration or learner testing'}
print(json.dumps(result, ensure_ascii=False, indent=2))
