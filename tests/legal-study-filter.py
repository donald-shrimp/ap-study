"""Private synthetic changed-law material; never modifies published questions."""
import copy,json,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from fp2_fixtures import prepare,builder,write
from browser_storage import nav,state,select_target,open_data_management
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with tempfile.TemporaryDirectory(prefix='hitomon-law-filter-') as d:
 root=Path(d);cfg,normal,cases=prepare(root);base=root/'content/fp2'
 old=copy.deepcopy(normal);old.update(id='synthetic-old',title='改正ありの合成問題');old['legalReview']={'status':'outdated','checkedAt':'2026-10-24','sourceRefs':['https://example.com/law'],'note':'合成テストの改正情報。'}
 normal['uses']=old['uses']=['practice','mock'];questions=[old,normal];hashes=json.loads((base/'source-files.json').read_text())
 cfg['mockSetSource']='content/fp2/mocks.json';write(base/'qualification.json',cfg)
 write(base/'questions.json',questions);write(base/'question-reviews.json',[{'questionId':q['id'],'version':1,'sha256':builder.diagnostic_digest(q),'normalizedSha256':builder.diagnostic_digest(builder.normalize(q,cfg,n+1)),'author':'synthetic-author','reviewer':'synthetic-reviewer','checkedAt':'2026-10-24T00:00:00Z','checks':{k:True for k in ['source','answer','choices','wording']},'notes':'Private synthetic test evidence only.','sourceHashes':hashes} for n,q in enumerate(questions)])
 write(base/'mocks.json',{'format':'hitomon-mock-sets','version':1,'qualificationId':'fp2','sets':[{'id':'synthetic-fixed','label':'合成模試','version':1,'status':'ready','size':2,'slots':[{'number':n+1,'questionId':q['id'],'topicId':q['topicId']} for n,q in enumerate(questions)]}]})
 cases[0]['legalReview']=copy.deepcopy(old['legalReview']);write(base/'practical-cases.json',cases);cr=json.loads((base/'practical-reviews.json').read_text());cr[0]['canonicalCaseSHA256']=builder.diagnostic_digest(cases[0]);write(base/'practical-reviews.json',cr);builder.build(root)
 manifest=json.loads((root/'data/qualifications/fp2/manifest.json').read_text());assert manifest['mockSets']['sets'][0]['hasLawChange'] is True
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/fp2/'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);pg=b.new_page(viewport={'width':390,'height':844});errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(url);pg.locator('.quick-start').wait_for()
   def exclude(value):
    pg.locator('#settings-button').click();pg.locator('#exclude-outdated').set_checked(value);state(pg);pg.get_by_role('button',name='設定を閉じる').click()
   def open_q(id):
    nav(pg,'materials');pg.locator(f'[data-action=start][data-id="{id}"]').click();pg.locator('.choices').wait_for()
   nav(pg,'materials');assert pg.locator('#catalog-results [data-action=start]').count()==1
   nav(pg,'home');pg.locator('.study-entrance').first.click();pg.locator('.choices').wait_for();s=state(pg);a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['questionId']==normal['id'];assert pg.locator('.legal-context').inner_text()=='法令基準日：2026-04-01'
   pg.get_by_role('radio').last.check();pg.locator('[data-action=submit]').click();pg.locator('#result-heading').wait_for()
   exclude(False);pg.reload();pg.locator('#result-heading').wait_for();assert state(pg)['settings']['excludeOutdated'] is False;open_q(old['id']);assert '学習非推奨' in pg.locator('.legal-context').inner_text();assert '2026-10-24' not in pg.locator('.legal-context').inner_text()
   pg.get_by_role('radio').last.check();pg.locator('[data-action=submit]').click();pg.locator('#result-heading').wait_for();exclude(True);nav(pg,'materials');assert pg.locator('#catalog-results [data-action=start]').count()==1
   state(pg);pg.reload();pg.locator('#qualification-switch').wait_for();assert state(pg)['settings']['excludeOutdated'] is True
   nav(pg,'history');assert len(state(pg)['attempts'])==2;open_data_management(pg)
   with pg.expect_download() as event:pg.locator('#export-state').click()
   backup=root/'private-test-backup.json';event.value.save_as(str(backup));data=json.loads(backup.read_text());assert data['settings']['excludeOutdated'] is True;record=next(r for r in data['records'] if r['questionId']==old['id']);assert record['material']['legalReview']==old['legalReview'];pg.get_by_role('button',name='設定を閉じる').click()
   nav(pg,'home');pg.locator('[data-view=mocks]').click();pg.locator('[data-action=start-mock]').wait_for();assert pg.locator('[data-action=start-mock]').is_disabled();exclude(False);assert pg.locator('[data-action=start-mock]').is_enabled()
   pg.locator('[data-action=start-mock]').click();pg.locator('[data-action=pause-diagnostic]').wait_for();pg.locator('[data-action=pause-diagnostic]').click();exclude(True);pg.locator('[data-view=mocks]').click();pg.locator('[data-action=resume-diagnostic]').wait_for();assert pg.locator('[data-action=start-mock]').is_disabled();pg.locator('[data-action=resume-diagnostic]').click();pg.locator('[data-action=pause-diagnostic]').wait_for();pg.locator('[data-action=pause-diagnostic]').click()
   select_target(pg,'jafp-practical','fp2');pg.locator('.study-entry').wait_for();assert pg.locator('.quick-start [data-action=written-start]').is_disabled()
   exclude(False);pg.locator('[data-action=written-start]').first.click();pg.locator('.written-layout').wait_for();assert '学習非推奨' in pg.locator('.legal-context').inner_text();pg.locator('input[data-written-key="q1--amount"]').fill('123');exclude(True);nav(pg,'home');assert pg.locator('.quick-start [data-action=written-start]').is_disabled() and pg.locator('.study-entry [data-action=written-resume]').count()==0
   nav(pg,'history');pg.locator('[data-action=written-resume]').first.click();pg.locator('.written-layout').wait_for();assert pg.locator('input[data-written-key="q1--amount"]').input_value()=='123'
   assert not errors,errors;b.close()
 finally:server.shutdown()
print('PASS synthetic confirmed-law filter / unchecked label hidden / include switch and persistence / original date+flag in backup / normal and case exclusion / blocked fixed mock with saved-run resume / historical answers and typed input retained')
