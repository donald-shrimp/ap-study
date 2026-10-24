"""Keep an editing numeric field and its caret across offline/online transitions."""
import shutil,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from fp2_fixtures import prepare
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with tempfile.TemporaryDirectory(prefix='fp2-focus-') as d:
 prepare(Path(d));server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/fp2/?part=jafp-practical');page.locator('.study-entry').wait_for();page.locator('[data-action=written-start]').first.click();field=page.locator('input[data-written-key="q1--amount"]');field.fill('1,490,000');field.evaluate('(e)=>{e.setSelectionRange(2,5);window.__editingNumeric=e;}')
   for offline in [True,False]:
    context.set_offline(offline);page.wait_for_function('(online)=>navigator.onLine===online',arg=not offline)
    # Observe the asynchronous connection handler after its cache checks finish.
    page.wait_for_timeout(300)
    assert field.evaluate('(e)=>e===window.__editingNumeric&&e.isConnected&&document.activeElement===e&&e.selectionStart===2&&e.selectionEnd===5&&e.value==="1,490,000"'),'Connection change replaced or blurred numeric input'
   page.locator('[data-action=written-submit][data-written-key="q1--amount"]').click();page.locator('input[data-written-key="q1--amount"][readonly]').wait_for();assert '自動判定：正解' in page.locator('section.written-field[data-written-key="q1--amount"]').inner_text();assert not errors,errors;browser.close()
 finally:server.shutdown()
print('PASS numeric input node, focus, caret and value retained offline and online / submit still renders locked answer and result')
