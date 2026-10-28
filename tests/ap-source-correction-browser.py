"""A corrected question offline, old v3 snapshots and a separate v4 attempt."""
import importlib.util,json,os,shutil,tempfile,threading
from pathlib import Path
from functools import partial
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,write_state,open_data_management,open_answer_history
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-source-correction-'));ID='r04a-q13'
read=lambda p:json.loads(p.read_text());m=read(ROOT/'data/qualifications/ap/manifest.json');q=next(q for p in m['packs'] for q in read(ROOT/'data/qualifications/ap'/p['url']) if q['id']==ID)
journals=[read(p) for p in (ROOT/'data/transcription-context-revisions').glob('*.json')];old_raw=next(i['beforeQuestion'] for j in journals for i in j['items'] if i['id']==ID and i.get('afterQuestion',{}).get('version')==4)
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);old=builder.normalize(old_raw,read(ROOT/'content/ap/qualification.json'),1)
assert old['version']==3 and q['version']==4
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/ap-study/';errors=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':390,'height':900});pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(BASE+'ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for();pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
  pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();pg.locator('[data-offline-select=none]').click();pg.locator(f'[data-offline-group="pack-{q["packId"]}-objective"]').check();pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
  nav(pg,'materials');pg.locator('[data-action=reset-filters]').click();pg.locator('[name=year]').select_option('2022');pg.locator('[name=season]').select_option('autumn');pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{ID}"]').click();pg.locator('.choices').wait_for()
  def correct_labels():
   text=pg.locator('.choices').inner_text();assert 'フェールセーフ' in text and 'フェールソフト' in text and 'フールセーフ' not in text and 'フールソフト' not in text,text
  correct_labels();pg.get_by_role('radio').nth(q['answer']).check();pg.locator('[data-action=submit]').click();pg.locator('#result').wait_for();s=state(pg);new_finished=next(a for a in s['attempts'] if a['id']==s['currentId']);assert new_finished['status']=='correct' and new_finished['questionVersion']==4;pg.screenshot(path=str(ART/'current-v4-390.png'),full_page=True)
  for width,scale in [(320,100),(390,200),(1440,100)]:
   pg.set_viewport_size({'width':width,'height':1000});pg.evaluate('(s)=>document.documentElement.style.setProperty("--study-text-scale",String(s/100))',scale);assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  pg.evaluate('document.documentElement.style.removeProperty("--study-text-scale")');pg.set_viewport_size({'width':390,'height':900})
  seeded=pg.evaluate('''async old=>{const {createAttempt,selectAnswer,openHint,gradeAttempt,finalizeAttempt}=await import(new URL('src/domain/study.js',document.baseURI));const finished=createAttempt(old),paused=createAttempt(old);selectAnswer(finished,old.answer,old);finalizeAttempt(finished,gradeAttempt(finished));selectAnswer(paused,1,old);openHint(paused);return {finished,paused};}''',old)
  assert seeded['finished']['status']=='correct';s=state(pg);s.update(attempts=[new_finished,seeded['finished'],seeded['paused']],currentId=seeded['paused']['id'],view='study');write_state(pg,s);pg.reload();pg.locator('.choices').wait_for();assert 'フールセーフ' in pg.locator('.choices').inner_text();pg.screenshot(path=str(ART/'legacy-v3-390.png'),full_page=True)
  pg.locator('[data-action=latest-hints]').click();pg.wait_for_function("document.querySelector('.choices')?.textContent.includes('フェールセーフ')");correct_labels();s=state(pg);latest=next(a for a in s['attempts'] if a['id']==s['currentId']);assert latest['id']!=seeded['paused']['id'] and latest['questionVersion']==4 and latest['selected']==seeded['paused']['selected'];assert pg.get_by_role('radio').nth(1).is_checked()
  for prior in [seeded['finished'],seeded['paused']]:
   saved=next(a for a in s['attempts'] if a['id']==prior['id'])
   diff={key:{'before':prior[key],'after':saved[key]} for key in ['questionSnapshot','materialSnapshot','hintEvents'] if prior[key]!=saved[key]}
   if diff:(ART/'snapshot-diff.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2)+'\n');print('Snapshot comparison:',ART,flush=True)
   assert not diff,diff
   assert saved['selected']==prior['selected'] and saved['status']==('postponed' if prior['id']==seeded['paused']['id'] else prior['status'])
  pg.set_viewport_size({'width':1440,'height':1000});pg.screenshot(path=str(ART/'latest-v4-1440.png'),full_page=True)
  nav(pg,'history');open_answer_history(pg);pg.locator(f'[data-action=resume][data-id="{seeded["finished"]["id"]}"]').click();pg.locator('#result').wait_for();assert 'フールセーフ' in pg.locator('.choices').inner_text();assert next(a for a in state(pg)['attempts'] if a['id']==seeded['finished']['id'])['status']=='correct'
  open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-backup.json';event.value.save_as(str(backup));assert len(read(backup)['records'])==4
  fresh=b.new_context();other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(BASE+'ap/?part=objective&entry=home');other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();attempts=state(other)['attempts'];assert len(attempts)==4 and sorted(a['questionVersion'] for a in attempts)==[3,3,4,4]
  assert not errors,errors;b.close()
finally:server.shutdown()
r={'scope':'Isolated synthetic guest records only','question':ID,'beforeVersion':3,'afterVersion':4,'offlineCorrectedChoices':True,'oldFinishedAndPausedSnapshotsAndHintsPreserved':True,'oldPausedProgressAfterStartingNewAttempt':'postponed','latestVersionCreatesSeparateAttemptAndPreservesSelection':True,'backupRoundTripRecords':4,'widths':[320,390,1440],'studyTextScalePercent':[100,200],'pageErrors':errors,'artifactDirectory':str(ART)};(ART/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('PASS corrected choices/offline/v3 snapshots/v4 separate attempt/backup4');print('Artifacts:',ART)
