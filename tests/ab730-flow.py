"""Real AB-730 authored bank in the shared app: mixed choices, diagnosis, backup."""
import json,os,shutil,tempfile,collections
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async,open_data_management,open_plan_ai
ROOT=Path(__file__).resolve().parents[1];URL=os.environ.get('HITOMON_TEST_URL','http://127.0.0.1:4173/');bank=json.loads((ROOT/'content/ab730/questions.json').read_text());byid={q['id']:q for q in bank};artifacts=Path(tempfile.mkdtemp(prefix='hitomon-ab730-flow-'))
READ_RUNS='''async()=>{const {createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:'ab730',rootPath:'/'});try{const identity=await s.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...identity,rootPath:'/',validate:(k,p)=>p});try{return await w.read();}finally{await w.close();}}finally{await s.close();}}'''
def run(page):return next(r['payload'] for r in page.evaluate(READ_RUNS) if r['kind']=='diagnostic')
def close_settings(page):page.get_by_role('button',name='設定を閉じる',exact=True).click()
def current(page):s=state(page);return next(a for a in s['attempts'] if a['id']==s['currentId'])
def choose_correct(page,q,name='answer'):
 ids=q.get('correctChoiceIds') or [q['correctChoiceId']]
 for id in ids:
  value=str(next(i for i,c in enumerate(q["choices"]) if c["id"]==id)) if name=="answer" else id
  page.locator(f'[name="{name}"][value="{value}"]').check()
with sync_playwright() as p:
 options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'localhost,127.0.0.1'}
 browser=p.chromium.launch(**options);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(15000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
 page.goto(URL);page.get_by_role('heading',name='資格・科目を選ぶ').wait_for();page.locator('.qualification-option').filter(has_text='AB-730').click();page.locator('.quick-start').wait_for()
 assert page.locator('#qualification-switch').inner_text().strip().startswith('AB-730')
 assert page.locator('.study-entrance').count()==1 and page.locator('[data-action=cards-open],[data-view=mocks]').count()==0
 page.locator('.study-entrance').click();page.locator('[name=answer]').first.wait_for();a=current(page);assert a['qualificationId']=='ab730';q=a['questionSnapshot'];choose_correct(page,q);page.locator('[data-action=submit]').click();page.locator('#result-heading').wait_for();assert current(page)['status']=='correct'
 page.locator('[data-action=ask-ai]').click();prompt=page.locator('#ai-handoff-preview').input_value();assert q['stem'] in prompt and all(c['text'] in prompt for c in q['choices']) and 'Microsoft公式資料確認版' in prompt;page.locator('#ai-handoff-close').click()
 def open_q(q):
  nav(page,'materials');page.locator('[data-action=reset-filters]').click();assert page.locator('[name=year],[name=season]').count()==0
  page.locator('[name=query]').fill(q['title']);button=page.locator(f'[data-action=start][data-id="{q["id"]}"]');assert button.count()==1,q['id'];button.click();page.locator('[name=answer]').first.wait_for();assert current(page)['questionId']==q['id']
 multis=[q for q in bank if q['type']=='multipleChoice']
 for i,q in enumerate(multis):
  open_q(q);assert page.locator('[name=answer][type=radio]').count()==0 and page.locator('[name=answer]').count()==len(q['choices'])
  assert page.locator('[data-action=hint],.hint-section').count()==0
  if i==0:
   id=str(next(j for j,c in enumerate(q['choices']) if c['id']==q['correctChoiceIds'][0]));page.locator(f'[name=answer][value="{id}"]').check();before=current(page);page.reload();page.locator('[name=answer]').first.wait_for();assert current(page)['selectedChoiceIds']==before['selectedChoiceIds'];assert page.locator(f'[name=answer][value="{id}"]').is_checked()
  for width in [320,390,1280]:page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),q['id']
  choose_correct(page,q);page.locator('[data-action=submit]').click();page.locator('#result-heading').wait_for();assert current(page)['status']=='correct';page.locator('.result details').filter(has=page.locator('.reason-list')).locator('summary').click();assert page.locator('.reason-list li').count()==len(q['choices'])
 page.set_viewport_size({'width':390,'height':844});nav(page,'topics');assert page.locator('.topic-card').count()==4;page.locator('.topic-card').first.locator('[data-action=field-practice]').click();page.locator('[name=answer]').first.wait_for();assert state(page)['session']['topicId'] in {q['topicId'] for q in bank}
 nav(page,'home');ordinary=len(state(page)['attempts']);page.locator('.home-assessments [data-view=diagnostics]').click();page.get_by_role('button',name='30問の診断をはじめる',exact=True).click();page.locator('[name=diagnostic-answer]').first.wait_for();r=run(page);assert len(r['slots'])==30 and len({s['attempt']['questionId'] for s in r['slots']})==30
 counts=collections.Counter(s['attempt']['questionSnapshot']['topicId'] for s in r['slots']);assert set(counts.values())=={7,8} and len(counts)==4
 frozen=json.dumps(r['slots'],sort_keys=True)
 q=r['slots'][0]['attempt']['questionSnapshot'];first=(q.get('correctChoiceIds') or [q['correctChoiceId']])[0];page.locator(f'[name=diagnostic-answer][value="{first}"]').check();page.locator('[data-action=pause-diagnostic]').click();page.reload();page.locator('.home-assessments [data-action=resume-diagnostic]').click();page.locator('[name=diagnostic-answer]').first.wait_for();assert page.locator(f'[name=diagnostic-answer][value="{first}"]').is_checked();assert json.dumps(run(page)['slots'],sort_keys=True)==frozen
 for i in range(30):
  r=run(page);assert r['currentIndex']==i;q=r['slots'][i]['attempt']['questionSnapshot'];assert page.locator('[data-action=hint],[data-action=ask-ai],.hint-section,.result').count()==0
  choose_correct(page,q,'diagnostic-answer');page.locator('[data-action=submit-diagnostic]').click()
  if i<29:page.get_by_text(f'診断 {i+2} / 30問',exact=True).wait_for()
 page.get_by_role('heading',name='診断結果',exact=True).wait_for();assert run(page)['status']=='completed' and len(run(page)['responses'])==30;assert len(state(page)['attempts'])==ordinary
 # AI summary and portable backup preserve actual mixed-format question snapshots.
 nav(page,'home');page.locator('.planning-entry [data-view=planning]').click();open_plan_ai(page)
 with page.expect_download() as download:page.locator('[data-action=export-summary]').click()
 summary_path=artifacts/'summary.json';download.value.save_as(summary_path);summary=json.loads(summary_path.read_text());assert 'ab730' in json.dumps(summary) and 'diagnostic' in json.dumps(summary)
 open_data_management(page)
 with page.expect_download() as download:page.locator('#export-state').click()
 backup_path=artifacts/'backup.json';download.value.save_as(backup_path);backup=json.loads(backup_path.read_text());assert len(backup['records'])==ordinary and any(a['material']['type']=='multipleChoice' and a['response']['choiceIds'] for a in backup['records']);assert backup['workspaceBackup']['runs'][0]['size']==30
 restored_context=browser.new_context(viewport={'width':390,'height':844});restored=restored_context.new_page();restored.on('pageerror',lambda e:errors.append(str(e)));restored.on('dialog',lambda d:d.accept());restored.goto(URL+'ab730/');restored.locator('.quick-start').wait_for();open_data_management(restored);restored.locator('#import-state').set_input_files(str(backup_path));restored.locator('#settings-status').filter(has_text='学習記録を読み込みました').wait_for();close_settings(restored);assert len(state(restored)['attempts'])==ordinary;assert run(restored)['status']=='completed' and len(run(restored)['responses'])==30;restored_context.close()
 close_settings(page);nav(page,'home');page.locator('#qualification-switch').click();page.locator('.qualification-option[data-qualification-id=ap][data-part-id=objective]').click();page.locator('.quick-start').wait_for();assert (state(page) or {}).get('attempts',[])==[]
 page.locator('#qualification-switch').click();page.locator('.qualification-option').filter(has_text='AB-730').click();page.locator('.quick-start').wait_for();assert len(state(page)['attempts'])==ordinary
 # All loaded packs remain available offline, including a different multi-choice question.
 context.set_offline(True);page.reload();page.locator('.quick-start').wait_for();open_q(multis[-1]);assert page.locator('[name=answer]').count()==len(multis[-1]['choices']);assert not errors,errors
 browser.close()
print('PASS actual AB-730174 / all17 multi-choice items and per-option reasons at320/390/1280 / one-click entry / no fake mocks/cards or AP filters / answer and AI / saved selections / four field routes / full30 balanced unaided diagnosis / checkpoint+frozen scope / results and summary+backup round-trip / AP isolation / offline; artifacts:',artifacts)
