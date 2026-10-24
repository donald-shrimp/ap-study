"""Synthetic FP-compatible subjects: isolated checkpoints, fields, backup, AI and offline."""
import json,shutil,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from fp2_fixtures import prepare,builder,write
from browser_storage import nav,state,select_target,open_data_management,open_plan_ai,wait_for_async
ART=Path(tempfile.mkdtemp(prefix='hitomon-fp2-flow-'))
def wait_value(pg,case_id,value):
 expected=json.dumps({'id':case_id,'value':value},ensure_ascii=False)
 wait_for_async(pg,"async()=>{const e="+expected+",{createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:'fp2',rootPath:'/'});try{const i=await s.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...i,rootPath:'/',namespaceName:'written',validate:()=>{}});try{return (await w.read()).some(r=>r.payload.caseId===e.id&&r.payload.responses['q1--amount']?.value===e.value);}finally{await w.close();}}finally{await s.close();}}")
def decode_figure(pg):
 pg.locator('[data-action=written-pane][data-pane=body]').click();pg.locator('.written-layout[data-pane=body]').wait_for();pg.locator('.written-body img').wait_for(state='visible');pg.wait_for_function('(()=>{const i=document.querySelector(".written-body img");return i?.complete&&i.naturalWidth>0})()');pg.locator('[data-action=written-pane][data-pane=questions]').click();pg.locator('.written-layout[data-pane=questions]').wait_for()
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
with tempfile.TemporaryDirectory(prefix='fp2-flow-root-') as d:
 root=Path(d);prepare(root);server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/fp2/'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(url);pg.locator('.quick-start').wait_for()
   pg.locator('.study-entrance').first.click();pg.locator('[data-action=submit]').wait_for();assert '現行法令：未確認' in pg.locator('.legal-context').inner_text();pg.locator('[name=answer][value="0"]').check();pg.locator('[data-action=submit]').click();pg.locator('#result-heading').wait_for();assert len(state(pg)['attempts'])==1
   select_target(pg,'jafp-practical','fp2');pg.locator('.study-entry').wait_for();assert 'synthetic-b' not in pg.locator('#main').inner_text();assert '問題を選ぶ · 1問' in pg.locator('#main').inner_text();pg.locator('[data-action=written-start]').first.click();pg.locator('.written-layout').wait_for();pg.locator('input[data-written-key="q1--amount"]').fill('1,490,000');pg.locator('input[data-written-key="q1--ratio"]').fill('0.435');assert '2026-04-01' in pg.locator('.legal-context').inner_text()
   select_target(pg,'kinzai-personal','fp2');pg.locator('.study-entry').wait_for();assert 'synthetic-a' not in pg.locator('#main').inner_text();pg.locator('[data-action=written-start]').first.click();pg.locator('input[data-written-key="q1--amount"]').fill('7');wait_value(pg,'synthetic-b','7');pg.reload();pg.locator('input[data-written-key="q1--amount"]').wait_for();assert pg.locator('input[data-written-key="q1--amount"]').input_value()=='7'
   select_target(pg,'jafp-practical','fp2');pg.locator('.study-entry [data-action=written-resume]').click();pg.locator('input[data-written-key="q1--ratio"]').wait_for();assert pg.locator('input[data-written-key="q1--ratio"]').input_value()=='0.435';assert pg.locator('input[data-written-key="q1--amount"]').input_value()=='1,490,000';decode_figure(pg)
   for n in range(4):
    key='q1--b'+str(n);pg.locator(f'input[data-written-key="{key}"][value=true]').check();pg.locator(f'[data-action=written-submit][data-written-key="{key}"]').click();pg.locator(f'section.written-field[data-written-key="{key}"] fieldset[disabled]').wait_for()
   for key in ['q1--amount','q1--ratio']:pg.locator(f'[data-action=written-submit][data-written-key="{key}"]').click();pg.locator(f'section.written-field[data-written-key="{key}"] input[readonly]').wait_for()
   pg.locator('[data-action=written-answer][data-written-key="q1--amount"]').click();pg.locator('[data-action=written-ai][data-written-key="q1--amount"]').click();pg.locator('#ai-handoff-dialog').wait_for(state='visible');prompt=pg.locator('#ai-handoff-preview').input_value();assert '円' in prompt and '1490000' in prompt and '2026-04-01' in prompt and 'synthetic-b' not in prompt;pg.locator('#ai-handoff-close').click()
   nav(pg,'history');assert '1問に取り組んだ' in pg.locator('#main').inner_text();assert 'synthetic-b' not in pg.locator('#main').inner_text();assert '6欄中6欄正解' in pg.locator('#main').inner_text()
   select_target(pg,'kinzai-personal','fp2');pg.locator('.study-entry [data-action=written-resume]').click();pg.locator('input[data-written-key="q1--amount"]').wait_for();assert pg.locator('input[data-written-key="q1--amount"]').input_value()=='7';pg.locator('[data-action=written-submit]').click();pg.locator('input[readonly]').wait_for();nav(pg,'history');assert 'synthetic-a' not in pg.locator('#main').inner_text()
   pg.locator('[data-view=planning]').first.click();open_plan_ai(pg)
   with pg.expect_download() as event:pg.locator('[data-action=export-summary]').click()
   path=ART/'summary.json';event.value.save_as(str(path));summary=json.loads(path.read_text());parts={p['examPartId']:p for p in summary['learningByPart']};assert parts['jafp-practical']['completedCases']==1 and parts['kinzai-personal']['completedCases']==1
   open_data_management(pg)
   with pg.expect_download() as event:pg.locator('#export-state').click()
   path=ART/'backup.json';event.value.save_as(str(path));backup=json.loads(path.read_text());assert len(backup['writtenBackup']['runs'])==2 and len(backup['records'])==1;assert all(r['material']['sourceRecord']['legalAsOf']=='2026-04-01' for r in backup['writtenBackup']['runs']);pg.get_by_role('button',name='設定を閉じる').click()
   select_target(pg,'jafp-practical','fp2');nav(pg,'home');pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();pg.locator('[data-offline-select=all]').click();pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for();pg.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.study-entry').wait_for();pg.locator('[data-action=written-start]').first.click();pg.locator('.written-layout').wait_for();decode_figure(pg);pg.locator('input[data-written-key="q1--amount"]').fill('１４９００００');wait_value(pg,'synthetic-a','１４９００００');pg.reload();pg.locator('input[data-written-key="q1--amount"]').wait_for();assert pg.locator('input[data-written-key="q1--amount"]').input_value()=='１４９００００'
   for width in [320,390,1440]:
    pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert pg.locator('.numeric-answer').first.evaluate('(e)=>{const i=e.querySelector("input").getBoundingClientRect(),u=e.querySelector("span").getBoundingClientRect();return u.x>=i.right&&Math.abs((i.y+i.height/2)-(u.y+u.height/2))<5;}')
   pg.screenshot(path=str(ART/'numeric-offline.png'),full_page=True);assert not errors,errors
   fresh=b.new_context(viewport={'width':390,'height':844});other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(url);other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(path));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();other.get_by_role('button',name='設定を閉じる').click();select_target(other,'jafp-practical','fp2');nav(other,'history');assert 'synthetic-a' in other.locator('#main').inner_text() and 'synthetic-b' not in other.locator('#main').inner_text();select_target(other,'kinzai-personal','fp2');nav(other,'history');assert 'synthetic-b' in other.locator('#main').inner_text() and 'synthetic-a' not in other.locator('#main').inner_text()
   write(root/'content/fp2/questions.json',[]);write(root/'content/fp2/question-reviews.json',[]);builder.build(root);only=b.new_context();pg2=only.new_page();pg2.goto(url);pg2.locator('.study-entry').wait_for();assert pg2.locator('#qualification-switch').get_attribute('data-part-id')=='jafp-practical';pg2.locator('#qualification-switch').click();pg2.get_by_role('heading',name='資格・科目を選ぶ',exact=True).wait_for();assert pg2.locator('.qualification-option').count()==2;assert pg2.locator('.qualification-option[data-part-id=objective]').count()==0;b.close()
 finally:server.shutdown()
print('PASS synthetic FP subjects / 4 boolean fields count as 1 question / numeric unit and input / law context / checkpoints and history isolated / shared summary and full backup import / AI / offline figures and input / case-only entry / 320,390,1440')
print('Artifacts:',ART)
