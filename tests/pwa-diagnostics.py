"""Check opt-in device diagnostics, failed downloads, and record privacy."""
import functools, json, os, shutil, tempfile, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state as stored_state

ROOT = Path(__file__).resolve().parents[1]
KEY = 'ap-study-mock.v1'
ARTIFACTS = Path(tempfile.mkdtemp(prefix='pwa-check-'))
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT.parent)))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = os.environ.get('AP_STUDY_PWA_URL', f'http://127.0.0.1:{server.server_port}/ap-study/')
with sync_playwright() as p:
    options = {'executable_path': shutil.which('chromium'), 'headless': True, 'args': ['--no-sandbox']}
    if URL.startswith('https://') and os.environ.get('HTTPS_PROXY'):
        options['proxy'] = {'server': os.environ['HTTPS_PROXY'], 'bypass': 'localhost,127.0.0.1'}
    context = p.chromium.launch_persistent_context(str(ARTIFACTS / 'profile'), **options,
                                                viewport={'width': 390, 'height': 844})
    page = context.new_page(); errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL); page.locator('.quick-start').wait_for()
    assert page.locator('#pwa-diagnostics').count() == 0
    # Include private content to detect accidental leakage, not just an empty default state.
    page.locator('.sidebar [data-view=topics]').click()
    note = page.locator('[data-reading-topic]').first
    note.evaluate('(input)=>input.closest("details").open=true')
    note.fill('PRIVATE-STUDY-NOTE-12345')
    original = stored_state(page)
    page.goto(URL + '?pwa-check=1'); page.locator('#pwa-diagnostics').wait_for()
    page.wait_for_function('(()=>{try{return JSON.parse(document.querySelector("#pwa-diagnostic-report").value).checksComplete}catch{return false}})()')
    assert page.locator('#settings-dialog').evaluate('(dialog)=>dialog.open')
    report = json.loads(page.locator('#pwa-diagnostic-report').input_value())
    assert report['manifest']['status'] == 200 and not report.get('error'), report
    assert report['manifest']['resolved']['id'].endswith('/ap-study/')
    assert {icon['decodedSize'] for icon in report['icons']} == {'192x192', '512x512'}, report
    assert 'PRIVATE-STUDY-NOTE-12345' not in json.dumps(report)
    assert stored_state(page) == original
    # Exercise the trusted copy action with a stub, so the test does not depend on OS clipboard.
    page.evaluate('Object.defineProperty(navigator,"clipboard",{value:{writeText:async text=>window.copiedReport=text},configurable:true})')
    page.locator('#copy-pwa-diagnostics').click()
    page.wait_for_function('!!window.copiedReport')
    copied = json.loads(page.evaluate('window.copiedReport'))
    assert copied['checksComplete'] and 'promptReceived' in copied['browser']
    assert 'PRIVATE-STUDY-NOTE-12345' not in page.evaluate('window.copiedReport')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    screenshot = ARTIFACTS / 'diagnostic-mobile.png'
    page.screenshot(path=str(screenshot))
    assert not errors, errors
    context.close()
    if not os.environ.get('AP_STUDY_PWA_URL'):
        # Bypass SW for controlled faults in the asset probes.
        browser = p.chromium.launch(**options)
        for fault in ('manifest', 'icon'):
            ctx = browser.new_context(service_workers='block')
            pg = ctx.new_page()
            pattern = '**/manifest.webmanifest*' if fault == 'manifest' else '**/icon-512.png'
            ctx.route(pattern, lambda route: route.fulfill(status=404, body='missing'))
            pg.goto(URL + '?pwa-check=1')
            pg.wait_for_function('(()=>{try{return JSON.parse(document.querySelector("#pwa-diagnostic-report").value).checksComplete}catch{return false}})()')
            report = json.loads(pg.locator('#pwa-diagnostic-report').input_value())
            if fault == 'manifest': assert 'HTTP 404' in report['error'], report
            else: assert any('HTTP 404' in icon.get('error', '') for icon in report['icons']), report
            ctx.close()
        browser.close()
server.shutdown()
print('PASS opt-in diagnostics / manifest and icon decoding / copy / private records unchanged / download failures')
print('Artifacts:', ARTIFACTS)
