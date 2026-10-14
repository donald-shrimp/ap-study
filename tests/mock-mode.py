"""Fixed 80-question mock UI, snapshots, offline resume, results and record routes."""
import json,os,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async
URL=os.getenv('HITOMON_TEST_URL','http://127.0.0.1:4173/ap/')
ROOT=Path(__file__).resolve().parents[1];ART=Path('/workspace/scratch/mock-mode');ART.mkdir(exist_ok=True)
READ='''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:'ap',rootPath:root.pathname});try{const identity=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),w=createWorkspaceStore({...identity,rootPath:root.pathname,validate:(k,p)=>p});try{return await w.read();}finally{await w.close();}}finally{await s.close();}}'''
def rows(page):return page.evaluate(READ)
def run(page):return next(r['payload'] for r in rows(page) if r['kind']=='mock')
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write']);page=ctx.new_page();page.set_default_timeout(60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
 page.goto(URL);page.locator('.home-assessments [data-view=mocks]').wait_for();assert page.locator('.study-entrance').count()==3
 page.locator('.home-assessments [data-view=mocks]').click();page.get_by_role('heading',name='模試を選ぶ',exact=True).wait_for();assert page.locator('.mock-set').count()==2
 assert page.locator('.mock-previous').count()==0;page.screenshot(path=str(ART/'selection.png'),full_page=True)
 page.locator('[data-mock-set=ap-mock-a] [data-action=start-mock]').click();page.get_by_text('模試 A 1 / 80問',exact=True).wait_for()
 initial=run(page);frozen=json.dumps(initial['slots'],sort_keys=True);expected=json.loads((ROOT/'content/ap/mock-sets.json').read_text())['sets'][0]['slots'];assert [s['attempt']['questionId'] for s in initial['slots']]==[s['questionId'] for s in expected]
 for i,slot in enumerate(initial['slots']):
  q=slot['attempt']['questionSnapshot'];assert page.locator('.hint-section,.result,.correct-choice,.reason-list').count()==0
  answer=q['correctChoiceId'] if i<60 else next(c['id'] for c in q['choices'] if c['id']!=q['correctChoiceId'])
  page.locator(f'[name=diagnostic-answer][value="{answer}"]').check()
  if i==2:
   page.get_by_role('button',name='中断',exact=True).click();wait_for_async(page,'async()=>{const r=await ('+READ+')();return r.some(r=>r.kind==="mock"&&r.payload.currentChoiceId!==null)}')
   page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener("controllerchange",r,{once:true}));}')
   ctx.set_offline(True);page.reload();page.locator('.home-assessments [data-view=mocks]').click();page.locator('[data-mock-set=ap-mock-a]').get_by_role('button',name='続きから',exact=True).click();page.get_by_text('模試 A 3 / 80問',exact=True).wait_for()
   assert page.locator(f'[name=diagnostic-answer][value="{answer}"]').is_checked();assert json.dumps(run(page)['slots'],sort_keys=True)==frozen
  page.get_by_role('button',name='未回答で次へ' if i==70 else '回答して結果へ' if i==79 else '回答して次へ',exact=True).click()
  if i<79:page.get_by_text(f'模試 A {i+2} / 80問',exact=True).wait_for()
 page.get_by_role('heading',name='模試 Aの結果',exact=True).wait_for();assert '正答率：75% · 60 / 80問正解' in page.locator('#main').inner_text();assert page.locator('.diagnostic-review').count()==80
 page.locator('.diagnostic-review').first.locator('summary').click();assert page.locator('.diagnostic-review').first.locator('.reason-list li').count()==4
 assert state(page)['attempts']==[];ctx.set_offline(False);page.screenshot(path=str(ART/'result.png'),full_page=True)
 page.get_by_role('button',name='結果と学習状況をAIへ渡す',exact=True).click();page.get_by_role('button',name='学習状況JSONをコピー',exact=True).click();page.get_by_text('コピーしました。',exact=True).wait_for();summary=json.loads(page.evaluate('navigator.clipboard.readText()'));assert summary['learningByPart'][0]['all']['completedAttempts']==0 and summary['diagnostics']==[] and len(summary['mockExams'])==1 and summary['mockExams'][0]['scoreRate']==.75
 nav(page,'history');page.get_by_role('button',name='模試結果',exact=True).click();page.locator('[data-mock-set=ap-mock-a] [data-action=mock-records]').click();page.get_by_role('button',name='結果を見る',exact=True).click();page.get_by_role('heading',name='模試 Aの結果',exact=True).wait_for()
 page.get_by_role('button',name='この模試の記録へ',exact=True).click();page.get_by_role('heading',name='模試 Aの記録',exact=True).wait_for();assert '75% · 60 / 80問正解' in page.locator('#main').inner_text()
 page.get_by_role('button',name='模試結果の一覧へ',exact=True).click();assert page.locator('[data-mode=mock][aria-pressed=true]').count()==1;assert '前回：75%' in page.locator('[data-mock-set=ap-mock-a]').inner_text()
 page.locator('[data-mock-set=ap-mock-a] [data-action=mock-records]').click();page.get_by_role('button',name='もう一度受ける',exact=True).click();page.get_by_text('模試 A 1 / 80問',exact=True).wait_for();rs=[r['payload'] for r in rows(page) if r['kind']=='mock'];assert len(rs)==2 and len({r['id'] for r in rs})==2;assert len({tuple(s['attempt']['questionId'] for s in r['slots']) for r in rs})==1
 page.get_by_role('button',name='中断',exact=True).click();nav(page,'history');page.locator('[data-action=field-mode][data-mode=mock]').click();page.locator('[data-mock-set=ap-mock-b] [data-action=mock-records]').click();page.get_by_role('heading',name='模試 Bの記録',exact=True).wait_for();assert 'まだ受けていません。' in page.locator('#main').inner_text()
 nav(page,'history');assert page.locator('.overall-rate').inner_text()=='未確認';page.get_by_role('button',name='診断結果',exact=True).click();assert '完了した診断はありません' in page.locator('#main').inner_text()
 nav(page,'home');page.locator('.home-assessments [data-view=mocks]').click();assert '前回：75%' in page.locator('[data-mock-set=ap-mock-a]').inner_text()
 page.evaluate('document.documentElement.classList.add("large-text")');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(ART/'selection-completed.png'),full_page=True)
 assert not errors,errors;b.close()
print('PASS fixed80 / unaided / 60 correct+19 incorrect+1 skipped / 75% denominator80 / offline selected answer and frozen resume / 80 explanations / repeated IDs / per-set record tabs / no ordinary or diagnostic pollution / mobile and 200%')
