"""Real FP60 corpus in a fresh guest browser; local or deployed URL."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,open_data_management
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-fp2-published-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**options);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto(BASE+'?qualifications');pg.locator('.qualification-option[data-qualification-id=fp2]').first.wait_for()
  assert pg.locator('.qualification-option[data-qualification-id=fp2]').count()==2
  objective=pg.locator('.qualification-option[data-qualification-id=fp2][data-part-id=objective]')
  assert '60問' in objective.inner_text()
  practical=pg.locator('.qualification-option[data-qualification-id=fp2][data-part-id=jafp-practical]')
  assert '40問' in practical.inner_text()
  objective.click();pg.locator('.quick-start').wait_for()
  assert pg.locator('[data-mode=diagnostic],[data-view=diagnostics],[data-view=mocks],[data-action=cards-open]').count()==0
  assert state(pg)['attempts']==[]
  pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
  pg.locator('[data-action=offline-open]').click();pg.locator('[data-offline-save]').wait_for();assert pg.locator('[data-offline-group]').count()==1
  pg.locator('[data-offline-save]').click();pg.locator('#offline-message').filter(has_text='保存できました').wait_for(timeout=60000);pg.locator('[data-offline-close]').click();assert state(pg)['attempts']==[]
  ctx.set_offline(True);pg.reload();pg.locator('.quick-start').wait_for()
  for n,correct in [(55,1),(14,2),(35,0)]:
   nav(pg,'materials');pg.locator('[name=query]').fill(f'問{n}');qid=f'fp2-202605-objective-q{n:02}';pg.locator(f'[data-action=start][data-id="{qid}"]').click();pg.locator('.choices').wait_for()
   assert '2025-04-01' in pg.locator('.legal-context').inner_text();assert pg.get_by_role('radio').count()==4
   if n==55:
    pg.wait_for_function('document.querySelector(".question-figure img")?.naturalWidth===888')
    assert pg.locator('.original-question').count()==0
    for width in [320,390,1440]:
     pg.set_viewport_size({'width':width,'height':900});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');pg.screenshot(path=str(ART/f'q55-offline-{width}.png'),full_page=True)
   pg.get_by_role('radio').nth(correct).check()
   if n==55:
    saved=state(pg);pg.reload();pg.locator('.choices').wait_for();assert pg.get_by_role('radio').nth(correct).is_checked();assert state(pg)['currentId']==saved['currentId']
   pg.get_by_role('button',name='回答する',exact=True).click();pg.locator('#result-heading').wait_for();assert pg.locator('#result-heading').inner_text()=='自力で正解';assert pg.locator('.reason-list li').count()==4
   if n==14:assert '合計上限４万円' in pg.locator('.reason-list li').nth(3).text_content()
   if n==35:assert '最初に返済した月' in pg.locator('.reason-list li').first.text_content()
   prompt=pg.evaluate('''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:'fp2',rootPath:root.pathname});try{const state=JSON.parse(await s.snapshot()),a=state.attempts.find(a=>a.id===state.currentId),{buildAIPrompt}=await import(new URL('src/features/ai-handoff.js',root));return buildAIPrompt({question:{...a.questionSnapshot,...a.materialSnapshot},attempt:a,qualification:{name:'FP2級'},baseURL:root.href});}finally{await s.close()}}''')
   assert '2025-04-01' in prompt and f'問{n}' in prompt
   if n==55:assert 'q55-family-chart.png' in prompt
  assert len(state(pg)['attempts'])==3
  ctx.set_offline(False);nav(pg,'history');open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'guest-backup.json';event.value.save_as(str(backup));data=json.loads(backup.read_text());assert len(data['records'])==3
  pg.get_by_role('button',name='設定を閉じる').click();pg.goto(BASE+'ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for();ap_state=state(pg);assert ap_state is None or ap_state['attempts']==[]
  pg.goto(BASE+'fp2/?part=objective&entry=home');pg.locator('.quick-start').wait_for();assert len(state(pg)['attempts'])==3
  fresh=b.new_context();other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(BASE+'fp2/');other.locator('.quick-start').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();assert len(state(other)['attempts'])==3
  assert not errors,errors;b.close()
finally:server.shutdown()
print('PASS FP60 objective + practical chooser / objective questions and required diagram offline / checkpoint / corrected answers / AI / backup / AP separation / 320,390,1440 / no JS errors')
print('Artifacts:',ART)
