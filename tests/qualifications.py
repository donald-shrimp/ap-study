from browser_storage import nav as action_nav, open_plan_editor, open_plan_ai
"""Real shared UI with two synthetic qualifications; fixtures are never published."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_storage import wait_for_async

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT/'tools/build-content.py')
builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
spec = importlib.util.spec_from_file_location('fixtures', ROOT/'tests/content.py')
fixtures = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        if "If-Modified-Since" in self.headers: del self.headers["If-Modified-Since"]
        super().do_GET()

with tempfile.TemporaryDirectory(prefix='hitomon-qualifications-') as directory:
    root = Path(directory)/'ap-study'; root.mkdir()
    for name in ['src','assets/icons','assets/vendor','templates','schemas']:
        shutil.copytree(ROOT/name,root/name)
    for name in ['app.js','styles.css','pwa.js','sw.js','manifest.webmanifest']:
        shutil.copy(ROOT/name,root/name)
    code_before = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*.js')}
    (root/'content').mkdir()
    (root/'content/qualifications.json').write_text(json.dumps({'qualifications':['fixture-a','fixture-b']}))
    for id,count in [('fixture-a',2),('fixture-b',5)]:
        path=root/'content'/id;path.mkdir()
        config={'id':id,'name':id,'shortName':id,'questionSource':f'content/{id}/questions.json','topics':[{'id':'basic','name':'基礎'}],'sourceLabel':'検証用','sourceDoc':'docs/SOURCES.md','sourceDescription':'公開しない検証用の独自問題'}
        question=fixtures.fixture(count)
        if count==5:
            question['hints']=[{'title':f'操作{i+1}','text':'2から1ずつ増やして数える。','revealsAnswer':False} for i in range(3)]+[{'title':'答え','text':'2＋3＝5です。','revealsAnswer':True}]
        (path/'qualification.json').write_text(json.dumps(config));(path/'questions.json').write_text(json.dumps([question]))
    builder.build(root)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=directory));threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/ap-study/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
            page.goto(url);page.get_by_role('heading',name='資格を選ぶ').wait_for()
            assert page.locator('#main a').count()==2
            page.locator('.brand').click();assert page.get_by_role('heading',name='資格を選ぶ').is_visible()
            page.get_by_role('link',name='fixture-a · 1問').click();page.locator('.quick-start').wait_for()
            assert not any('/packs/' in r for r in requests)
            page.locator('.sidebar [data-view=topics]').click();page.locator('.reading-note summary').click();page.locator('[data-reading-topic]').fill('第1章')
            page.locator('[data-action=topic-session]').click();page.get_by_role('radio').last.wait_for()
            assert page.get_by_role('radio').count()==2
            assert any('/fixture-a/packs/' in r for r in requests) and not any('/fixture-b/packs/' in r for r in requests)
            page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').last.check();page.get_by_role('button',name='回答する',exact=True).click()
            assert page.locator('#result-heading').inner_text()=='ヒントで正解'
            page.goto(url+'fixture-b/');page.locator('.quick-start').wait_for();page.locator('.sidebar [data-view=history]').click();assert '解答済み 0 / 1問' in page.locator('.progress-counts').inner_text()
            page.locator('.sidebar [data-view=home]').click();page.locator('.quick-start [data-action=start-session]').click();page.get_by_role('radio').last.wait_for();assert page.get_by_role('radio').count()==5
            for i in range(4):page.locator('[data-action=hint]').click();assert page.locator('.hint-box').count()==i+1
            page.get_by_role('radio').last.check();page.get_by_role('button',name='回答する',exact=True).click()
            assert page.locator('#result-heading').inner_text()=='解答を確認' and page.locator('.reason-list li').count()==5
            page.locator('.sidebar [data-view=home]').click()
            page.goto(url+'fixture-a/');page.locator('#result-heading').wait_for();assert page.locator('#result-heading').inner_text()=='ヒントで正解'
            # Add a second one-question pack without touching application code.
            path=root/'content/fixture-a/questions.json';old=fixtures.fixture(2);new=fixtures.fixture(2,'constructor','extra')
            path.write_text(json.dumps([old,new]));builder.build(root)
            page.reload();page.locator('#result-heading').wait_for();page.locator('.sidebar [data-view=home]').click();page.locator('.sidebar [data-view=history]').click();assert '解答済み 1 / 2問' in page.locator('.progress-counts').inner_text()
            # Change and then retire the question. The original answer stays graded
            # against its snapshot and remains readable after removal from the catalog.
            old['stem']='2＋2は幾つですか。';old['version']=2;old['correctChoiceId']='c0';old['summary']='2＋2＝4'
            cfg_path=root/'content/fixture-a/qualification.json';cfg=json.loads(cfg_path.read_text());cfg['topics'][0]['name']='改名した基礎';cfg_path.write_text(json.dumps(cfg))
            path.write_text(json.dumps([old,new]));builder.build(root);page.reload();page.locator('.sidebar [data-view=history]').click();page.locator('[data-action=resume]').click()
            assert '2＋3' in page.locator('.question-stem').inner_text() and '正解：2' in ''.join(page.locator('.answer-selection').inner_text().split())
            page.locator('.sidebar [data-view=topics]').click();page.locator('.reading-note summary').click();assert page.locator('[data-reading-topic]').input_value()=='第1章'
            action_nav(page,'materials');page.locator('[data-action=edit][data-id="same-question"]').click();page.locator('#editor-dialog').wait_for();page.locator('[name=summary]').fill('個人の解説');page.get_by_role('button',name='編集を保存する',exact=True).click()
            page.locator('.sidebar [data-view=home]').click();path.write_text(json.dumps([new]));builder.build(root)
            page.reload();page.locator('.quick-start').wait_for();page.locator('.sidebar [data-view=history]').click();assert '解答済み 0 / 1問' in page.locator('.progress-counts').inner_text()
            page.locator('.sidebar [data-view=history]').click();assert page.locator('[data-action=start]').count()==0
            page.locator('[data-action=resume]').click();assert page.locator('#result-heading').inner_text()=='ヒントで正解'
            page.locator('[data-action=next]').click();page.get_by_role('radio').last.wait_for();page.get_by_role('radio').last.check();page.get_by_role('button',name='回答する',exact=True).click();assert page.locator('#result-heading').inner_text()=='自力で正解'
            assert code_before=={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.js')}
            page.evaluate('document.documentElement.style.zoom="200%"');assert page.locator('.study-back-button').bounding_box()['height']>=44
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            page.evaluate('document.documentElement.style.zoom=""')
            page.evaluate('navigator.serviceWorker.ready.then(()=>true)');page.wait_for_function('!!navigator.serviceWorker.controller')
            context.set_offline(True);page.reload();page.locator('#result-heading').wait_for();assert page.locator('html').get_attribute('data-qualification')=='fixture-a'
            assert not errors,errors
            # First direct qualification visit, with no earlier reload/cache.
            fresh=browser.new_context();direct=fresh.new_page();direct.goto(url+'fixture-b/');direct.locator('.quick-start').wait_for()
            direct.locator('.quick-start [data-action=start-session]').click();direct.get_by_role('radio').last.wait_for()
            direct.evaluate('navigator.serviceWorker.ready.then(()=>true)');direct.wait_for_function('!!navigator.serviceWorker.controller')
            wait_for_async(direct,'async()=>!!(await caches.match(new URL("index.html",location.href)))')
            fresh.set_offline(True);direct.reload();direct.get_by_role('radio').last.wait_for();assert direct.get_by_role('radio').count()==5
            fresh.close()
            browser.close()
        print('PASS two qualification pages / lazy packs / duplicate IDs / 2 and 5 choices / variable hints / immutable retired history and personal notes / topic rename / 200% mobile / qualified offline page')
    finally:server.shutdown()
