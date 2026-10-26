"""Real reviewed FP practical corpus: render, grading, offline and saved records."""
import json,os,shutil,threading,tempfile
from pathlib import Path
from urllib.parse import urlparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_storage import open_written_case, open_data_management,select_target,state
ROOT=Path(__file__).resolve().parents[1];scratch=Path(tempfile.mkdtemp(prefix='hitomon-fp2-practical-'))
cases=json.loads((ROOT/'content/fp2/practical-cases.json').read_text())
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();base=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if base.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**options);ctx=b.new_context(viewport={'width':1440,'height':1000});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(base+'fp2/?part=jafp-practical&entry=home');pg.locator('.study-entry').wait_for();assert pg.locator('.quick-start').count()==1
  pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
  for n,c in enumerate(cases,1):
   if n>1:pg.locator('#main .study-toolbar [data-view=home]').click();pg.locator('.study-entry').wait_for()
   open_written_case(pg,c['id']);pg.locator('.written-layout').wait_for()
   assert pg.locator('section.written-field').count()==sum(len(i['fields']) for i in c['items'])
   if c['bodyFigures']:
    pg.wait_for_function('Array.from(document.querySelectorAll(".written-body img")).every(i=>i.complete&&i.naturalWidth>0)')
   for width in [320,390,1440]:
    pg.set_viewport_size({'width':width,'height':1000})
    if width<1000:pg.locator('[data-action=written-pane][data-pane=body]').click();pg.locator('.written-layout[data-pane=body]').wait_for()
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(n,width)
    if n in [15,16,33,39] and width in [390,1440]:pg.screenshot(path=str(scratch/f'preview-q{n:02}-{width}.png'))
   # All official fields through the actual input and submit flow.
   for i in c['items']:
    for f in i['fields']:
     key=i['id']+'--'+f['id'];selector=f'[data-written-key="{key}"]'
     if f['type']=='singleChoice':
      choice=next(a for a in f['choices'] if a['label']==f['referenceAnswers'][0]);pg.locator('input'+selector+f'[value="{choice["id"]}"]').check()
     else:pg.locator('input'+selector).fill(f['referenceAnswers'][0])
     pg.locator('[data-action=written-submit]'+selector).click();pg.locator('section.written-field'+selector).filter(has_text='自動判定：正解').wait_for()
   print('checked',n,flush=True)
  pg.locator('#main .study-toolbar [data-view=home]').click();pg.locator('.study-entry').wait_for();pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();pg.locator('[data-offline-select=all]').click();pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.study-entry').wait_for()
  open_written_case(pg,'fp2-202605-jafp-q16');pg.locator('.written-layout').wait_for();pg.wait_for_function('Array.from(document.querySelectorAll(".written-body img")).every(i=>i.complete&&i.naturalWidth>0)');assert pg.locator('.written-body img').count()==1
  pg.locator('#main .study-toolbar [data-view=home]').click();pg.locator('.study-entry').wait_for()
  open_written_case(pg,'fp2-202605-jafp-q04');pg.locator('input[data-written-key="item1--yield"]').fill('0.435');pg.reload();pg.locator('input[data-written-key="item1--yield"]').wait_for();assert pg.locator('input[data-written-key="item1--yield"]').input_value()=='0.435'
  ctx.set_offline(False);open_data_management(pg)
  with pg.expect_download() as ev:pg.locator('#export-state').click()
  backup=scratch/'test-backup.json';ev.value.save_as(str(backup));saved=json.loads(backup.read_text());assert len(saved['writtenBackup']['runs'])==len(cases)+2 and saved['records']==[]
  pg.get_by_role('button',name='設定を閉じる').click()
  fresh=b.new_context(viewport={'width':390,'height':844});other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(base+'fp2/?part=jafp-practical&entry=home');other.locator('.study-entry').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();other.get_by_role('button',name='設定を閉じる').click();other.locator('.study-entry [data-action=written-resume]').click();other.locator('input[data-written-key="item1--yield"]').wait_for();assert other.locator('input[data-written-key="item1--yield"]').input_value()=='0.435'
  select_target(other,'objective','fp2');other.locator('.quick-start').wait_for();assert state(other)['attempts']==[]
  assert not errors,errors
  b.close();(scratch/'browser-results.json').write_text(json.dumps({'mode':'published material via real application','casesRendered':len(cases),'fieldsSubmittedCorrectly':sum(len(i['fields']) for c in cases for i in c['items']),'requiredFiguresDecoded':sum(len(c['bodyFigures']) for c in cases),'viewports':[320,390,1440],'offlineManagedDownloadAndQ16Figure':True,'offlineNumericCheckpoint':True,'backupImport':True,'objectiveRecordsSeparated':True,'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
except Exception:
 pg.screenshot(path=str(scratch/'browser-failure.png')); print(pg.locator('#main').inner_text()[:2000],flush=True);raise
finally:server.shutdown()
print('PASS FP practical80case/136field; three widths; required figures/offline/checkpoint/backup/subject separation');print('Artifacts:',scratch)
