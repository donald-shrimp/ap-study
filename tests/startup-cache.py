"""Warm startup restores checkpoints while every server response is stalled."""
import functools,shutil,threading,time
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import state
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.server.block:self.server.release.wait(12)
  try:super().do_GET()
  except (BrokenPipeError,ConnectionResetError):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));server.block=False;server.release=threading.Event();threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/ap-study/'
TRACE='''(()=>{window.startupFrames=[];new MutationObserver(()=>{const m=document.getElementById('main');if(!m)return;const v=m.querySelector('.loading')?'loading':m.querySelector('.written-layout')?'written':m.querySelector('.question-panel')?'study':m.querySelector('.quick-start,.study-entry')?'home':'other';if(startupFrames.at(-1)!==v)startupFrames.push(v)}).observe(document,{childList:true,subtree:true})})()'''
def ready(pg):pg.wait_for_function('document.getElementById("main")?.getAttribute("aria-busy")==="false" && !document.getElementById("main").inert',timeout=4000)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  for target in ['ap/?part=objective','ap/?part=written','ab730/']:
   ctx=b.new_context(viewport={'width':390,'height':844});ctx.add_init_script(TRACE);pg=ctx.new_page();errors=[];ctx.on('page',lambda page:page.on('pageerror',lambda e:errors.append(str(e))));pg.goto(BASE+target);pg.locator('.quick-start,.study-entry').wait_for();pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller')
   # All qualification HTML belongs to the installed release, not the network.
   assert pg.evaluate('''async()=>{const names=await caches.keys(),shell=await caches.open(names.find(n=>n.includes('shell-'))),root=new URL('.',document.baseURI);return !!(await shell.match(new URL('ap/index.html',root)))&&!!(await shell.match(new URL('ab730/index.html',root)));}''')
   written='written' in target
   if written:
    pg.locator('[data-action=written-start]').first.click();field=pg.locator('textarea[data-written-key]').first;field.fill('起動確認のテスト回答');pg.locator('[data-action=written-submit]').first.click();pg.wait_for_function('document.querySelector("textarea[data-written-key]")?.readOnly')
   else:
    pg.locator('.study-entrance[data-paper-mode=all]' if target.startswith('ap/') else '.study-entrance').click();pg.locator('[name=answer]').first.check();before=state(pg);assert next(a for a in before['attempts'] if a['id']==before['currentId'])['selected']==0
   server.block=True;server.release.clear();pg.close();pg=ctx.new_page();start=time.monotonic();pg.goto(BASE+target,wait_until='commit',timeout=4000);ready(pg);elapsed=time.monotonic()-start
   if written:assert pg.locator('textarea[data-written-key]').first.input_value()=='起動確認のテスト回答';expected='written'
   else:assert pg.locator('[name=answer]').first.is_checked();assert state(pg)['currentId']==before['currentId'];expected='study'
   frames=pg.evaluate('startupFrames');assert expected in frames and 'home' not in frames,frames
   assert not errors,errors;print('PASS stalled network + saved checkpoint + no home flash:',target,round(elapsed,3),'s',flush=True)
   server.block=False;server.release.set();ctx.close()
  b.close()
finally:server.block=False;server.release.set();server.shutdown()
