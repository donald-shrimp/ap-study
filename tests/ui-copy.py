"""Reduced copy keeps partial-sync warnings, stored work and data-management actions."""
import json,shutil,tempfile,uuid
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state,nav,open_data_management

ROOT=Path(__file__).resolve().parents[1]
ART=Path(tempfile.mkdtemp(prefix='hitomon-ui-copy-'))
URL='http://127.0.0.1:4173/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.locator('.quick-start').wait_for()
    page.wait_for_function('!document.getElementById("google-login").disabled')
    assert not page.locator('#main .workspace-status').is_visible()
    assert 'この端末の計画' not in page.locator('#main').inner_text()
    page.locator('#settings-button').click()
    assert page.locator('#import-guest').is_hidden()
    assert page.locator('#data-management').evaluate('(el)=>!el.open')
    assert page.locator('#sync-about').evaluate('(el)=>!el.open')
    # Use real display functions with five simulated backend status reports.
    page.evaluate('''async()=>{const m=await import('/src/ui/sync-status.js');m.setSyncAccount(true,['study','planning','learning','cards','personal']);for(const scope of ['study','planning','learning','cards','personal'])m.setSyncStatus(scope,'synced');}''')
    assert page.locator('#sync-state').inner_text()=='同期済み'
    assert page.locator('#sync-details').is_hidden()
    assert not page.locator('#settings-dialog').inner_text().count('も同期済み')
    page.screenshot(path=str(ART/'settings-synced-390.png'))
    page.evaluate('''async()=>{const m=await import('/src/ui/sync-status.js');m.setSyncStatus('planning','rules',{code:'permission-denied',message:'test rules error'});}''')
    assert '同期できません' in page.locator('#sync-state').inner_text()
    assert page.locator('#sync-details p').count()==1
    assert 'Firebase' not in page.locator('#settings-dialog').inner_text()
    assert 'permission-denied' not in page.locator('#settings-dialog').inner_text()
    page.locator('#sync-technical > summary').click()
    assert 'permission-denied' in page.locator('#sync-technical pre').inner_text()
    page.locator('#sync-technical > summary').click()
    # Reproduce the previously persistent home paragraph and verify it is hidden.
    page.evaluate('''async()=>{
      const {createPlanningFeature}=await import('/src/features/planning.js');const {makeState}=await import('/src/domain/study.js');
      const qualification={id:'fixture',name:'検証資格',topics:[{id:'db',name:'DB'}]},state=makeState(),noop=()=>{};
      const feature=createPlanningFeature({qualification,rootPath:'/',getStore:()=>null,getState:()=>state,getNavigation:()=>0,content:null,base:[],validateAttempt:noop,onUpdate:noop,onNavigate:noop,onNotice:noop,onChanged:noop,getReviewCount:()=>0,download:noop});
      feature.onStatus('error');if(document.querySelector('#main .workspace-status').hidden)throw new Error('error hidden');
      feature.onStatus('synced');if(!document.querySelector('#main .workspace-status').hidden)throw new Error('normal status remained');
      const sync=await import('/src/ui/sync-status.js');sync.setSyncAccount(false);
    }''')
    # A real failed local save must also prevent a successful-sync claim.
    page.evaluate('''()=>{window.originalPut=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='meta')throw new DOMException('storage full','QuotaExceededError');return window.originalPut.apply(this,args);};}''')
    page.locator('#text-smaller').click()
    page.wait_for_function('document.getElementById("save-state").textContent.includes("保存でき")')
    assert '保存できません' in page.locator('#sync-state').inner_text()
    assert '端末の保存' in page.locator('#sync-details').inner_text()
    page.evaluate('()=>{IDBObjectStore.prototype.put=window.originalPut;}')
    page.locator('#text-reset').click()
    page.wait_for_function('document.getElementById("save-state").textContent==="この端末に保存済み"')
    assert page.locator('#sync-state').get_attribute('data-status')=='guest'
    assert 'storage full' not in page.locator('#settings-status').inner_text()
    page.get_by_role('button',name='設定を閉じる').click()
    page.locator('[data-action=entry-start][data-paper-mode=all]').click();page.get_by_role('radio').first.wait_for()
    for _ in range(3):page.locator('[data-action=hint]').click()
    page.get_by_role('radio').first.check();page.locator('[data-action=submit]').click()
    page.locator('#result-heading').wait_for()
    assert '全ヒントを表示済み' not in page.locator('#main').inner_text()
    assert '解答後のヒント閲覧は' not in page.locator('#main').inner_text()
    assert '別の日の自力正解' not in page.locator('#main').inner_text()
    assert page.locator('.review-date').is_visible()
    page.locator('[data-action=ask-ai]').click();assert '少し待って' not in page.locator('#ai-handoff-dialog').inner_text()
    page.locator('#ai-handoff-close').click()
    page.locator('[data-action=end]').click();before=state(page)
    # Data controls work without ever opening the flashcard mode first.
    open_data_management(page,'cards')
    with page.expect_download() as download:page.locator('[data-action=card-export]').click()
    assert json.loads(Path(download.value.path()).read_text())['events']==[]
    card=json.loads((ROOT/'content/ap/flashcards.json').read_text())['cards'][0]
    event={'id':str(uuid.uuid4()),'cardId':card['id'],'cardVersion':card['version'],'outcome':'again','at':'2026-10-13T00:00:00.000Z'}
    payload={'format':'hitomon-card-record','version':1,'qualificationId':'ap','events':[event]}
    page.locator('#import-cards').set_input_files({'name':'cards.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
    page.wait_for_function('document.getElementById("settings-status").textContent.includes("取り込みました")')
    with page.expect_download() as download:page.locator('[data-action=card-export]').click()
    assert json.loads(Path(download.value.path()).read_text())['events']==[event]
    page.locator('.card-data > summary').click();page.once('dialog',lambda d:d.accept());page.locator('[data-action=card-clear]').click()
    page.wait_for_function('document.getElementById("settings-status").textContent.includes("削除しました")')
    with page.expect_download() as download:page.locator('[data-action=card-export]').click()
    assert json.loads(Path(download.value.path()).read_text())['events']==[]
    assert state(page)['attempts']==before['attempts']
    with page.expect_download() as download:page.locator('#export-state').click()
    backup=json.loads(Path(download.value.path()).read_text());assert backup['attempts']==before['attempts']
    with page.expect_download() as download:page.locator('[data-action=export-diagnostics]').click()
    assert json.loads(Path(download.value.path()).read_text())['format']=='hitomon-diagnostics'
    page.locator('#import-diagnostics').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{}'})
    page.wait_for_function('document.getElementById("settings-status").textContent.includes("バックアップ")')
    page.get_by_role('button',name='設定を閉じる').click()
    nav(page,'materials');assert page.locator('[name=enriched]').count()==0
    assert '個別ヒント・解説あり' not in page.locator('#main').inner_text()
    options=page.locator('.catalog-options').first;assert not options.evaluate('(el)=>el.open')
    options.locator('summary').click();options.locator('[data-action=edit]').click();page.locator('#editor-dialog').wait_for()
    page.locator('#close-editor').click()
    # Human readable conflict previews; raw data stays inside an extra disclosure.
    page.evaluate('''async()=>{
      const {createPlanningViews}=await import('/src/ui/planning.js'),{blankPlan}=await import('/src/domain/planning.js');
      const q={id:'fixture',name:'検証資格',examParts:[{id:'a',label:'科目A',practiceAvailable:true}],topics:[{id:'db',name:'DB'}]};
      const plan=blankPlan(q);plan.examDates=[{examPartId:'a',date:'2027-01-01'}];plan.phases=[{id:'first',name:'基礎',start:'2026-12-01',end:'2026-12-31',examPartIds:['a'],focusTopicIds:['db'],targets:{completedAttempts:20}}];
      const remote=structuredClone(plan);remote.phases[0].targets.completedAttempts=30;
      const views=createPlanningViews({qualification:q,documents:[{id:'planning',kind:'planning',payload:plan,localRevision:1,conflict:{payload:remote}}],attempts:[]});
      const el=document.createElement('section');el.id='conflict-fixture';el.innerHTML=views.conflictsHTML();document.body.append(el);
    }''')
    text=page.locator('#conflict-fixture').inner_text()
    assert '科目A：2027-01-01' in text and '目標20回' in text and '目標30回' in text
    assert 'completedAttempts' not in text and 'examPartId' not in text
    page.locator('#conflict-fixture').evaluate('(el)=>el.remove()')
    nav(page,'home')
    for width in [320,390,1280]:
        page.set_viewport_size({'width':width,'height':844});page.locator('#settings-button').click()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(ART/f'settings-{width}.png'));page.get_by_role('button',name='設定を閉じる').click()
    assert not errors,errors
    browser.close()
print('PASS aggregate and partial sync / normal status removed / management downloads and card import-delete / stored attempts preserved / contextual editing / human conflict preview / 320 and 390px and PC')
print('Artifacts:',ART)
