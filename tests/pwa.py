from browser_storage import nav as action_nav, open_plan_editor, open_plan_ai
"""Exercise installation metadata, offline study, and a service-worker update.

A local server simulates a new release without touching repository files.
Use AP_STUDY_PWA_URL to also check a deployed site's offline behavior.
"""
import functools,json,os,shutil,tempfile,threading,hashlib
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import state as stored_state, READ_STATE,wait_for_async
ROOT=Path(__file__).resolve().parents[1]
RELEASE=(ROOT/'sw.js').read_text().split("const RELEASE = '",1)[1].split("'",1)[0]
NEXT_RELEASE=RELEASE+'-test2'
ARTIFACTS=Path(tempfile.mkdtemp(prefix='ap-study-pwa-'))
KEY='ap-study-mock.v1'
bank=json.loads((ROOT/'data/questions.json').read_text());by_id={q['id']:q for q in bank}
PACK_ROOT=ROOT/'data/qualifications/ap'
CONTENT_MANIFEST=json.loads((PACK_ROOT/'manifest.json').read_text())
FIRST_PACK=CONTENT_MANIFEST['packs'][0]
UPDATED_PACK=json.loads((PACK_ROOT/FIRST_PACK['url']).read_text())
UPDATED_PACK[0]['summary']+='（更新確認）'
UPDATED_PACK_BODY=(json.dumps(UPDATED_PACK,ensure_ascii=False,separators=(',',':'))+'\n').encode()

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urlparse(self.path).path
  if self.server.upgraded and path in ['/ap-study/sw.js','/ap-study/index.html','/ap-study/','/ap-study/data/qualifications/ap/manifest.json','/ap-study/data/qualifications/ap/'+FIRST_PACK['url']]:
   filename='index.html' if path.endswith('/') else path.rsplit('/',1)[-1]
   if path.endswith(FIRST_PACK['url']):body=UPDATED_PACK_BODY;kind='application/json'
   elif filename=='manifest.json':
    updated=json.loads(json.dumps(CONTENT_MANIFEST));updated['packs'][0]['sha256']=hashlib.sha256(UPDATED_PACK_BODY).hexdigest();body=json.dumps(updated,ensure_ascii=False).encode();kind='application/json'
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
 def state():
  return stored_state(page)
 def nav(view):action_nav(page,view)
 def choose_q(id):
  nav('materials');page.locator('[data-action=reset-filters]').click();q=by_id[id]
  page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title'])
 def open_q(id):
  choose_q(id);page.locator(f'[data-action=start][data-id="{id}"]').click();page.wait_for_function('document.querySelector("#main").getAttribute("aria-busy")!=="true"')
 page.goto(URL);page.locator('.quick-start').wait_for();page.evaluate('async()=>{await navigator.serviceWorker.ready}');page.wait_for_function('!!navigator.serviceWorker.controller')
 cdp=ctx.new_cdp_session(page);manifest=cdp.send('Page.getAppManifest');assert not manifest['errors'],manifest
 data=json.loads(manifest['data']);assert data['display']=='standalone' and data['name']=='ひと問'
 # Unlike start_url, id is resolved against the origin, not the manifest URL.
 # "./" silently identifies the entire github.io host, not this Pages project.
 identity=cdp.send('Page.getAppId')
 expected_id=page.evaluate('new URL("./",document.baseURI).href')
 assert identity['appId']==expected_id,(identity,expected_id)
 assert {x['sizes'] for x in data['icons']}=={'192x192','512x512'} and 'maskable' in data['icons'][1]['purpose']
 assert page.evaluate('navigator.serviceWorker.controller.scriptURL').endswith('/ap-study/sw.js')
 assert page.evaluate('async()=>{const r=await navigator.serviceWorker.ready;return r.scope}').endswith('/ap-study/')
 for icon in data['icons']:
  dimensions=page.evaluate('async path=>{const i=new Image();i.src=new URL(path,document.baseURI);await i.decode();return `${i.naturalWidth}x${i.naturalHeight}`}',icon['src']);assert dimensions==icon['sizes']
 installability=cdp.send('Page.getInstallabilityErrors');assert not installability['installabilityErrors'],installability
 print('PASS manifest / project-specific app identity / 192 and 512px icons / maskable / subdirectory scope',flush=True)
 open_q('r07h-q1');page.locator('.source-question img').evaluate('(img)=>img.decode()')
 wait_for_async(page,'async()=>!!(await caches.match(new URL("assets/questions/r07h/r07h-q1.webp",document.baseURI)))')
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
 page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='続きから',exact=True).click();assert state()['currentId']==attempt
 assert page.get_by_role('radio').nth(3).is_checked() and page.locator('.hint-box').count()==1
 # Navigating during the debounced scroll save must preserve the study position.
 page.evaluate('window.scrollTo(0,400)')
 wait_for_async(page,'async()=>{const s=await ('+READ_STATE+')();return window.scrollY>0&&s.attempts.find(a=>a.id===s.currentId).scrollY===window.scrollY;}')
 assert state()['attempts'][-1]['scrollY']>0
 page.evaluate('window.dispatchEvent(new Event("scroll"))');nav('materials')
 before=state();page.wait_for_timeout(300);assert state()==before,'Leaving study overwrote its saved scroll position'
 # A missing image does not create an unreadable attempt or destroy the paused one.
 choose_q('r07h-q2');before=state();page.locator('[data-action=start][data-id=r07h-q2]').click();after=state()
 if after!=before:
  changed={key:[before.get(key),after.get(key)] for key in before if before.get(key)!=after.get(key)}
  if 'attempts' in changed:
   changed['attempts']=[{key:[old.get(key),new.get(key)] for key in old if old.get(key)!=new.get(key)} for old,new in zip(before['attempts'],after['attempts'])]
  raise AssertionError(f'Offline guard changed record: {changed}')
 assert '保存されていません' in page.locator('#notice').inner_text(),page.locator('#notice').inner_text()
 nav('home');page.locator('.hero-start [data-action=start-session]').click();assert state()['currentId']!=attempt
 assert page.locator('.image-error').count()==0
 page.reload();page.get_by_role('radio').first.wait_for();assert page.locator('.image-error').count()==0
 page.screenshot(path=str(ARTIFACTS/'offline-mobile.png'),full_page=True)
 print('PASS visible pause control / offline reload / images / selection and hint resume / scroll preserved on navigation / cached-only picking / missing-image guard',flush=True)
 ctx.set_offline(False);page.reload();page.get_by_role('radio').first.wait_for();page.wait_for_function('navigator.onLine');open_q('r07h-q1');page.locator('.source-question img').evaluate('(img)=>img.decode()')
 page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').nth(2).check();before=state()
 if not os.environ.get('AP_STUDY_PWA_URL'):
  # An unrelated app cache must survive activation of our newer worker.
  page.evaluate('async()=>{const c=await caches.open("other-app-test");await c.put("/unrelated",new Response("keep"))}')
  server.upgraded=True
  updated=page.evaluate('async()=>{const url=new URL("data/qualifications/ap/manifest.json",document.baseURI);const m=await(await fetch(url)).json();return await(await fetch(new URL(m.packs[0].url,url))).json();}');assert '更新確認' in updated[0]['summary']
  page.evaluate('async()=>{const r=await navigator.serviceWorker.ready;await r.update()}')
  wait_for_async(page,'async()=>!!(await navigator.serviceWorker.getRegistration()).waiting')
  # No automatic reload should interrupt an in-progress answer.
  assert state()['currentId']==before['currentId'] and page.get_by_role('radio').nth(2).is_checked()
  page.get_by_role('button',name='表示・データ',exact=True).click();page.locator('#update-app').wait_for(state='visible')
  with page.expect_navigation(wait_until='load'):
   page.locator('#update-app').click()
  page.locator('.hint-box').wait_for();wait_for_async(page,'async()=>!(await navigator.serviceWorker.getRegistration()).waiting')
  assert state()['currentId']==before['currentId'] and page.get_by_role('radio').nth(2).is_checked() and page.locator('.hint-box').count()==1
  names=page.evaluate('async()=>await caches.keys()');assert 'other-app-test' in names and any(name.endswith('shell-'+NEXT_RELEASE) for name in names)
  assert not any(name.endswith('shell-'+RELEASE) for name in names)
  ctx.set_offline(True);page.reload();page.locator('.hint-box').wait_for();page.locator('.source-question img').evaluate('(img)=>img.decode()')
  assert state()['currentId']==before['currentId'];assert '更新確認' in page.evaluate('async()=>{const url=new URL("data/qualifications/ap/manifest.json",document.baseURI);const m=await(await fetch(url)).json();return await(await fetch(new URL(m.packs[0].url,url))).json();}')[0]['summary']
  print('PASS online bank freshness / update on request / record unchanged / old shell removed / other caches and saved images retained / offline new release',flush=True)
 assert not errors,errors
 ctx.close()
server.shutdown()
print('Artifacts:',ARTIFACTS)
