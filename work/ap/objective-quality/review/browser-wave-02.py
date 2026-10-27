"""Wave02: batch-05..08 in real app; derived from the validated pilot browser check."""
import json,os,shutil,tempfile,threading,importlib.util,sys
from pathlib import Path
from functools import partial
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/"tests"))
from browser_storage import nav,state,write_state,open_data_management,open_answer_history
ROOT=Path(__file__).resolve().parents[4];W=ROOT/'work/ap/objective-quality';ART=Path(tempfile.mkdtemp(prefix='hitomon-ap-quality-'))
read=lambda p:json.loads(p.read_text());ids=[id for n in range(5,9) for id in read(W/f'batches/batch-{n:02d}/assignment.json')['questionIds']];m=read(ROOT/'data/qualifications/ap/manifest.json')
bank=[q for pack in m['packs'] for q in read(ROOT/'data/qualifications/ap'/pack['url'])];by={q['id']:q for q in bank};qs=[by[id] for id in ids]
sys.path.insert(0,str(ROOT/'tools'));spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);cfg=read(ROOT/'content/ap/qualification.json');old={q['id']:builder.normalize(q,cfg,n+1) for n,q in enumerate(read(W/'baseline/questions.json')) if q['id'] in ids or q['id'] in ['r07h-q4','r05a-q1']}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/');plain=lambda s:s.replace('**','');errors=[]
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':900});pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(BASE+'ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for()
  pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller');pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();pg.locator('[data-offline-select=none]').click()
  for pack in {q['packId'] for q in qs}:pg.locator(f'[data-offline-group="pack-{pack}-objective"]').check()
  pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
  def open_q(q):
   nav(pg,'materials');pg.locator('[data-action=reset-filters]').click();pg.locator('[name=year]').select_option(str(q['year']));pg.locator('[name=season]').select_option(q['season']);pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{q["id"]}"]').click();pg.locator('.choices').wait_for()
  def submit(q):
   pg.get_by_role('radio').nth(q['answer']).check();pg.locator('[data-action=submit]').click();pg.locator('#result').wait_for();s=state(pg);return next(a for a in s['attempts'] if a['id']==s['currentId'])
  for n,q in enumerate(qs,1):
   open_q(q);assert pg.locator('#result,.hint-box').count()==0
   for img in pg.locator('.question-panel img').all():img.scroll_into_view_if_needed();img.evaluate('(i)=>i.decode()')
   for step,h in enumerate(q['hints'],1):
    button=pg.locator('[data-action=hint]');assert ('答えを含む' in button.inner_text())==h['revealsAnswer'];button.click();assert plain(h['text']) in pg.locator('#hints').inner_text();assert pg.locator('.hint-box').count()==step;assert pg.locator('#result').count()==0
   a=submit(q);assert a['questionVersion']==q['version'] and a['hintsBeforeAnswer']==3 and a['status']==('revealed' if any(h['revealsAnswer'] for h in q['hints']) else 'assisted')
   pg.locator('#result details').evaluate_all('(es)=>es.forEach(e=>e.open=true)')
   assert pg.locator('#result details > p.explanation').text_content()==plain(q['explanation'])
   assert pg.locator('.reason-list li').all_text_contents()==[c['label']+plain(r) for c,r in zip(q['choices'],q['choiceReasons'])]
   assert pg.locator('#result > p.explanation').text_content()==plain(q['summary'])
   for width,scale in [(320,100),(390,100),(1440,100),(390,200)]:
    pg.set_viewport_size({'width':width,'height':1000});pg.evaluate('(s)=>document.documentElement.style.setProperty("--study-text-scale",String(s/100))',scale);assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(q['id'],width,scale)
    if q['id'] in ['r04h-q11','r03a-q12','r06a-q12','r07h-q17'] and width==390 and scale==100:pg.screenshot(path=str(ART/(q['id']+'-390.png')),full_page=True)
   pg.evaluate('document.documentElement.style.removeProperty("--study-text-scale")');pg.set_viewport_size({'width':390,'height':900});print('PASS wave02',n,q['id'],flush=True)
  # A first-stage answer and a cumulative second-stage answer must be revealed immediately.
  for id,count in [('r07h-q4',1),('r03h-q2',2)]:
   q=by[id];open_q(q)
   for _ in range(count):pg.locator('[data-action=hint]').click()
   pg.get_by_role('radio').nth(q['answer']).check();state(pg);pg.reload();pg.locator('.hint-box').first.wait_for();assert pg.locator('.hint-box').count()==count;assert pg.get_by_role('radio').nth(q['answer']).is_checked();a=submit(q);assert a['status']=='revealed' and a['hintsBeforeAnswer']==count
  # Later hints preserve a result obtained without help.
  q=by['r07h-q4'];open_q(q);a=submit(q);assert a['status']=='correct'
  for _ in q['hints']:pg.locator('[data-action=hint]').click()
  s=state(pg);a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['status']=='correct' and a['hintsBeforeAnswer']==0 and all(e['phase']=='after' for e in a['hintEvents'])
  ctx.set_offline(False);open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-backup.json';event.value.save_as(str(backup));assert len(read(backup)['records'])==83
  fresh=b.new_context();other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(BASE+'ap/?part=objective&entry=home');other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();assert len(state(other)['attempts'])==83;fresh.close()
  legacy=b.new_context();pg=legacy.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(BASE+'ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for()
  seeded=pg.evaluate('''async old=>{const {createAttempt,selectAnswer,openHint,gradeAttempt,finalizeAttempt}=await import(new URL('src/domain/study.js',document.baseURI));const finished=createAttempt(old['r07h-q4']),paused=createAttempt(old['r05a-q1']);openHint(finished);selectAnswer(finished,old['r07h-q4'].answer,old['r07h-q4']);finalizeAttempt(finished,gradeAttempt(finished));selectAnswer(paused,old['r05a-q1'].answer,old['r05a-q1']);return {finished,paused};}''',old)
  assert seeded['finished']['status']=='assisted';s=state(pg);s.update(attempts=[seeded['finished'],seeded['paused']],currentId=seeded['paused']['id'],view='study');write_state(pg,s);pg.reload();pg.locator('.question-panel').wait_for()
  s=state(pg);assert next(a for a in s['attempts'] if a['id']==seeded['paused']['id'])['materialSnapshot']==seeded['paused']['materialSnapshot']
  pg.locator('[data-action=latest-hints]').click();pg.locator('.question-panel').wait_for();s=state(pg);new=next(a for a in s['attempts'] if a['id']==s['currentId']);assert new['id']!=seeded['paused']['id'] and new['questionVersion']==by['r05a-q1']['version'] and new['selected']==seeded['paused']['selected'];assert next(a for a in s['attempts'] if a['id']==seeded['paused']['id'])['materialSnapshot']==seeded['paused']['materialSnapshot']
  nav(pg,'history');open_answer_history(pg);pg.locator(f'[data-action=resume][data-id="{seeded["finished"]["id"]}"]').click();pg.locator('#result').wait_for();assert pg.locator('#result details > p.explanation').text_content()==plain(seeded['finished']['materialSnapshot']['explanation']);assert next(a for a in state(pg)['attempts'] if a['id']==seeded['finished']['id'])['status']=='assisted'
  assert not errors,errors;b.close()
finally:server.shutdown()
result={'scope':'isolated synthetic guest records, no personal account','baseURL':BASE,'batches':[f'batch-{n:02d}' for n in range(5,9)],'questions':80,'hints':240,'choiceReasons':320,'widths':[320,390,1440],'studyTextScalePercent':[100,200],'offline':True,'backupImportRecords':83,'oldSnapshotsAndGradesPreserved':True,'latestHintsCreatesSeparateNewVersion':True,'afterGradingHintsPreserveOutcome':True,'firstAndCumulativeRevealVerified':True,'pageErrors':errors,'artifactDirectory':str(ART)};(ART/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('PASS AP wave02 80questions/240hints/320reasons/offline/snapshots/backup');print('Artifacts:',ART)
