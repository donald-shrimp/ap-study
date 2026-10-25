"""Recommended/topic/session queues on real FP and AP cases, isolated guest data."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import nav,open_data_management
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-case-navigation-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
banks={'fp2':json.loads((ROOT/'content/fp2/practical-cases.json').read_text()),'ap':json.loads((ROOT/'content/ap/written-cases.json').read_text())}
READ='''async q=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:q,rootPath:root.pathname});try{const i=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),w=createWorkspaceStore({...i,rootPath:root.pathname,namespaceName:'written',validate:(k,p)=>p});try{return (await w.read()).map(r=>r.payload);}finally{await w.close();}}finally{await s.close();}}'''
def rows(pg,q='fp2'):return pg.evaluate(READ,q)
def current(pg,q='fp2'):
 rs=rows(pg,q);active=pg.evaluate('''q=>{const suffix=':'+q+':written-view'+(q==='fp2'?':jafp-practical':'');const key=Object.keys(localStorage).find(k=>k.endsWith(suffix));return JSON.parse(localStorage.getItem(key)).currentId;}''',q);return next(r for r in rs if r['id']==active)
def complete(pg,c):
 for item in c['items']:
  pg.locator(f'.written-item-nav [data-action=written-item][data-id="{item["id"]}"]').click()
  for f in item['fields']:
   field=pg.locator(f'.written-field[data-written-key="{item["id"]}--{f["id"]}"]')
   if f['type']=='singleChoice':field.locator('input[value="'+next(a['id'] for a in f['choices'] if a['label']==f['referenceAnswers'][0])+'"]').check()
   else:field.locator('input' if f['type']=='numeric' else 'textarea').fill(f['referenceAnswers'][0])
   field.locator('[data-action=written-submit]').click()
 # In exam mode all responses must be submitted before opening any answer.
 for item in c['items']:
  pg.locator(f'.written-item-nav [data-action=written-item][data-id="{item["id"]}"]').click()
  for f in item['fields']:
   field=pg.locator(f'.written-field[data-written-key="{item["id"]}--{f["id"]}"]')
   field.locator('[data-action=written-answer]').click();field.locator('.written-answer').wait_for()
   if field.locator('[data-action=written-rate]').count():field.locator('[data-action=written-rate][data-outcome=meets]').click()
 pg.locator('[data-action=written-next]').wait_for()
def pack(pg,pack_id):
 nav(pg,'home');pg.locator('[data-action=written-packs]').click();pg.locator('[data-action=written-pack][data-pack="'+pack_id+'"]').click()
def widths(pg,name):
 for width in [320,390,1440]:
  pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,width)
 pg.screenshot(path=str(ART/(name+'.png')),full_page=True);pg.set_viewport_size({'width':390,'height':844})
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto(BASE+'fp2/?part=jafp-practical&entry=home');pg.locator('.quick-start').wait_for();assert pg.locator('.written-case-option').count()==0;assert 'ランダム' not in pg.locator('#main').inner_text();widths(pg,'fp-home')
  pack(pg,'202605');assert pg.locator('.written-case-option').count()==40;widths(pg,'fp-pack');pg.locator('[data-action=written-sequence]').click();pg.locator('.written-layout').wait_for();assert current(pg)['caseId']=='fp2-202605-jafp-q01'
  complete(pg,banks['fp2'][0]);pg.reload();pg.locator('[data-action=written-next]').wait_for();assert '番号順' in pg.locator('.case-study-scope').inner_text();pg.locator('[data-action=written-next]').click();pg.locator('.written-layout').wait_for();assert current(pg)['caseId']=='fp2-202605-jafp-q02'
  nav(pg,'home');pg.locator('.quick-start [data-action=written-start]').click();pg.locator('.written-layout').wait_for();assert current(pg)['caseId']!='fp2-202605-jafp-q02';assert len([r for r in rows(pg) if r['caseId']=='fp2-202605-jafp-q02'])==1
  nav(pg,'topics');assert pg.locator('.case-topic').count()==6;widths(pg,'fp-topics');pg.locator('[data-action=written-recommend][data-topic=financial-assets]').click();pg.locator('.written-layout').wait_for();c=next(c for c in banks['fp2'] if c['id']==current(pg)['caseId']);assert c['topicId']=='financial-assets';complete(pg,c);pg.locator('[data-action=written-next]').click();pg.locator('.written-layout').wait_for();assert current(pg)['material']['topicId']=='financial-assets'
  nav(pg,'home');pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller');pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();ctx.set_offline(True)
  pack(pg,'202605');pg.locator('[data-action=written-sequence]').click();pg.locator('.written-layout').wait_for();complete(pg,banks['fp2'][0]);pg.locator('[data-action=written-next]').click();pg.locator('.written-layout').wait_for();assert current(pg)['caseId']=='fp2-202605-jafp-q02';pg.reload();pg.locator('.written-layout').wait_for();assert '番号順' in pg.locator('.case-study-scope').inner_text();ctx.set_offline(False)
  open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-navigation-backup.json';event.value.save_as(str(backup));saved=json.loads(backup.read_text());assert saved['writtenBackup']['studyContexts'];assert saved['records']==[]
  fresh=b.new_context(viewport={'width':390,'height':844});other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(BASE+'fp2/?part=jafp-practical&entry=home');other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();other.get_by_role('button',name='設定を閉じる',exact=True).click();other.locator('.quick-start [data-action=written-resume]').click();other.locator('.written-layout').wait_for();assert '番号順' in other.locator('.case-study-scope').inner_text();fresh.close()
  ap=b.new_context(viewport={'width':1440,'height':1000});page=ap.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(BASE+'ap/?part=written&entry=home');page.locator('.quick-start').wait_for();page.locator('[data-action=written-packs]').click();assert page.locator('.case-pack-card').count()==8;page.locator('[data-action=written-pack][data-pack="2025-spring"]').click();assert page.locator('.written-case-option').count()==11;page.locator('[name=written-study-mode]').select_option('exam');page.locator('[data-action=written-sequence]').click();page.locator('.written-layout').wait_for();run=current(page,'ap');assert run['caseId']=='ap-r07h-pm1' and run['mode']=='exam';complete(page,next(c for c in banks['ap'] if c['id']==run['caseId']));page.locator('[data-action=written-next]').click();page.locator('.written-layout').wait_for();assert current(page,'ap')['caseId']=='ap-r07h-pm2';assert '番号順' in page.locator('.case-study-scope').inner_text();page.reload();page.locator('.written-layout').wait_for();assert current(page,'ap')['caseId']=='ap-r07h-pm2';assert not errors,errors
  b.close()
finally:server.shutdown()
print('PASS recommended/topic/pack queues / numeric order / whole AP cases / offline / resume / backup / responsive / no JS errors');print('Artifacts:',ART)
