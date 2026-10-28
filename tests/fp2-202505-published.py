"""All May 2025 FP material through the full app, locally or on Pages."""
import json,os,shutil,sys,tempfile,threading
from pathlib import Path
from functools import partial
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,open_data_management,select_target,open_written_case,wait_for_async
ROOT=Path(__file__).resolve().parents[1]
ART=Path(tempfile.mkdtemp(prefix='hitomon-fp2-202505-'))
qs=[q for q in json.loads((ROOT/'content/fp2/questions.json').read_text()) if q['packId']=='202505']
cases=[c for c in json.loads((ROOT/'content/fp2/practical-cases.json').read_text()) if c['id'].startswith('fp2-202505-')]
assert len(qs)==60 and len(cases)==40
required={f['image'] for c in cases for f in c['bodyFigures']}
assert len(required)==5
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
    def translate_path(self,path):
        if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
        return super().translate_path(path)

server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
url=BASE+'fp2/?part=objective&entry=home'
errors=[]
plain=lambda t:t.replace('**','')
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.environ.get('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts)
  ctx=b.new_context(viewport={'width':390,'height':900});pg=ctx.new_page()
  pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto(url);pg.locator('.quick-start').wait_for()
  pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
  pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for()
  pg.locator('[data-offline-select=all]').click();pg.locator('[data-offline-save]').click()
  pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000)
  pg.locator('[data-offline-close]').click()
  select_target(pg,'jafp-practical','fp2');pg.locator('.study-entry').wait_for()
  pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for()
  pg.locator('[data-offline-select=all]').click();pg.locator('[data-offline-save]').click()
  pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click()
  select_target(pg,'objective','fp2');pg.locator('.quick-start').wait_for()
  ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
  for q in qs:
   nav(pg,'materials');pg.locator('[name=query]').fill(q['title'])
   pg.locator(f'[data-action=start][data-id="{q["id"]}"]').click();pg.locator('.choices').wait_for()
   assert pg.locator('#result,.hint-box').count()==0
   if q['number'] in [10,28]:assert pg.locator('.question-stem table').count()==1
   for h in q.get('hints',[]):
    button=pg.locator('[data-action=hint]');assert ('答えを含む' in button.inner_text())==h['revealsAnswer']
    button.click();assert plain(h['text']) in pg.locator('#hints').inner_text()
   index=next(i for i,c in enumerate(q['choices']) if c['id']==q['correctChoiceId'])
   pg.get_by_role('radio').nth(index).check();pg.locator('[data-action=submit]').click();pg.locator('#result').wait_for()
   saved=state(pg);trial=next(a for a in saved['attempts'] if a['id']==saved['currentId'])
   assert trial['status']==('revealed' if any(h['revealsAnswer'] for h in q.get('hints',[])) else ('assisted' if q.get('hints') else 'correct'))
   assert trial['hintsBeforeAnswer']==0
   pg.locator('#result details').evaluate_all('(es)=>es.forEach(e=>e.open=true)')
   assert pg.locator('.reason-list li').all_text_contents()==[c['label']+plain(r) for c,r in zip(q['choices'],q['choiceReasons'])]
   assert pg.locator('#result details > p.explanation').text_content()==plain(q['explanation'])
   for width in [320,390,1440]:
    pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),q['id']
   pg.set_viewport_size({'width':390,'height':900})
   if q['number']%10==0:print('PASS objective',q['number'],flush=True)
  select_target(pg,'jafp-practical','fp2');pg.locator('.study-entry').wait_for()
  decoded=set()
  for n,c in enumerate(cases,1):
   pg.set_viewport_size({'width':1440,'height':1000})
   open_written_case(pg,c['id']);pg.locator('.written-layout').wait_for()
   assert pg.locator('.written-body figure').count()==len(c['bodyFigures'])
   if c['bodyFigures']:
    pg.wait_for_function('Array.from(document.querySelectorAll(".written-body img")).every(i=>i.complete&&i.naturalWidth>0)')
    decoded.update(f['image'] for f in c['bodyFigures'])
   for width,scale in [(320,100),(390,100),(1440,100),(390,200)]:
    pg.set_viewport_size({'width':width,'height':1000});pg.evaluate('(s)=>document.documentElement.style.setProperty("--study-text-scale",String(s/100))',scale)
    if width<1000:pg.locator('[data-action=written-pane][data-pane=body]').click()
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(n,width,scale)
    if width==390 and scale==100 and n in [5,8,9,13,14,18,23,24,29,33,37,40]:pg.screenshot(path=str(ART/f'practical-q{n:02}-390.png'))
   pg.evaluate('document.documentElement.style.removeProperty("--study-text-scale")');pg.set_viewport_size({'width':1440,'height':1000})
   for it in c['items']:
    for f in it['fields']:
     key=it['id']+'--'+f['id'];selector=f'[data-written-key="{key}"]'
     if f['type']=='singleChoice':
      ch=next(ch for ch in f['choices'] if ch['label']==f['referenceAnswers'][0])
      choice=pg.locator('input'+selector+f'[value="{ch["id"]}"]')
      choice.locator('..').click();assert choice.is_checked()
     else:pg.locator('input'+selector).fill(f['referenceAnswers'][0])
    if len(it['fields'])>1:pg.locator('[data-action=written-check-item]').click()
    else:pg.locator('[data-action=written-submit]').click()
    for f in it['fields']:
     key=it['id']+'--'+f['id'];pg.locator(f'section.written-field[data-written-key="{key}"]').filter(has_text='自動判定：正解').wait_for()
   pg.locator('#main .study-toolbar [data-view=home]').click();pg.locator('.study-entry').wait_for()
   if n%10==0:print('PASS practical',n,flush=True)
  assert decoded==required
  # A new, ungraded written response survives an offline reload.
  open_written_case(pg,'fp2-202505-jafp-q05');pg.locator('input[data-written-key="item1--amount"]').fill('1.23')
  wait_for_async(pg,'''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:'fp2',rootPath:root.pathname});try{const i=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),w=createWorkspaceStore({...i,rootPath:root.pathname,namespaceName:'written',validate:()=>{}});try{return (await w.read()).some(r=>r.payload.caseId==='fp2-202505-jafp-q05'&&r.payload.responses['item1--amount']?.value==='1.23');}finally{await w.close();}}finally{await s.close();}}''')
  pg.reload();pg.locator('.written-layout').wait_for();assert pg.locator('input[data-written-key="item1--amount"]').input_value()=='1.23'
  ctx.set_offline(False);open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-backup.json';event.value.save_as(str(backup));data=json.loads(backup.read_text())
  assert len(data['records'])==60 and len(data['writtenBackup']['runs'])==41
  fresh=b.new_context(viewport={'width':390,'height':900});other=fresh.new_page();other.on('dialog',lambda d:d.accept())
  other.goto(url);other.locator('.quick-start').wait_for();open_data_management(other)
  other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for()
  assert len(state(other)['attempts'])==60
  other.get_by_role('button',name='設定を閉じる').click();select_target(other,'jafp-practical','fp2')
  other.locator('.study-entry [data-action=written-resume]').click();other.locator('.written-layout').wait_for()
  assert other.locator('input[data-written-key="item1--amount"]').input_value()=='1.23'
  assert not errors,errors
  b.close()
except Exception:
 try:
  pg.screenshot(path=str(ART/'failure.png'));(ART/'failure.txt').write_text(pg.locator('body').inner_text())
 except Exception:pass
 print('Artifacts:',ART,flush=True)
 raise
finally:server.shutdown()
result={'scope':'Reviewed 202505 material in the full published bank; isolated guest, no personal account access','baseURL':BASE,'objectiveQuestions':60,'choicesAndReasons':240,'hints':0,'practicalCases':40,'officialFieldsCorrect':68,'uniqueRequiredFiguresDecodedOffline':len(decoded),'figurePlacements':5,'viewports':[320,390,1440],'studyTextScale200Percent':True,'offlineDownloadAndAll100Problems':True,'offlineWrittenCheckpoint':True,'syntheticBackupExportImport':True,'pageErrors':errors,'artifactDirectory':str(ART)}
(ART/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS PR37 real UI / all100 / no hints / 68 fields / 5 figures / offline / checkpoint / backup')
print('Artifacts:',ART)
