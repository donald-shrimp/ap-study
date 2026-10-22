"""Real UI: download unseen material, offline questions/choice figures/B answers, deletion."""
import json,os,shutil,threading,tempfile
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import state,nav,select_target,wait_for_async
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-offline-materials-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=s.serve_forever,daemon=True).start();BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{s.server_port}/ap-study/')
def open_manager(pg):
 pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();return pg.locator('#offline-dialog')
def save(pg,id):
 d=open_manager(pg);d.locator('[data-offline-select=none]').click();d.locator(f'[data-offline-group="{id}"]').check();d.locator('[data-offline-save]').click();d.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);return d
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**options)
  for id in ['ap','ab730']:
   ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));requests=[];pg.on('request',lambda r:requests.append(r.url));pg.goto(BASE+id+'/');pg.locator('.quick-start').wait_for();pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller');assert not any('/offline.' in u for u in requests)
   before=state(pg);group='pack-r07h-objective' if id=='ap' else 'pack-supplied-1-objective';d=save(pg,group);assert state(pg)==before
   assert '保存済み' in d.locator(f'[data-offline-row="{group}"]').inner_text();assert not pg.evaluate('''async()=>{const names=await caches.keys();for(const n of names){const c=await caches.open(n);if((await c.keys()).some(r=>r.url.includes('/assets/questions/')))return true}return false}''')
   for width in [320,390,1440]:pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth');assert d.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
   pg.set_viewport_size({'width':390,'height':844});pg.screenshot(path=str(ART/(id+'-saved.png')),full_page=True);d.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
   qid='r07h-q5' if id=='ap' else None;m=json.load(open(ROOT/'data/qualifications'/id/'manifest.json'));qs=json.load(open(ROOT/'data/qualifications'/id/m['packs'][0]['url']));q=next(q for q in qs if q['id']==qid) if qid else next(q for q in qs if q['type']=='singleChoice');qid=q['id']
   nav(pg,'materials');pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{qid}"]').click();pg.locator('[data-action=submit]').wait_for()
   if id=='ap':pg.locator('.question-figure img').evaluate('(i)=>i.decode()');pg.locator('.original-question summary').click();pg.locator('.original-content').filter(has_text='オンライン').wait_for();assert pg.locator('.original-content img').count()==0
   for c in q.get('correctChoiceIds') or [q['correctChoiceId']]:pg.locator(f'.choice:has([name=answer][value="{next(i for i,x in enumerate(q["choices"]) if x["id"]==c)}"])').click()
   pg.locator('[data-action=submit]').click();pg.locator('#result-heading').wait_for();assert len(state(pg)['attempts'])==1
   nav(pg,'home');d=open_manager(pg);d.locator(f'[data-offline-remove="{group}"]').click();d.locator('#offline-message').filter(has_text='削除しました').wait_for();d.locator(f'[data-offline-row="{group}"] .offline-status').filter(has_text='未保存').wait_for();assert len(state(pg)['attempts'])==1;d.locator('[data-offline-close]').click();assert not errors,errors
   print('PASS',id,'unseen offline question/figures/answer, originals excluded, 320/390/1440, delete retains records',flush=True)
   # Save the complete qualification, then exercise a never-opened late pack.
   ctx.set_offline(False);pg.reload();pg.locator('.quick-start').wait_for();d=open_manager(pg);d.locator('[data-offline-select=all]').click();d.locator('[data-offline-save]').click();d.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=90000);assert len(state(pg)['attempts'])==1;d.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
   allqs=[q for pack in m['packs'] for q in json.load(open(ROOT/'data/qualifications'/id/pack['url']))];q=next(q for q in allqs if not q.get('stem')) if id=='ap' else next(q for q in reversed(allqs) if q['type']=='singleChoice')
   nav(pg,'materials');pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{q["id"]}"]').click();pg.locator('[data-action=submit]').wait_for()
   if id=='ap':pg.locator('.source-question img').first.evaluate('(i)=>i.decode()');assert pg.locator('.choices input').count()==4
   assert not errors,errors;print('PASS complete',id,'download / unseen late pack or image-only question / no study records from download',flush=True);ctx.close()
  # B uses a shared text bank but requires every selected session's figure.
  ctx=b.new_context(viewport={'width':1440,'height':900});pg=ctx.new_page();pg.goto(BASE+'ap/');pg.locator('.quick-start').wait_for();select_target(pg,'written');pg.locator('.study-entry').wait_for();pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller');before=state(pg);d=save(pg,'cases-ap-r07h-pm1');assert state(pg)==before;d.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.study-entry').wait_for()
  assert pg.locator('[data-action=written-start][data-id=ap-r07a-pm1]').first.is_disabled();pg.locator('[data-action=written-start][data-id=ap-r07h-pm1]').first.click();pg.locator('.written-layout').wait_for();pg.locator('.written-body .question-figure img').first.evaluate('(i)=>i.decode()');pg.locator('textarea[data-written-key]').first.fill('オフライン回答');pg.locator('[data-action=written-submit]').first.click();pg.locator('[data-action=written-answer]').first.click();pg.locator('.written-answer').wait_for();pg.locator('[data-action=written-rate][data-outcome=unsure]').first.click();pg.reload();pg.locator('textarea[data-written-key]').first.wait_for();assert pg.locator('textarea[data-written-key]').first.input_value()=='オフライン回答';pg.screenshot(path=str(ART/'written-offline.png'),full_page=True);print('PASS B required figures and shared bank / unsaved case disabled / free text, example, self rating and reload',flush=True);ctx.close();b.close()
finally:s.shutdown()
print('Artifacts:',ART)
