"""Real SW: saved diagrams remain usable while online requests stall."""
import json,shutil,threading,time
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import wait_for_async
ROOT=Path(__file__).resolve().parents[1];gates={}
FRESH='<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><title>fresh</title></svg>'
SAVED=FRESH.replace('fresh','saved')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/probe':body=b'<html><body></body></html>';kind='text/html'
  elif path.startswith('/assets/review-'):
   gates[path].wait(10);body=FRESH.encode();kind='image/svg+xml'
  else:return super().do_GET()
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/'
FETCH='''async ({path,cache='default'})=>{const start=performance.now(),r=await fetch(path,{cache}),text=await r.text();return {elapsedMs:Math.round(performance.now()-start),text,offline:r.headers.get('X-Hitomon-Offline')};}'''
results={}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context();pg=ctx.new_page();pg.goto(BASE+'probe');pg.evaluate('async()=>{await navigator.serviceWorker.register("/sw.js");await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener("controllerchange",ok,{once:true}));}')
  def prepare(name,saved=True):
   path='/assets/review-'+name+'.svg';gates[path]=threading.Event()
   if saved:pg.evaluate('async({path,text})=>{await(await caches.open("hitomon-/images")).put(new URL(path,location.href),new Response(text,{headers:{"Content-Type":"image/svg+xml"}}));}',{'path':path,'text':SAVED})
   return path
  path=prepare('stalled');r=pg.evaluate(FETCH,{'path':path});assert r['text']==SAVED and r['elapsedMs']<900,r;results['stalledCachedMs']=r['elapsedMs'];gates[path].set()
  wait_for_async(pg,'async()=>{const r=await(await caches.open("hitomon-/images")).match(new URL('+json.dumps(path)+',location.href));return r&&(await r.text()).includes("fresh");}')
  path=prepare('fast');gates[path].set();assert pg.evaluate(FETCH,{'path':path})['text']==FRESH
  path=prepare('reload');threading.Timer(1.2,gates[path].set).start();r=pg.evaluate(FETCH,{'path':path,'cache':'reload'});assert r['text']==FRESH and r['elapsedMs']>=800,r;results['explicitReloadMs']=r['elapsedMs']
  path=prepare('missing',saved=False);threading.Timer(1.2,gates[path].set).start();r=pg.evaluate(FETCH,{'path':path});assert r['text']==FRESH and r['elapsedMs']>=800,r
  ctx.set_offline(True);r=pg.evaluate(FETCH,{'path':path});assert r['text']==FRESH and r['offline']=='1';assert pg.evaluate('async()=>{try{await fetch("/assets/review-absent.svg");return false;}catch{return true;}}');b.close()
finally:
 for gate in gates.values():gate.set()
 server.shutdown()
print('PASS stalled saved image fallback / fast fresh image / background refresh / explicit SHA download / cache miss / offline failure:',results)
