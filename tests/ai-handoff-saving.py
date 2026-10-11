"""Do not leave before grading is durably saved, including manual handoff."""
import os,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async
ROOT=Path(__file__).resolve().parents[1];BASE=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
source=(ROOT/'src/storage/local.js').read_text().replace(' function write(state,options){',' function write(state,options){\n  if(globalThis.failLocalWrites)return Promise.reject(Error("simulated disk full"));\n  if(globalThis.pauseLocalWrites)return globalThis.pauseLocalWrites.then(()=>write(state,options));',1)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);context=browser.new_context(service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/src/storage/local.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=source));page.route('https://chatgpt.com/**',lambda r:r.fulfill(status=200,content_type='text/html',body='AI navigation fixture'))
 def begin(delay=True):
  page.goto(BASE);page.wait_for_function('document.querySelector("#main")?.getAttribute("aria-busy")==="false"');nav(page,'home');page.locator('.study-entrance').first.click();page.get_by_role('button',name='回答する',exact=True).wait_for();s=state(page);a=next(a for a in s['attempts'] if a['id']==s['currentId']);page.get_by_role('radio').nth(a['questionSnapshot']['answer']).check();state(page)
  if delay:page.evaluate('()=>{globalThis.pauseLocalWrites=new Promise(resolve=>{globalThis.finishSave=()=>{globalThis.pauseLocalWrites=null;resolve()}})}')
  else:page.evaluate('globalThis.failLocalWrites=true')
  page.locator('[data-action=submit]').click();page.locator('[data-action=ask-ai]').click();page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:async value=>{globalThis.copiedQuestion=value}}})');return a['id']
 def returned(id):
  page.go_back();page.locator('[data-action=ask-ai]').wait_for();s=state(page);a=next(a for a in s['attempts'] if a['id']==id);assert a['status']=='correct' and a['completedAt'] and a['selected']==a['questionSnapshot']['answer'];assert s['currentId']==id
 # A fast clipboard must not bypass a slow IndexedDB save.
 id=begin();page.locator('#ai-handoff-open').click();page.wait_for_function('Boolean(globalThis.copiedQuestion)');assert page.url.startswith(BASE);assert page.locator('#ai-handoff-open').is_disabled();assert '保存を確認' in page.locator('#ai-handoff-status').inner_text();page.evaluate('globalThis.finishSave()');page.wait_for_url('https://chatgpt.com/');returned(id)
 # Dismissing while save completes keeps the answer, without a late redirect.
 id=begin();page.locator('#ai-handoff-open').click();page.wait_for_function('Boolean(globalThis.copiedQuestion)');page.keyboard.press('Escape');page.locator('[data-action=ask-ai]').click();page.evaluate('globalThis.finishSave()');wait_for_async(page,'async()=>document.querySelector("#save-state").textContent.includes("保存済み")');assert page.url.startswith(BASE) and page.locator('#ai-handoff-dialog').is_visible();page.locator('#ai-handoff-close').click();assert next(a for a in state(page)['attempts'] if a['id']==id)['status']=='correct'
 # A failed write keeps the page and gives recovery guidance. Retrying can save.
 id=begin(False);page.locator('#ai-handoff-open').click();page.locator('#ai-handoff-manual:visible').wait_for();assert page.url.startswith(BASE);assert '学習記録を保存できなかった' in page.locator('#ai-handoff-status').inner_text();page.evaluate('globalThis.failLocalWrites=false');page.locator('#ai-handoff-open').click();page.wait_for_url('https://chatgpt.com/');returned(id)
 # The manual fallback link has the same save barrier, even without clipboard.
 id=begin();page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:async()=>{throw new DOMException("blocked","NotAllowedError")}}})');page.locator('#ai-handoff-open').click();page.locator('#ai-handoff-manual:visible').wait_for();page.locator('#ai-handoff-fallback').click();assert page.url.startswith(BASE);assert '保存を確認' in page.locator('#ai-handoff-status').inner_text();page.evaluate('globalThis.finishSave()');page.wait_for_url('https://chatgpt.com/');returned(id)
 assert not errors,errors;browser.close()
print('PASS delayed local save before AI / cancel during save preserves answer / failed save stays and retry succeeds / manual fallback save barrier')
