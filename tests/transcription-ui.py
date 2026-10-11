"""Reviewed text in actual practice, diagnostic renderer and offline resume."""
import json,os,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async

ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
bank={q['id']:q for q in json.loads((ROOT/'data/questions.json').read_text())}
records=[r for file in sorted((ROOT/'data/transcriptions').glob('*.json')) for r in json.loads(file.read_text())]
selected=set(os.environ.get('AP_TRANSCRIPTION_IDS','').split(','))-{''}
if selected:
 assert selected<={r['id'] for r in records}, 'Unreviewed ID requested'
 records=[r for r in records if r['id'] in selected]
artifacts=Path('/workspace/scratch/transcription-ui');artifacts.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.locator('.quick-start').wait_for()
 def open_q(id):
  nav(page,'materials');page.locator('[data-action=reset-filters]').click();q=bank[id]
  page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title'])
  page.locator(f'[data-action=start][data-id="{id}"]').click();page.get_by_role('button',name='回答する',exact=True).wait_for();state(page)
 def fits():
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),page.viewport_size
  assert page.locator('.math-error').count()==0
  assert page.locator('.choices input').count()==4
  assert page.locator('.question-panel .question-stem').count()==1
 for record in records:
  open_q(record['id']);fits()
  current=next(a for a in state(page)['attempts'] if a['id']==state(page)['currentId'])
  assert current['questionSnapshot']['stem']==record['stem']
  assert page.locator('.original-question').count()==1
 # Reviewed image-retention decisions leave the original question usable.
 for entry in json.loads((ROOT/'data/transcription-image-retentions.json').read_text()):
  open_q(entry['id'])
  assert page.locator('.question-panel .question-stem').count()==0
  page.wait_for_function('[...document.querySelectorAll(".source-question img")].every(img=>img.complete&&img.naturalWidth>0)')
  assert page.locator('.source-question img').count()==len(bank[entry['id']]['sourceImages'])
  assert page.locator('.choices input').count()==4
 for width in [320,780,1280]:
  page.set_viewport_size({'width':width,'height':900})
  for id in ['r04h-q1','r04h-q4','r06h-q2','r06h-q8','r07h-q1','r07h-q6','r07h-q7','r07h-q8']:
   open_q(id);fits()
 page.set_viewport_size({'width':390,'height':844});open_q('r04h-q1');assert page.locator('.question-stem u').inner_text()=='発生しないもの'
 page.screenshot(path=str(artifacts/'fraction-and-subscripts.png'),full_page=True)
 open_q('r04h-q4');page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').nth(0).check();before=state(page)
 page.reload();page.get_by_role('button',name='回答する',exact=True).wait_for();assert page.get_by_role('radio').nth(0).is_checked();assert page.locator('.hint-box').count()==1
 page.get_by_role('button',name='回答する',exact=True).click();assert page.locator('.result').count()==1
 page.locator('.result details').filter(has=page.locator('.reason-list')).locator('summary').click();assert page.locator('.reason-list li').count()==4
 open_q('r06h-q8');assert page.locator('.choices table,.choices .choice-text').count()==0;assert page.locator('.question-figure img').count()==1;assert page.locator('.choices .choice-code').all_text_contents()==['ア','イ','ウ','エ']
 page.get_by_role('radio').nth(1).check();state(page);page.reload();page.get_by_role('button',name='回答する',exact=True).wait_for()
 assert page.get_by_role('radio').nth(1).is_checked() and page.locator('.choices table,.choices .choice-text').count()==0
 assert page.locator('.question-figure img').evaluate('(img)=>img.complete&&img.naturalWidth===938')
 page.evaluate('document.documentElement.style.fontSize="200%"');fits();page.evaluate('document.documentElement.style.fontSize=""')
 open_q('r07h-q6');assert page.locator('.choices img').count()==4
 page.locator('.original-question>summary').click();page.get_by_role('button',name='問題画像を拡大',exact=True).click();assert page.locator('#image-dialog').is_visible();page.keyboard.press('Escape')
 page.screenshot(path=str(artifacts/'tree-and-original.png'),full_page=True)
 # Exercise the same diagnostic renderer with reviewed real question snapshots.
 diagnostic=page.evaluate('''async()=>{
 const {loadCatalog}=await import('/src/content/catalog.js'),catalog=await loadCatalog('ap');
 const {createAssessment}=await import('/src/domain/diagnostic.js'),{createPlanningViews}=await import('/src/ui/planning.js');
 const questions=await Promise.all(['r07h-q1','r06h-q8'].map(id=>catalog.ensure(id)));
 const run=createAssessment(questions,catalog.manifest),views=createPlanningViews({qualification:catalog.manifest,documents:[{id:run.id,kind:'diagnostic',payload:run}],attempts:[],currentRunId:run.id});
 return views.diagnosticHTML();
 }''')
 assert 'class="katex"' in diagnostic and '$((P' not in diagnostic and 'ヒントを' not in diagnostic and 'class="result"' not in diagnostic
 grouped_diagnostic=page.evaluate('''async()=>{
 const {loadCatalog}=await import('/src/content/catalog.js'),catalog=await loadCatalog('ap');
 const {createAssessment}=await import('/src/domain/diagnostic.js'),{createPlanningViews}=await import('/src/ui/planning.js');
 const run=createAssessment([await catalog.ensure('r06h-q8')],catalog.manifest);
 const views=createPlanningViews({qualification:catalog.manifest,documents:[{id:run.id,kind:'diagnostic',payload:run}],attempts:[],currentRunId:run.id});
 const node=document.createElement('div');node.innerHTML=views.diagnosticHTML();
 return {choices:[...node.querySelectorAll('.choice-code')].map(el=>el.textContent),tables:node.querySelectorAll('.choices table,.choices .choice-text').length,image:node.querySelector('.question-figure img')?.getAttribute('src'),hint:node.textContent.includes('ヒントを')};
 }''')
 assert grouped_diagnostic['choices']==['ア','イ','ウ','エ'] and grouped_diagnostic['tables']==0 and not grouped_diagnostic['hint'],grouped_diagnostic
 assert grouped_diagnostic['image'].endswith('r06h-q8-figure-and-choices.webp'),grouped_diagnostic
 # Core math assets and current question/figures/original survive no network.
 wait_for_async(page,'async()=>{await navigator.serviceWorker.ready;return Boolean(navigator.serviceWorker.controller)}')
 context.set_offline(True);page.reload();page.get_by_role('button',name='回答する',exact=True).wait_for();fits()
 page.locator('.original-question>summary').click();assert page.locator('.original-question img').evaluate('(img)=>img.complete&&img.naturalWidth>0')
 assert page.locator('.choices img').evaluate_all('(imgs)=>imgs.every(img=>img.complete&&img.naturalWidth>0)')
 assert page.locator('.choices .katex').count()==0
 assert not errors,errors
 context.set_offline(False);open_q('r06h-q2');context.set_offline(True);page.reload();page.get_by_role('button',name='回答する',exact=True).wait_for();assert page.locator('.katex .mfrac').count()==4;fits()
 assert page.evaluate('document.fonts.check("16px KaTeX_Main")')
 assert not errors,errors
 browser.close()
print(f'PASS {len(records)} actual questions / 320-1280px / 200% / math-table-figures / hints-choice resume / four reasons / diagnostic math unaided / offline original and fonts')
