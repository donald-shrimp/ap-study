"""Mixed recommendations through real UI/IndexedDB; only isolated guest records."""
import json,os,shutil,tempfile,threading
from datetime import datetime,timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from browser_storage import state,write_state
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-scheduling-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
def current(pg):
 s=state(pg);return next(a for a in s['attempts'] if a['id']==s['currentId'])
def start(pg):
 pg.locator('.study-entrance[data-paper-mode=all]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();return current(pg)
def answer(pg):
 a=current(pg);q=a['questionSnapshot'];ids=pg.evaluate('''async q=>{const {correctIds}=await import('./src/domain/question-format.js');return correctIds(q);}''',q)
 for i,c in enumerate(q['choices']):
  if c['id'] in ids:pg.locator('.choice').nth(i).click()
 pg.get_by_role('button',name='回答する',exact=True).click();pg.locator('#result-heading').wait_for();assert current(pg)['status']=='correct'
def next_question(pg):
 pg.get_by_role('button',name='もう1問',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();return current(pg)
errors=[];results=[]
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts)
  for qualification in ['ap','ab730','fp2']:
   ctx=b.new_context(viewport={'width':390,'height':900},timezone_id='Asia/Tokyo');pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(BASE+qualification+'/?part=objective&entry=home');pg.locator('.study-entrance[data-paper-mode=all]').wait_for();s=state(pg)
   fixture=pg.evaluate('''async()=>{
    const {loadCatalog}=await import('./src/content/catalog.js'),{createAttempt,selectAnswer,finalizeAttempt}=await import('./src/domain/study.js');
    const catalog=await loadCatalog(document.documentElement.dataset.qualification,{requestedPartId:'objective'}),attempts=[];
    for(const [i,id] of catalog.questions.slice(0,8).map(q=>q.id).entries()){
     await catalog.ensure(id);const q=catalog.questions.find(q=>q.id===id),at=new Date(Date.now()-(30+i)*86400000).toISOString(),a=createAttempt(q,{at});
     selectAnswer(a,(q.answer+1)%q.choices.length);finalizeAttempt(a,'incorrect',at);a.practiceScope={intent:'review'};attempts.push(a);
    }return attempts;
   }''')
   known={a['questionId'] for a in fixture};oldest=fixture[-1]['questionId'];s.update(attempts=fixture,currentId=None,view='home',session={'attemptIds':[],'topic':None});write_state(pg,s);pg.reload();pg.locator('.study-entrance[data-paper-mode=all]').wait_for()
   first=start(pg);assert first['questionId'] not in known;answer(pg)
   pg.get_by_role('button',name='ホーム',exact=True).click();pg.locator('.study-entrance[data-paper-mode=all]').wait_for();state(pg);pg.reload();pg.locator('.study-entrance[data-paper-mode=all]').wait_for()
   second=start(pg);assert second['questionId'] not in known and second['questionId']!=first['questionId'];answer(pg)
   third=next_question(pg);assert third['questionId']==oldest
   pg.get_by_role('button',name='解答を見る',exact=True).click();pg.locator('#result-heading').wait_for();assert current(pg)['status']=='revealed'
   tomorrow=(datetime.now(ZoneInfo('Asia/Tokyo'))+timedelta(days=1)).date().isoformat();assert tomorrow in pg.locator('.review-date').inner_text()
   fourth=next_question(pg);assert fourth['questionId'] not in known
   pg.locator('.choice').first.click();saved=current(pg)
   pg.evaluate('''async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener('controllerchange',ok,{once:true}));}''')
   ctx.set_offline(True);pg.reload();pg.get_by_role('button',name='回答する',exact=True).wait_for();restored=current(pg);assert restored['id']==saved['id'] and restored['selected']==saved['selected'];ctx.set_offline(False)
   for width in [320,390,1440]:
    pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');pg.screenshot(path=str(ART/f'{qualification}-{width}.png'))
   results.append({'qualification':qualification,'newReviewMix':['new','new','due','new'],'sessionRestart':True,'revealedNextDay':True,'offlineResume':True});ctx.close()
  assert not errors,errors;b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({'cases':results,'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
print('PASS AP / AB-730 / FP normal mix, session restart, oldest review, disclosure and offline resume');print('Artifacts:',ART)
