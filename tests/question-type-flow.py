"""Private multi-selection UI at phone and desktop widths, including offline saves."""
import json,shutil,tempfile,threading,copy
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from common_fixtures import prepare,builder,write,review
from browser_storage import nav,state
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
READ_RUNS='''async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('hitomon:/:workspace');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});return new Promise((resolve,reject)=>{const r=db.transaction('documents').objectStore('documents').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}'''
def multi(q):
    q=copy.deepcopy(q);q.pop('correctChoiceId');q.update(type='multipleChoice',choices=[{'id':'a','label':'A','text':'1'},{'id':'b','label':'B','text':'2'},{'id':'c','label':'C','text':'3'}],correctChoiceIds=['a','c'],selection={'mode':'exact','count':2},grading={'method':'exactChoiceSet'},stem='奇数を2つ選んでください。',explanation='1と3が奇数です。',choiceReasons=['奇数','偶数','奇数']);return q
with tempfile.TemporaryDirectory() as d:
    root=Path(d);config,normal,extras=prepare(root);normal=[multi(q) for q in normal];extras=[multi(q) for q in extras];path=root/'content/fixture'
    for name,data in [('questions.json',normal),('reviews.json',[review(q) for q in normal]),('assessments.json',extras),('assessment-reviews.json',[review(q) for q in extras])]:write(path/name,data)
    builder.build(root);server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE ERROR:',str(e),flush=True)));page.on('dialog',lambda dialog:dialog.accept())
            page.goto(url);page.locator('.study-entrance').first.click();submit=page.locator('[data-action=submit]');submit.wait_for();assert submit.is_disabled();assert '2つ選' in page.locator('legend').inner_text();assert page.get_by_role('radio').count()==0
            page.get_by_role('checkbox').nth(2).check();assert submit.is_disabled();assert state(page)['attempts'][0]['selectedChoiceIds']==['c'];page.reload();page.get_by_role('checkbox').nth(2).wait_for();assert page.get_by_role('checkbox').nth(2).is_checked();page.get_by_role('checkbox').first.check();assert submit.is_enabled();page.get_by_role('checkbox').nth(1).check();assert submit.is_disabled();page.get_by_role('checkbox').nth(1).uncheck()
            for width in [320,390,1280]:page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.set_viewport_size({'width':390,'height':844});submit.click();page.locator('#result-heading').wait_for();assert '自力' in page.locator('#result-heading').inner_text();assert 'A・C' in page.locator('.answer-selection').inner_text();assert state(page)['attempts'][0]['selectedChoiceIds']==['a','c']
            page.locator('[data-action=ask-ai]').click();prompt=page.locator('#ai-handoff-preview').input_value();assert '答えを2つ選' in prompt;assert 'A：1' in prompt and 'C：3' in prompt;page.locator('#ai-handoff-close').click()
            nav(page,'home');page.locator('.home-assessments [data-view=diagnostics]').click();page.get_by_role('button',name='40問の診断をはじめる',exact=True).click();page.get_by_role('checkbox').first.wait_for();assert page.locator('[data-action=hint],[data-action=ask-ai],.result').count()==0
            page.get_by_role('checkbox').nth(2).check();assert page.locator('[data-action=submit-diagnostic]').is_disabled();page.locator('[data-action=pause-diagnostic]').click();run=next(r['payload'] for r in page.evaluate(READ_RUNS) if r['kind']=='diagnostic');assert run['currentChoiceId']==['c'];assert not run['responses'];page.reload();page.locator('.home-assessments [data-action=resume-diagnostic]').click();page.get_by_role('checkbox').nth(2).wait_for();assert page.get_by_role('checkbox').nth(2).is_checked()
            context.set_offline(True);page.reload();page.get_by_role('checkbox').nth(2).wait_for();assert page.get_by_role('checkbox').nth(2).is_checked();page.get_by_role('checkbox').first.check();page.locator('[data-action=submit-diagnostic]').click();page.get_by_text('診断 2 / 40問',exact=True).wait_for();page.locator('[data-action=end-diagnostic]').click();page.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();assert '正解 1' in page.locator('#main').inner_text();assert len(state(page)['attempts'])==1
            context.set_offline(False);nav(page,'home');page.locator('.home-assessments [data-view=mocks]').click();page.locator('[data-action=start-mock]').click();page.get_by_role('checkbox').first.wait_for();page.get_by_role('checkbox').first.check();page.get_by_role('checkbox').nth(1).check();page.locator('[data-action=pause-diagnostic]').click();page.reload();page.locator('.home-assessments [data-view=mocks]').click();page.locator('[data-action=resume-diagnostic]').click();page.get_by_role('checkbox').nth(1).wait_for();assert page.get_by_role('checkbox').nth(1).is_checked();page.locator('[data-action=submit-diagnostic]').click();page.locator('[data-action=end-diagnostic]').click();page.get_by_role('heading',name='テスト模試の結果（部分結果）',exact=True).wait_for();assert '0 / 40問正解' in page.locator('#main').inner_text();page.locator('.diagnostic-review summary').first.click();assert 'A・B' in page.locator('#main').inner_text();assert len(state(page)['attempts'])==1
            assert not errors,errors;browser.close()
    finally:server.shutdown()
print('PASS 320/390/1280 multi selection / exact count and excess guard / answer labels / AI / partial save and reload / offline diagnosis / frozen mock responses and final sets / no assistance or ordinary-record contamination')
