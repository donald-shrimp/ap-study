"""Old installed-PWA catalogs must recover new qualifications/parts on the first visit."""
import json,os,shutil,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import open_written_case, state
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-catalog-refresh-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
LIST=json.loads((ROOT/'data/qualifications/catalog.json').read_text());MANIFEST=json.loads((ROOT/'data/qualifications/fp2/manifest.json').read_text())
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**options)
  for scenario in ['missing-qualification','missing-part','chooser','missing-case-catalog']:
   ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(BASE+'ap/');pg.locator('.quick-start').wait_for();pg.locator('.study-entrance[data-paper-mode=all]').click();pg.locator('.question-panel').wait_for();pg.get_by_role('radio').first.check();before=state(pg)
   pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
   old=json.loads(json.dumps(LIST));manifest=json.loads(json.dumps(MANIFEST))
   if scenario=='missing-case-catalog':manifest['cases'].pop('index')
   else:
    manifest['studyTargets']=manifest['studyTargets'][:1];manifest['cases']['count']=0;manifest['examParts'][1]['practiceAvailable']=False
    if scenario=='missing-qualification':old['qualifications']=[q for q in old['qualifications'] if q['id']!='fp2']
    else:next(q for q in old['qualifications'] if q['id']=='fp2')['studyTargets']=manifest['studyTargets']
   pg.evaluate('''async({base,old,manifest})=>{const root=new URL(base),cache=await caches.open(`hitomon-${root.pathname}content`);for(const[path,value]of [['data/qualifications/catalog.json',old],['data/qualifications/fp2/manifest.json',manifest]])await cache.put(new URL(path,root),new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}}));}''',{'base':BASE,'old':old,'manifest':manifest})
   path='?qualifications&qualification=fp2&part=jafp-practical' if scenario=='chooser' else 'fp2/?part=jafp-practical&entry=home'
   pg.goto(BASE+path)
   if scenario=='chooser':pg.locator('.qualification-option[data-qualification-id=fp2][data-part-id=jafp-practical]').click()
   pg.locator('.study-entry').wait_for();assert pg.locator('.quick-start').count()==1;assert pg.locator('#qualification-switch').get_attribute('data-part-id')=='jafp-practical';assert pg.locator('#main h1').filter(has_text='読み込めません').count()==0
   if scenario=='missing-case-catalog':
    pg.locator('[data-action=written-packs]').click();pg.locator('.case-pack-card').wait_for();assert '2026年5月公表' in pg.locator('.case-pack-card').inner_text()
   open_written_case(pg,'fp2-202605-jafp-q04');pg.locator('input[data-written-key="item1--yield"]').fill('0.435');pg.reload();pg.locator('input[data-written-key="item1--yield"]').wait_for();assert pg.locator('input[data-written-key="item1--yield"]').input_value()=='0.435'
   pg.screenshot(path=str(ART/(scenario+'.png')))
   pg.goto(BASE+'ap/');pg.locator('.question-panel').wait_for();assert state(pg)['currentId']==before['currentId'];assert pg.get_by_role('radio').first.is_checked();assert state(pg)['attempts']==before['attempts'];assert not errors,errors
   print('PASS first visit from stale cache:',scenario,'/ AP answers preserved / FP numeric checkpoint',flush=True);ctx.close()
  # Even a genuine startup failure must leave the PWA update controls reachable.
  ctx=b.new_context();pg=ctx.new_page();pg.goto(BASE+'?qualification=not-published');pg.get_by_role('heading',name='ひと問を読み込めませんでした。',exact=True).wait_for();pg.locator('#settings-button').click();assert pg.locator('#settings-dialog').evaluate('(d)=>d.open');ctx.close()
  print('PASS settings remain reachable after an unavailable qualification',flush=True)
  b.close()
finally:server.shutdown()
print('Artifacts:',ART)
