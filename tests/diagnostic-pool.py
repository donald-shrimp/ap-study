"""Real UI with a synthetic, reviewed diagnostic bank; never published."""
import json,shutil,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from diagnostic_fixtures import prepare

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if 'If-Modified-Since' in self.headers:del self.headers['If-Modified-Since']
  super().do_GET()

READ='''async()=>{
 const {createLocalStore}=await import('/src/storage/local.js');const study=createLocalStore({qualificationId:'fixture',rootPath:'/'});
 try{const identity=await study.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return {study:JSON.parse(await study.snapshot()),documents:await workspace.read()};}finally{await workspace.close();}}finally{await study.close();}
}'''
with tempfile.TemporaryDirectory(prefix='hitomon-diagnostic-pool-') as directory:
 root=Path(directory);prepare(root)
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=directory));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write']);page=context.new_page();errors=[];requests=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.on('dialog',lambda d:d.accept())
   page.goto(f'http://127.0.0.1:{server.server_port}/');page.get_by_role('button',name='とりあえずはじめる',exact=True).wait_for();assert not any('/data/qualifications/fixture/diagnostic.' in url for url in requests)
   page.get_by_role('button',name='とりあえずはじめる',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for();assert not page.evaluate(READ)['study']['attempts'][0]['questionSnapshot'].get('diagnosticOnly');page.get_by_role('button',name='中断',exact=True).click()
   page.get_by_role('button',name='実力診断（30問）',exact=True).click();page.get_by_role('button',name='30問の診断をはじめる',exact=True).click();page.locator('[name=diagnostic-answer]').first.wait_for()
   run=next(r['payload'] for r in page.evaluate(READ)['documents'] if r['kind']=='diagnostic');assert sum(s['kind']=='derived' for s in run['slots'])==3;assert len({s['parentQuestionId'] or s['attempt']['questionId'] for s in run['slots']})==30
   assert any('/data/qualifications/fixture/diagnostic.' in url for url in requests)
   for i in range(30):
    slot=run['slots'][i];q=slot['attempt']['questionSnapshot'];assert page.locator('.hint-section,.result,.correct-choice').count()==0
    choice='wrong' if slot['kind']=='derived' else 'right';page.locator(f'[name=diagnostic-answer][value="{choice}"]').check()
    page.get_by_role('button',name='回答して結果へ' if i==29 else '回答して次へ',exact=True).click()
    if i<29:page.get_by_text(f'診断 {i+2} / 30問',exact=True).wait_for()
    if i==1:
     page.get_by_role('button',name='中断',exact=True).click();page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener("controllerchange",r,{once:true}));}')
     context.set_offline(True);page.reload();page.get_by_role('button',name='診断の続きから',exact=True).click();page.get_by_text('診断 3 / 30問',exact=True).wait_for()
   page.get_by_role('heading',name='診断結果',exact=True).wait_for();page.get_by_text('出題構成を確認',exact=True).click();assert '派生問題：3問出題・3問回答・0問正解' in page.locator('#main').inner_text()
   derived=page.locator('.diagnostic-review').filter(has=page.locator('button').filter(has_text='元の過去問を学習'));derived.first.locator('summary').click();assert derived.first.locator('.reason-list li').count()==2
   page.get_by_role('button',name='結果と学習状況をAIへ渡す',exact=True).click();page.get_by_role('button',name='学習状況JSONをコピー',exact=True).click();page.get_by_text('コピーしました。',exact=True).wait_for();summary=json.loads(page.evaluate('navigator.clipboard.readText()'));assert summary['learning']['all']['completedAttempts']==27 and summary['diagnostics'][0]['answered']==30
   page.locator('.sidebar [data-view=review]').click();assert not page.locator('[data-action=start][data-id^=v]').count();assert 'もう一度解く問題はありません' in page.locator('#main').inner_text() or page.locator('[data-action=start]').count()==0
   page.locator('.sidebar [data-view=history]').click();assert not page.locator('[data-action=resume][data-id^=v]').count()
   page.locator('.sidebar [data-view=materials]').click();assert '診断専用検証' not in page.locator('#main').inner_text()
   context.set_offline(False);page.locator('.sidebar [data-view=home]').click();page.get_by_role('button',name='診断結果を見る',exact=True).click();page.get_by_role('button',name='結果を見る',exact=True).click();derived=page.locator('.diagnostic-review').filter(has=page.locator('button').filter(has_text='元の過去問を学習'));derived.first.locator('summary').click();derived.first.get_by_role('button',name='元の過去問を学習',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for();data=page.evaluate(READ);assert not data['study']['attempts'][-1]['questionSnapshot'].get('diagnosticOnly')
   # A damaged bank must fail diagnosis explicitly, never silently replace its
   # questions with originals or prevent immediate ordinary study.
   damaged=browser.new_context(service_workers='block');broken=damaged.new_page();broken.route('**/data/qualifications/fixture/diagnostic.*.json',lambda route:route.fulfill(status=200,content_type='application/json',body='[]'))
   broken.goto(f'http://127.0.0.1:{server.server_port}/');broken.get_by_role('button',name='実力診断（30問）',exact=True).click();broken.get_by_role('button',name='30問の診断をはじめる',exact=True).click();broken.get_by_text('教材の確認に失敗しました',exact=False).wait_for();assert not broken.evaluate(READ)['documents']
   broken.locator('.sidebar [data-view=home]').click();broken.get_by_role('button',name='とりあえずはじめる',exact=True).click();broken.get_by_role('button',name='回答する',exact=True).wait_for();damaged.close()
   assert not errors,errors;browser.close()
 finally:server.shutdown();server.server_close()
print('PASS diagnostic-only bank lazy load / 3 variants balanced with originals / family uniqueness / 30 unaided answers / offline frozen resume / result provenance / external export / no ordinary study, review or search contamination / return to original')
