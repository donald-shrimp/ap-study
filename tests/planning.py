from browser_storage import nav as action_nav, open_plan_editor, open_plan_ai
"""Real UI: optional planning, JSON validation, unaided assessment and offline resume."""
import json, shutil, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=Path(tempfile.mkdtemp(prefix='hitomon-planning-'))
READ='''async()=>{
 const {createLocalStore}=await import('/src/storage/local.js');const study=createLocalStore({qualificationId:'ap',rootPath:'/'});
 try{const identity=await study.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js');const workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return {study:JSON.parse(await study.snapshot()),documents:await workspace.read()};}finally{await workspace.close();}}finally{await study.close();}
}'''
def state(page):return page.evaluate(READ)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write'])
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept())
    page.goto('http://127.0.0.1:4173/')
    page.get_by_role('button',name='おまかせで1問',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for()
    assert page.locator('.session-milestone').count()==0 and '目安' not in page.locator('.study-toolbar').inner_text()
    page.get_by_role('button',name='中断',exact=True).click()
    page.get_by_role('button',name='計画を登録',exact=True).click()
    open_plan_editor(page);open_plan_ai(page)
    page.locator('[name=exam-objective]').fill('2026-11-04');page.locator('[name=exam-written]').fill('2026-11-30');page.get_by_role('button',name='受験日を保存',exact=True).click();page.get_by_text('受験日を保存しました。',exact=True).wait_for()
    example=json.loads((ROOT/'schemas/study-plan.example.json').read_text());example['phases'][0]['targets']['completedAttempts']=120
    open_plan_ai(page);page.locator('#plan-json').fill(json.dumps(example));page.get_by_role('button',name='検証してプレビュー',exact=True).click();page.get_by_role('heading',name='登録後の内容',exact=True).wait_for();page.get_by_role('button',name='この内容で登録',exact=True).click();page.get_by_text('受験日と計画を登録しました。',exact=True).wait_for()
    before=next(r['payload'] for r in state(page)['documents'] if r['id']=='planning')
    open_plan_ai(page);invalid={**example,'qualificationId':'other'};page.locator('#plan-json').fill(json.dumps(invalid));page.get_by_role('button',name='検証してプレビュー',exact=True).click();page.get_by_text('開いている資格と一致しません',exact=False).wait_for()
    assert next(r['payload'] for r in state(page)['documents'] if r['id']=='planning')==before
    page.get_by_role('button',name='学習状況JSONをコピー',exact=True).click();page.get_by_text('コピーしました。',exact=True).wait_for();exported=json.loads(page.evaluate('navigator.clipboard.readText()'));assert exported['format']=='hitomon-study-summary' and 'questionSnapshot' not in json.dumps(exported)
    page.get_by_role('button',name='ホーム',exact=True).click();page.get_by_role('button',name='実力診断（30問）',exact=True).click();page.get_by_role('button',name='30問の診断をはじめる',exact=True).click();page.locator('[name=diagnostic-answer]').first.wait_for()
    assert page.locator('.hint-section,.result,.correct-choice,.answer-selection').count()==0
    for i in range(3):
        page.locator('[name=diagnostic-answer]').first.check();page.get_by_role('button',name='回答して次へ',exact=True).click();page.get_by_text(f'診断 {i+2} / 30問',exact=True).wait_for()
    page.locator('[name=diagnostic-answer]').last.check();page.wait_for_function('document.querySelector("[data-action=submit-diagnostic]").disabled===false')
    page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='診断の続きから',exact=True).wait_for()
    saved=state(page);run=next(r['payload'] for r in saved['documents'] if r['kind']=='diagnostic');assert run['status']=='in_progress' and run['currentIndex']==3 and len(run['responses'])==3
    assert not any(a['status'] in ['correct','incorrect'] for a in saved['study']['attempts'])
    page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(resolve=>navigator.serviceWorker.addEventListener("controllerchange",resolve,{once:true}));}')
    context.set_offline(True);page.reload();page.get_by_role('button',name='診断の続きから',exact=True).click();page.get_by_text('診断 4 / 30問',exact=True).wait_for();assert page.locator('[name=diagnostic-answer]').last.is_checked()
    page.get_by_role('button',name='ここまでで診断終了',exact=True).click();page.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();assert '3 / 30問に回答' in page.locator('#main').inner_text()
    assert page.locator('.hint-section').count()==0
    result=state(page);final=next(r['payload'] for r in result['documents'] if r['kind']=='diagnostic');assert final['status']=='ended_early'
    page.get_by_role('button',name='ホーム',exact=True).click();assert page.get_by_role('button',name='診断の続きから',exact=True).count()==0
    action_nav(page,'review');assert page.locator('#main').inner_text()
    context.set_offline(False);page.locator('.sidebar [data-view=home]').click();page.get_by_role('button',name='診断結果を見る',exact=True).click();page.get_by_role('button',name='30問の診断をはじめる',exact=True).click();page.locator('[name=diagnostic-answer]').first.wait_for()
    for i in range(30):
        page.locator('[name=diagnostic-answer]').first.check();page.get_by_role('button',name='回答して結果へ' if i==29 else '回答して次へ',exact=True).click()
        if i<29:page.get_by_text(f'診断 {i+2} / 30問',exact=True).wait_for()
    page.get_by_role('heading',name='診断結果',exact=True).wait_for();assert page.locator('.diagnostic-topics .row').count()==17
    page.locator('.diagnostic-review').first.locator('summary').click();assert page.locator('.diagnostic-review').first.locator('.reason-list li').count()==4
    snapshot=state(page);assert sum(r['kind']=='diagnostic' and r['payload']['status']=='completed' for r in snapshot['documents'])==1
    page.screenshot(path=str(ARTIFACTS/'diagnostic-result.png'),full_page=True)
    page.locator('.diagnostic-review').first.get_by_role('button',name='学習モードで解き直す',exact=True).click();page.get_by_role('button',name='ヒントを1つ見る',exact=True).wait_for();page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
    assert next(r['payload'] for r in state(page)['documents'] if r['id']==final['id'])==final
    page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='計画を見る',exact=True).click();page.evaluate('document.documentElement.style.fontSize="32px"');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(ARTIFACTS/'planning-mobile-200.png'),full_page=True)
    assert not errors,errors
    browser.close()
print('PASS plan import preview / invalid import unchanged / AI summary / 30-question unaided diagnosis / offline draft resume / partial and complete results / retry independence / mobile 200%')
print('Artifacts:',ARTIFACTS)
