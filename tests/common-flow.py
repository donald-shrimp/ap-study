"""Shared UI with parentless 40-question assessments; no real exam added."""
import json,shutil,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from common_fixtures import prepare,builder,write
from browser_storage import nav,state
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
READ_RUNS='''async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('hitomon:/:workspace');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});return new Promise((resolve,reject)=>{const r=db.transaction('documents').objectStore('documents').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}'''
with tempfile.TemporaryDirectory(prefix='hitomon-common-flow-') as d:
    root=Path(d);config,normal,extras=prepare(root)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda dialog:dialog.accept())
            page.goto(url);page.locator('.study-entrance').first.click();page.locator('[data-action=submit]').wait_for();assert page.locator('[data-action=hint]').count()==0
            page.get_by_role('radio').last.check();page.locator('[data-action=submit]').click();page.locator('#result-heading').wait_for();assert '自力' in page.locator('#result-heading').inner_text();assert page.locator('.takeaway').count()==0
            page.locator('[data-action=ask-ai]').click();prompt=page.locator('#ai-handoff-preview').input_value();assert 'テスト第1版' in prompt and '加算' in prompt and 'https://example.com/learning' in prompt;page.locator('#ai-handoff-close').click()
            page.reload();page.locator('#result-heading').wait_for();ordinary=state(page)['attempts'];assert len(ordinary)==1
            nav(page,'home');assert '40問' in page.locator('.home-assessments [data-view=mocks]').inner_text();page.locator('.home-assessments [data-view=diagnostics]').click();page.get_by_role('button',name='40問の診断をはじめる',exact=True).click();page.locator('[name=diagnostic-answer]').first.wait_for()
            assert page.locator('[data-action=hint],[data-action=ask-ai],.hint-section,.result').count()==0
            page.get_by_role('radio').last.check();page.locator('[data-action=submit-diagnostic]').click();page.get_by_text('診断 2 / 40問',exact=True).wait_for();page.locator('[name=diagnostic-answer]').last.check();page.locator('[data-action=pause-diagnostic]').click()
            rows=page.evaluate(READ_RUNS);run=next(r['payload'] for r in rows if r['kind']=='diagnostic');before=json.dumps(run['slots'],sort_keys=True);assert run['size']==40 and len(run['responses'])==1 and run['currentChoiceId']=='b'
            # Change only the current blueprint; existing runs keep their 40 slots.
            config['diagnosticBlueprint']={'size':60,'sampling':'topic-round-robin'};write(root/'content/fixture/qualification.json',config);builder.build(root)
            page.reload();page.locator('.home-assessments [data-action=resume-diagnostic]').click();page.get_by_role('radio').last.wait_for();assert page.get_by_role('radio').last.is_checked();assert json.dumps(next(r['payload'] for r in page.evaluate(READ_RUNS) if r['kind']=='diagnostic')['slots'],sort_keys=True)==before
            context.set_offline(True);page.reload();page.locator('[name=diagnostic-answer]').last.wait_for();assert page.get_by_role('radio').last.is_checked();page.locator('[data-action=submit-diagnostic]').click();page.locator('[data-action=end-diagnostic]').click();page.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();assert page.locator('[data-action=start]').count()==0, 'Independent dedicated items must not link to an undefined parent';page.locator('summary').filter(has_text='出題の内訳').click();assert '独自問題' in page.locator('#main').inner_text();assert len(state(page)['attempts'])==len(ordinary)
            context.set_offline(False);nav(page,'home');page.locator('.home-assessments [data-view=mocks]').click();assert '固定40問' in page.locator('.mock-set').inner_text();assert '80問' not in page.locator('#main').inner_text();page.locator('[data-action=start-mock]').click();page.get_by_role('radio').last.wait_for();page.get_by_role('radio').last.check();page.locator('[data-action=pause-diagnostic]').click();mock=json.loads((root/'content/fixture/mocks.json').read_text());mock['sets'][0]['size']=20;mock['sets'][0]['slots']=mock['sets'][0]['slots'][:20];mock['sets'][0]['version']=2;write(root/'content/fixture/mocks.json',mock);builder.build(root);page.reload();page.locator('.home-assessments [data-view=mocks]').click();assert '固定20問' in page.locator('.mock-set').inner_text();assert '0 / 40問' in page.locator('.mock-set').inner_text();page.locator('.mock-set [data-action=resume-diagnostic]').click();assert page.get_by_role('radio').last.is_checked();assert page.locator('[data-action=hint],[data-action=ask-ai]').count()==0
            page.locator('[data-action=submit-diagnostic]').click();page.locator('[data-action=end-diagnostic]').click();page.get_by_role('heading',name='テスト模試の結果（部分結果）',exact=True).wait_for();assert '1 / 40問正解' in page.locator('#main').inner_text();assert len(state(page)['attempts'])==len(ordinary)
            mock['sets']=[];write(root/'content/fixture/mocks.json',mock);builder.build(root);page.reload();nav(page,'home');page.locator('.home-assessments [data-view=mocks]').click();page.get_by_role('button',name='結果を見る',exact=True).click();page.get_by_role('heading',name='テスト模試の結果（部分結果）',exact=True).wait_for();assert page.locator('[data-action=start-mock]').count()==0
            for width in [320,390,1280]:page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            nav(page,'home');page.locator('[data-action=cards-open]').click();page.locator('[data-action=card-flip]').click();assert page.locator('.flashcard details').count()==0;page.locator('[data-action=card-rate][data-outcome=recalled]').click();page.reload();page.locator('.flashcard').wait_for()
            assert not errors,errors;browser.close()
    finally:server.shutdown()
print('PASS generic normal question without hints / frozen scope in AI / 40-question diagnosis, policy update and offline resume / independent results without fake-parent links / 40-question fixed mock and saved choice / standalone cards / no ordinary-record contamination / mobile and desktop')
