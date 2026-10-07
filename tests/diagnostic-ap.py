"""Exercise the actual AP derived bank locally or at a supplied public URL."""
import json
import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state, nav, wait_for_async

URL = os.environ.get('HITOMON_TEST_URL', 'http://127.0.0.1:4173/')
READ = '''async()=>{
 const root=new URL('.',document.baseURI);
 const {createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:'ap',rootPath:root.pathname});
 try{const identity=await store.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root));
 const workspace=createWorkspaceStore({...identity,rootPath:root.pathname,validate:(kind,payload)=>payload});
 try{return {study:JSON.parse(await store.snapshot()),documents:await workspace.read()};}finally{await workspace.close();}
 }finally{await store.close();}
}'''
def run(page):
    return next(r['payload'] for r in page.evaluate(READ)['documents'] if r['kind']=='diagnostic')

with sync_playwright() as p:
    opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
    if URL.startswith('https:') and os.getenv('HTTPS_PROXY'):
        opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
    browser=p.chromium.launch(**opts)
    context=browser.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write'])
    page=context.new_page(); errors=[]; requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
    page.on('dialog',lambda d:d.accept())
    page.goto(URL);page.get_by_role('button',name='おまかせで1問',exact=True).wait_for()
    assert not any('/data/qualifications/ap/diagnostic.' in u for u in requests)
    page.get_by_role('button',name='おまかせで1問',exact=True).click()
    page.get_by_role('button',name='回答する',exact=True).wait_for()
    assert not state(page)['attempts'][-1]['questionSnapshot'].get('diagnosticOnly')
    page.get_by_role('button',name='中断',exact=True).click();state(page)
    page.get_by_role('button',name='実力診断（30問）',exact=True).click()
    page.get_by_role('button',name='30問の診断をはじめる',exact=True).click()
    page.locator('[name=diagnostic-answer]').first.wait_for()
    initial=run(page); slots=initial['slots']; frozen=json.dumps(slots,sort_keys=True)
    derived=[s for s in slots if s['kind']=='derived']
    assert len(derived)==17 and len({s['attempt']['questionSnapshot']['topicId'] for s in derived})==17
    assert len({s['parentQuestionId'] or s['attempt']['questionId'] for s in slots})==30
    assert initial['selectionPolicy']['defaultVariantLimit']==1 and initial['selectionPolicy']['variantLimits']=={}
    for i,s in enumerate(slots):
        q=s['attempt']['questionSnapshot']
        assert page.locator('.hint-section,.result,.correct-choice,.reason-list').count()==0
        assert page.get_by_role('button',name='ヒント',exact=False).count()==0
        answer=q['correctChoiceId'] if s['kind']=='original' else next(c['id'] for c in q['choices'] if c['id']!=q['correctChoiceId'])
        page.locator(f'[name=diagnostic-answer][value="{answer}"]').check()
        if i==2:
            page.get_by_role('button',name='中断',exact=True).click()
            wait_for_async(page, '''async()=>{
             const root=new URL('.',document.baseURI);const {createLocalStore}=await import(new URL('src/storage/local.js',root));const study=createLocalStore({qualificationId:'ap',rootPath:root.pathname});
             try{const identity=await study.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root));const w=createWorkspaceStore({...identity,rootPath:root.pathname,validate:(k,p)=>p});try{const r=(await w.read()).find(r=>r.kind==='diagnostic');return r?.payload.currentIndex===2&&r.payload.currentChoiceId!==null;}finally{await w.close();}}finally{await study.close();}
            }''')
            page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener("controllerchange",r,{once:true}));}')
            # Wait for actual original images, not merely a truthy async Promise.
            images=[path for slot in slots for path in slot['attempt']['questionSnapshot'].get('sourceImages',[])]
            assert page.evaluate('async paths=>{const cache=await caches.open(`hitomon-${new URL(".",document.baseURI).pathname}images`);return (await Promise.all(paths.map(p=>cache.match(p)))).every(Boolean);}',images)
            context.set_offline(True);page.reload()
            page.get_by_role('button',name='診断の続きから',exact=True).click()
            page.get_by_text('診断 3 / 30問',exact=True).wait_for()
            assert page.locator(f'[name=diagnostic-answer][value="{answer}"]').is_checked()
            assert json.dumps(run(page)['slots'],sort_keys=True)==frozen
        page.get_by_role('button',name='回答して結果へ' if i==29 else '回答して次へ',exact=True).click()
        if i<29:page.get_by_text(f'診断 {i+2} / 30問',exact=True).wait_for()
    page.get_by_role('heading',name='診断結果',exact=True).wait_for()
    page.get_by_text('出題構成を確認',exact=True).click()
    assert '派生問題：17問出題・17問回答・0問正解' in page.locator('#main').inner_text()
    reviews=page.locator('.diagnostic-review').filter(has=page.locator('button').filter(has_text='元の過去問を学習'))
    assert reviews.count()==17
    for i in range(17):
        assert reviews.nth(i).locator('.reason-list li').count()==4
    reviews.first.locator('summary').click();assert reviews.first.locator('.reason-list li').count()==4
    artifact=Path('/workspace/scratch/diagnostic-review-20261008');artifact.mkdir(exist_ok=True)
    page.screenshot(path=str(artifact/('public-results.png' if URL.startswith('https:') else 'local-results.png')),full_page=True)
    page.get_by_role('button',name='結果と学習状況をAIへ渡す',exact=True).click()
    page.get_by_role('button',name='学習状況JSONをコピー',exact=True).click()
    page.get_by_text('コピーしました。',exact=True).wait_for()
    summary=json.loads(page.evaluate('navigator.clipboard.readText()'))
    assert summary['learning']['all']['completedAttempts']==13
    result=summary['diagnostics'][0]
    assert result['answered']==30 and result['correct']==13 and result['assistance']=='none'
    assert next(c for c in result['composition'] if c['kind']=='derived')['answered']==17
    assert len([item for item in result['items'] if item['kind']=='derived' and item['parentQuestionId']])==17
    nav(page,'review');assert not page.locator('[data-action=start][data-id^="ap-diagnostic-"]').count()
    nav(page,'materials');assert not page.locator('[data-action=start][data-id^="ap-diagnostic-"]').count()
    assert all(not a['questionSnapshot'].get('diagnosticOnly') for a in state(page)['attempts'])
    context.set_offline(False);page.reload()
    page.locator('.sidebar [data-view=home]').wait_for()
    page.locator('.sidebar [data-view=home]').click()
    page.get_by_role('button',name='診断結果を見る',exact=True).click()
    page.get_by_role('button',name='結果を見る',exact=True).click()
    reviews=page.locator('.diagnostic-review').filter(has=page.locator('button').filter(has_text='元の過去問を学習'))
    reviews.first.locator('summary').click();reviews.first.get_by_role('button',name='元の過去問を学習',exact=True).click()
    try:
        page.get_by_role('button',name='回答する',exact=True).wait_for(timeout=10000)
    except Exception:
        page.screenshot(path=str(artifact/'return-parent-failure.png'),full_page=True)
        print(page.locator('#main').inner_text(),page.locator('#notice').inner_text() if page.locator('#notice').count() else '',page.evaluate('navigator.onLine'),flush=True)
        raise
    assert not state(page)['attempts'][-1]['questionSnapshot'].get('diagnosticOnly')
    assert not errors,errors
    (artifact/('public-browser.json' if URL.startswith('https:') else 'local-browser.json')).write_text(json.dumps({'url':URL,'derived':17,'original':13,'families':30,'answered':30,'regularCompleted':13,'offlineFrozenResume':True,'choiceReasons':4,'errors':errors},ensure_ascii=False,indent=2)+'\n')
    browser.close()
print('PASS actual AP 17 derived + 13 originals / 30 unique families / no assistance / offline frozen resume + selected answer / 4 reasons / result and AI export / normal-study exclusion / return to parent')
