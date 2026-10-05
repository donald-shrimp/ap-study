"""Exercise installation metadata, offline study, and a service-worker update.

A local server simulates a new release without touching repository files.
Use AP_STUDY_PWA_URL to also check a deployed site's offline behavior.
"""
import functools,json,os,shutil,tempfile,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
RELEASE=(ROOT/'sw.js').read_text().split("const RELEASE = '",1)[1].split("'",1)[0]
NEXT_RELEASE=RELEASE+'-test2'
ARTIFACTS=Path(tempfile.mkdtemp(prefix='ap-study-pwa-'))
KEY='ap-study-mock.v1'
bank=json.loads((ROOT/'data/questions.json').read_text());by_id={q['id']:q for q in bank}
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urlparse(self.path).path
  if self.server.upgraded and path in ['/ap-study/sw.js','/ap-study/index.html','/ap-study/','/ap-study/data/questions.json']:
   filename='index.html' if path.endswith('/') else path.rsplit('/',1)[-1]
   if filename=='questions.json':
    updated=json.loads(json.dumps(bank));updated[0]['summary']+='（更新確認）';body=json.dumps(updated,ensure_ascii=False).encode();kind='application/json'
   else:
    body=(ROOT/filename).read_text().replace(RELEASE,NEXT_RELEASE).encode();kind='application/javascript' if filename=='sw.js' else 'text/html'
   self.send_response(200);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Cache-Control','no-cache');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT.parent)));server.upgraded=False
threading.Thread(target=server.serve_forever,daemon=True).start()
URL=os.environ.get('AP_STUDY_PWA_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
with sync_playwright() as p:
 options={'executable_path':shutil.which('chromium'),'headless':True,'args':['--no-sandbox']}
 if URL.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 ctx=p.chromium.launch_persistent_context(str(ARTIFACTS/'profile'),**options,viewport={'width':390,'height':844});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def state():return page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',KEY)
 def nav(view):page.locator(f'.sidebar [data-view={view}]').click()
 def choose_q(id):
  nav('materials');page.locator('[data-action=reset-filters]').click();q=by_id[id]
  page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title'])
 def open_q(id):
  choose_q(id);page.locator(f'[data-action=start][data-id="{id}"]').click()
 page.goto(URL);page.locator('.quick-start').wait_for();page.evaluate('async()=>{await navigator.serviceWorker.ready}');page.wait_for_function('!!navigator.serviceWorker.controller')
 cdp=ctx.new_cdp_session(page);manifest=cdp.send('Page.getAppManifest');assert not manifest['errors'],manifest
 data=json.loads(manifest['data']);assert data['display']=='standalone' and data['name']=='ひと問'
 assert {x['sizes'] for x in data['icons']}=={'192x192','512x512'} and 'maskable' in data['icons'][1]['purpose']
 assert page.evaluate('navigator.serviceWorker.controller.scriptURL').endswith('/ap-study/sw.js')
 assert page.evaluate('async()=>{const r=await navigator.serviceWorker.ready;return r.scope}').endswith('/ap-study/')
 for icon in data['icons']:
  dimensions=page.evaluate('async path=>{const i=new Image();i.src=new URL(path,document.baseURI);await i.decode();return `${i.naturalWidth}x${i.naturalHeight}`}',icon['src']);assert dimensions==icon['sizes']
 installability=cdp.send('Page.getInstallabilityErrors');assert not installability['installabilityErrors'],installability
 print('PASS manifest / 192 and 512px icons / maskable / subdirectory scope',flush=True)
 open_q('r07h-q1');page.locator('.source-question img').evaluate('(img)=>img.decode()')
 page.wait_for_function('async()=>!!(await caches.match(new URL("assets/questions/r07h/r07h-q1.webp",document.baseURI)))')
 page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').nth(3).check();attempt=state()['currentId']
 pause=page.get_by_role('button',name='中断',exact=True)
 appearance=pause.evaluate('(el)=>{const s=getComputedStyle(el);return {border:s.borderTopStyle,color:s.borderTopColor,bg:s.backgroundColor,h:el.offsetHeight}}')
 assert appearance['border']=='solid' and appearance['bg']!='rgba(0, 0, 0, 0)' and appearance['h']>=44
 assert pause.locator('svg[aria-hidden=true]').count()==1
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path=str(ARTIFACTS/'pause-mobile.png'),full_page=True)
 ctx.set_offline(True);page.wait_for_function('!navigator.onLine');page.reload();page.locator('.hint-box').wait_for()
 assert state()['currentId']==attempt and page.get_by_role('radio').nth(3).is_checked() and state()['attempts'][-1]['hintCount']==1
 page.locator('.source-question img').evaluate('(img)=>img.decode()');assert page.locator('#offline-status').is_visible()
 page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='再開する',exact=True).click();assert state()['currentId']==attempt
 assert page.get_by_role('radio').nth(3).is_checked() and page.locator('.hint-box').count()==1
 # A missing image does not create an unreadable attempt or destroy the paused one.
 choose_q('r07h-q2');before=state();page.locator('[data-action=start][data-id=r07h-q2]').click();assert state()==before and '保存されていません' in page.locator('#notice').inner_text()
 nav('home');page.locator('.quick-start [data-count="1"]').click();assert state()['currentId']!=attempt
 assert page.locator('.image-error').count()==0
 page.reload();page.get_by_role('radio').first.wait_for();assert page.locator('.image-error').count()==0
 page.screenshot(path=str(ARTIFACTS/'offline-mobile.png'),full_page=True)
 print('PASS visible pause control / offline reload / images / selection and hint resume / cached-only picking / missing-image guard',flush=True)
 ctx.set_offline(False);page.reload();page.get_by_role('radio').first.wait_for();page.wait_for_function('navigator.onLine');open_q('r07h-q1');page.locator('.source-question img').evaluate('(img)=>img.decode()')
 page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').nth(2).check();before=state()
 if not os.environ.get('AP_STUDY_PWA_URL'):
  # An unrelated app cache must survive activation of our newer worker.
  page.evaluate('async()=>{const c=await caches.open("other-app-test");await c.put("/unrelated",new Response("keep"))}')
  server.upgraded=True
  updated=page.evaluate('async()=>{const r=await fetch("data/questions.json?v=refresh");return await r.json()}');assert '更新確認' in updated[0]['summary']
  page.evaluate('async()=>{const r=await navigator.serviceWorker.ready;await r.update()}')
  page.wait_for_function('async()=>!!(await navigator.serviceWorker.getRegistration()).waiting')
  # No automatic reload should interrupt an in-progress answer.
  assert state()['currentId']==before['currentId'] and page.get_by_role('radio').nth(2).is_checked()
  page.get_by_role('button',name='表示・データ',exact=True).click();page.locator('#update-app').wait_for(state='visible');page.locator('#update-app').click()
  page.locator('.hint-box').wait_for();page.wait_for_function('async()=>!(await navigator.serviceWorker.getRegistration()).waiting')
  assert state()['currentId']==before['currentId'] and page.get_by_role('radio').nth(2).is_checked() and page.locator('.hint-box').count()==1
  names=page.evaluate('async()=>await caches.keys()');assert 'other-app-test' in names and any(name.endswith('shell-'+NEXT_RELEASE) for name in names)
  assert not any(name.endswith('shell-'+RELEASE) for name in names)
  ctx.set_offline(True);page.reload();page.locator('.hint-box').wait_for();page.locator('.source-question img').evaluate('(img)=>img.decode()')
  assert state()['currentId']==before['currentId'];assert '更新確認' in page.evaluate('async()=>await(await fetch("data/questions.json")).json()')[0]['summary']
  print('PASS online bank freshness / update on request / record unchanged / old shell removed / other caches and saved images retained / offline new release',flush=True)
 assert not errors,errors
 ctx.close()
server.shutdown()
print('Artifacts:',ARTIFACTS)
