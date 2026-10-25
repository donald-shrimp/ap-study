"""Qualification-specific sync labels in the real shared settings renderer."""
import os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/')
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);pg=b.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  for id,label in [('ap','科目B'),('fp2','実技（日本FP協会）')]:
   pg.goto(BASE+id+'/?part=objective&entry=home');pg.locator('.quick-start').wait_for();pg.locator('#settings-button').click()
   for kind in ['error','conflict']:
    pg.evaluate('''async({id,kind})=>{const root=new URL('.',document.baseURI),q=await(await fetch(new URL('data/qualifications/'+id+'/manifest.json',root))).json(),{qualificationSyncLabels}=await import(new URL('src/domain/sync-status.js',root)),ui=await import(new URL('src/ui/sync-status.js',root));ui.setSyncAccount(true,['written'],qualificationSyncLabels(q));ui.setSyncStatus('written',kind,new Error('synthetic'));}''',{'id':id,'kind':kind})
    assert pg.locator('#sync-details strong').inner_text()==label
    if id=='fp2':assert '科目B' not in pg.locator('#sync-details').inner_text() and 'きんざい' not in pg.locator('#sync-details').inner_text()
    for width in [320,390,1440]:
     pg.set_viewport_size({'width':width,'height':1000});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert pg.locator('#settings-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
   pg.evaluate('''async()=>{const ui=await import(new URL('src/ui/sync-status.js',document.baseURI));ui.setSyncStatus('written','synced');}''');assert pg.locator('#sync-state').inner_text()=='同期済み';assert pg.locator('#sync-details').is_hidden()
  assert not errors,errors;b.close()
finally:server.shutdown()
print('PASS AP/FP sync error and conflict labels / hidden unpublished parts / 320,390,1440px / concise normal state')
