"""Real question snapshots, qualification routes and offline AI copy."""
import json,os,shutil
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
bank={q['id']:q for q in json.loads((ROOT/'data/questions.json').read_text())}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE);page.locator('.quick-start').wait_for()
 def open_q(id):
  q=bank[id];nav(page,'materials');page.locator('[data-action=reset-filters]').click();page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title']);page.locator(f'[data-action=start][data-id="{id}"]').click();page.get_by_role('button',name='回答する',exact=True).wait_for();assert page.locator('[data-action=ask-ai]').count()==0
 def ask():
  page.locator('[data-action=ask-ai]').click();page.locator('#ai-handoff-dialog').wait_for();return page.locator('#ai-handoff-preview').input_value()
 def close():page.locator('#ai-handoff-close').click()
 for status in ['correct','assisted','incorrect','revealed']:
  open_q('r04h-q4');q=bank['r04h-q4']
  if status=='assisted':page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
  if status=='revealed':page.locator('[data-action=reveal]').click()
  else:
   page.get_by_role('radio').nth((q['answer']+1)%4 if status=='incorrect' else q['answer']).check();page.locator('[data-action=submit]').click()
  page.locator('[data-action=ask-ai]').wait_for();saved=state(page);attempt=next(a for a in saved['attempts'] if a['id']==saved['currentId']);assert attempt['status']==status
  prompt=ask();assert q['stem'] in prompt and attempt['materialSnapshot']['explanation'] in prompt
  if attempt['selected'] is not None:assert '【私の回答】\n\n'+q['choices'][attempt['selected']]['label']+'：' in prompt
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert page.locator('#ai-handoff-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
  close();after=state(page);a=next(a for a in after['attempts'] if a['id']==attempt['id']);assert all(a[k]==attempt[k] for k in ['status','selected','hintCount','hintsBeforeAnswer','hintEvents','questionSnapshot','materialSnapshot'])
 page.set_viewport_size({'width':390,'height':844});open_q('r05h-q1');page.locator('[data-action=reveal]').click();text=ask();assert '原文の文字起こしは確認できていません' in text
 assert not bank['r05h-q1'].get('searchText') or bank['r05h-q1']['searchText'] not in text
 base=page.evaluate('document.baseURI');expected={urljoin(base,s) for s in bank['r05h-q1']['sourceImages']}
 assert expected <= set(page.locator('#ai-handoff-images a').evaluate_all('(links)=>links.map(a=>a.href)'));close()
 page.goto(urljoin(BASE,'ap/'));page.wait_for_function('document.querySelector("#main")?.getAttribute("aria-busy")==="false"');open_q('r05a-q17');page.locator('[data-action=reveal]').click();text=ask()
 assert bank['r05a-q17']['choices'][0]['text'] in text
 links=page.locator('#ai-handoff-images a').evaluate_all('(links)=>links.map(a=>a.href)');assert all('/ap/assets/' not in link for link in links)
 base=page.evaluate('document.baseURI');assert urljoin(base,bank['r05a-q17']['image']) in links;close()
 wait_for_async(page,'async()=>{await navigator.serviceWorker.ready;return Boolean(navigator.serviceWorker.controller)}')
 wait_for_async(page,'async()=>Boolean(await caches.match(new URL("src/features/ai-handoff.js",document.baseURI).href))')
 context.set_offline(True);page.reload();page.locator('[data-action=ask-ai]').wait_for();text=ask();assert bank['r05a-q17']['stem'] in text
 page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:async value=>{window.copiedOfflineAI=value}}})');page.locator('#ai-handoff-prompt-details>summary').click();page.locator('#ai-handoff-copy-only').click();page.wait_for_function('Boolean(window.copiedOfflineAI)');assert page.evaluate('window.copiedOfflineAI')==text;close()
 context.set_offline(False)
 unsupported=page.evaluate('''async()=>{
 const {loadCatalog}=await import(new URL('src/content/catalog.js',document.baseURI)),catalog=await loadCatalog('ap');
 const {createAssessment}=await import(new URL('src/domain/diagnostic.js',document.baseURI)),{createPlanningViews}=await import(new URL('src/ui/planning.js',document.baseURI));
 const run=createAssessment([await catalog.ensure('r04h-q4')],catalog.manifest),views=createPlanningViews({qualification:catalog.manifest,documents:[{id:run.id,kind:'diagnostic',payload:run}],attempts:[],currentRunId:run.id});
 return views.diagnosticHTML();
 }''');assert 'data-action="ask-ai"' not in unsupported and 'ヒントを' not in unsupported
 assert not errors,errors;browser.close()
print('PASS AI handoff real correct/assisted/incorrect/revealed snapshots / 320-1280px / image-only and grouped tables / qualification base URL / offline copy / diagnostic unaided')
