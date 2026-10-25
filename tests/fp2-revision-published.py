"""All60 reviewed explanations and old-version snapshots in isolated browsers."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,write_state,open_data_management,open_answer_history
from fp2_fixtures import builder

ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-fp2-revision-'))
questions=json.loads((ROOT/'content/fp2/questions.json').read_text());cfg=json.loads((ROOT/'content/fp2/qualification.json').read_text())
old=[builder.normalize({**q,'enrichment':'reviewed'},cfg,n+1) for n,q in enumerate(json.loads((ROOT/'delivery/content/fp2/questions.json').read_text()))]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
plain=lambda value:value.replace('**','')
errors=[]
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.getenv('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**options);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(BASE+'fp2/?part=objective&entry=home');pg.locator('.quick-start').wait_for();pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
  pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
  for q in questions:
   nav(pg,'materials');pg.locator('[name=query]').fill('問'+str(q['number']));pg.locator('[data-action=start][data-id="'+q['id']+'"]').click();pg.locator('.choices').wait_for();assert pg.locator('#result').count()==0
   index=next(i for i,c in enumerate(q['choices']) if c['id']==q['correctChoiceId']);pg.get_by_role('radio').nth(index).check();pg.locator('[data-action=submit]').click();pg.locator('#result').wait_for();pg.locator('#result details').evaluate_all('(els)=>els.forEach(e=>e.open=true)')
   assert pg.locator('#result details > p.explanation').text_content()==plain(q['explanation']),q['id']
   assert pg.locator('.takeaway').text_content()=='要点'+plain(q['takeaway']),q['id']
   assert pg.locator('.reason-list li').all_text_contents()==[c['label']+plain(r) for c,r in zip(q['choices'],q['choiceReasons'])],q['id']
   if q.get('summary'):assert pg.locator('#result > p.explanation').text_content()==plain(q['summary'])
   assert pg.locator('#result .takeaway strong:not(.takeaway-label)').count()>0
   for width,scale in [(320,100),(390,100),(1440,100),(390,200)]:
    pg.set_viewport_size({'width':width,'height':900});pg.evaluate('(s)=>document.documentElement.style.fontSize=s+"%"',scale)
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(q['number'],width,scale)
   if q['number'] in [14,27,46,55,59]:pg.screenshot(path=str(ART/('q'+str(q['number'])+'-offline.png')),full_page=True)
   pg.set_viewport_size({'width':390,'height':844});pg.evaluate('document.documentElement.style.fontSize=""')
   if q['number']%10==0:print('PASS published revised explanations',q['number'],flush=True)
  s=state(pg);assert len(s['attempts'])==60
  assert all(a['questionVersion']==next(q['version'] for q in questions if q['id']==a['questionId']) for a in s['attempts'])
  ctx.set_offline(False);open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-browser-backup.json';event.value.save_as(str(backup));assert len(json.loads(backup.read_text())['records'])==60
  fresh=b.new_context();other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(BASE+'fp2/?part=objective&entry=home');other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();assert len(state(other)['attempts'])==60;fresh.close()
  # Seed old records using the public storage adapter, preserving the actual old
  # material. Resume and backup must not reinterpret them as the new version.
  legacy=b.new_context();pg=legacy.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(BASE+'fp2/?part=objective&entry=home');pg.locator('.quick-start').wait_for()
  seeded=pg.evaluate('''async old=>{
   const {createAttempt,selectAnswer,gradeAttempt,finalizeAttempt}=await import('./src/domain/study.js');
   const finished=createAttempt(old[13]),paused=createAttempt(old[54]);selectAnswer(finished,old[13].answer,old[13]);finalizeAttempt(finished,gradeAttempt(finished));selectAnswer(paused,old[54].answer,old[54]);return {finished,paused};
  }''',old)
  before=state(pg);before.update(attempts=[seeded['finished'],seeded['paused']],currentId=seeded['paused']['id'],view='study');write_state(pg,before);pg.reload();pg.locator('.question-panel').wait_for();assert pg.get_by_role('radio').nth(old[54]['answer']).is_checked()
  after=state(pg);assert after['currentId']==before['currentId'];assert next(a for a in after['attempts'] if a['id']==seeded['paused']['id'])['materialSnapshot']==seeded['paused']['materialSnapshot']
  nav(pg,'history');open_answer_history(pg);pg.locator('[data-action=resume][data-id="'+seeded['finished']['id']+'"]').click();pg.locator('#result').wait_for();assert pg.locator('#result details > p.explanation').text_content()==seeded['finished']['materialSnapshot']['explanation']
  nav(pg,'materials');pg.locator('[name=query]').fill('問14');pg.locator('[data-action=start][data-id="fp2-202605-objective-q14"]').click();pg.locator('.choices').wait_for();s=state(pg);current=next(a for a in s['attempts'] if a['id']==s['currentId']);assert current['questionVersion']==3 and current['materialSnapshot']['explanation']==questions[13]['explanation']
  assert not errors,errors;b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({'revisedQuestions':60,'choiceReasons':240,'offlineManagedDownload':True,'widths':[320,390,1440],'fontScalePercent':[100,200],'backupImportRecords':60,'oldPausedAndCompletedSnapshotsPreserved':True,'newAttemptUsesNewVersion':True,'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
print('PASS FP60 revision /240 reasons / offline / responsive / backup / old and new versions');print('Artifacts:',ART)
