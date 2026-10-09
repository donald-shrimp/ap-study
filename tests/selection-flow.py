"""Selection audit regressions, isolated guest records and synthetic remote data."""
import json, os, shutil
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from browser_storage import state, write_state, nav, open_plan_ai, open_answer_history

ROOT=Path(__file__).resolve().parents[1]
URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/')
ART=Path(os.getenv('AP_STUDY_ARTIFACTS','/workspace/scratch/selection-implementation'));ART.mkdir(parents=True,exist_ok=True)
corpus=json.loads((ROOT/'data/questions.json').read_text())
deck=json.loads((ROOT/'content/ap/flashcards.json').read_text())
def current(pg):
    s=state(pg);return next(a for a in s['attempts'] if a['id']==s['currentId'])
def entry(pg,mode):return pg.locator(f'.study-entrance[data-paper-mode="{mode}"]')
def start(pg,mode='all'):
    entry(pg,mode).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();return current(pg)
def answer(pg,correct=True):
    a=current(pg);n=a['questionSnapshot']['answer'];pg.get_by_role('radio').nth(n if correct else (n+1)%4).check();pg.get_by_role('button',name='回答する',exact=True).click();pg.locator('#result-heading').wait_for()
def search(pg,id):
    nav(pg,'materials');pg.locator('[data-action=reset-filters]').click();q=next(q for q in corpus if q['id']==id)
    pg.locator('[name=year]').select_option(str(q['year']));pg.locator('[name=season]').select_option(q['season']);pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{id}"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for()
cases=[]
with sync_playwright() as p:
    opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
    if URL.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
    browser=p.chromium.launch(**opts)
    def fresh():
        context=browser.new_context(viewport={'width':390,'height':844},timezone_id='Asia/Tokyo');pg=context.new_page();pg.set_default_timeout(15000);pg.on('pageerror',lambda e: (_ for _ in ()).throw(AssertionError(str(e))));pg.on('dialog',lambda d:d.accept());pg.goto(URL);entry(pg,'all').wait_for();pg.wait_for_function('document.getElementById("sync-state").textContent.includes("ログインすると、学習記録を同期できます。")');return context,pg
    def done(context,name):
        cases.append(name);print('PASS',name,flush=True);context.close()
    # Automatic home scope is broad; only the explicit plan recommendation scopes it.
    ctx,pg=fresh();pg.get_by_role('button',name='計画を登録',exact=True).click();today=datetime.now(ZoneInfo('Asia/Tokyo')).date();date=lambda n:(today+timedelta(days=n)).isoformat()
    plan=json.loads((ROOT/'schemas/study-plan.example.json').read_text());plan['examDates']=[];plan['phases']=[{'id':'focus','name':'DBとNW','start':date(0),'end':date(7),'examPartIds':['objective'],'targets':{'completedAttempts':20},'focusTopicIds':['database','network']}]
    open_plan_ai(pg);pg.locator('#plan-json').fill(json.dumps(plan));pg.get_by_role('button',name='検証してプレビュー',exact=True).click();pg.get_by_role('button',name='この内容で登録',exact=True).click();pg.get_by_text('受験日と計画を登録しました。',exact=True).wait_for();nav(pg,'home')
    a=start(pg,'paperless');assert state(pg)['session']['topicId'] is None and not state(pg)['session']['topicIds'];answer(pg);pg.get_by_role('button',name='もう1問',exact=True).click();assert current(pg)['questionId']!=a['questionId'];assert state(pg)['session']['topicId'] is None
    pg.get_by_role('button',name='中断',exact=True).click();pg.locator('.plan-next [data-action=plan-start]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['questionSnapshot']['topicId'] in ['database','network'];assert state(pg)['session']['topicIds']==['database','network'];answer(pg);pg.get_by_role('button',name='もう1問',exact=True).click();assert current(pg)['questionSnapshot']['topicId'] in ['database','network'];pg.get_by_role('button',name='中断',exact=True).click()
    for width in [320,390]:
        pg.set_viewport_size({'width':width,'height':844});assert pg.locator('.home-core').bounding_box()['y']+pg.locator('.home-core').bounding_box()['height']<844;assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
    pg.screenshot(path=str(ART/'home.png'),full_page=False);done(ctx,'F01 explicit plan scope / broad home / mobile home')
    # Postponing advances, preserving choice and hint. Reload cannot auto-loop it.
    ctx,pg=fresh();a=start(pg,'paperless');pg.get_by_role('radio').first.check();pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('button',name='この問題はあとで解く',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();b=current(pg);assert b['questionId']!=a['questionId'];s=state(pg);old=next(x for x in s['attempts'] if x['id']==a['id']);assert old['deferred'] and old['hintCount']==1 and old['selected']==0
    pg.reload();assert current(pg)['id']==b['id'];pg.get_by_role('button',name='中断',exact=True).click();assert entry(pg,'paperless').get_attribute('data-id')==b['id'];nav(pg,'review');pg.locator(f'[data-action=resume][data-id="{a["id"]}"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);assert a['hintCount']==1 and a['selected']==0 and not a['deferred'];done(ctx,'F02 postpone / next / reload / saved-work resume')
    # A rejected save must not strand the visible question after postponing.
    ctx,pg=fresh();a=start(pg,'paperless');pg.get_by_role('radio').first.check();pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();state(pg)
    pg.evaluate('''()=>{const original=IDBObjectStore.prototype.put;window.__selectionOriginalPut=original;IDBObjectStore.prototype.put=function(...args){if(this.name==='outbox')throw new DOMException('injected full','QuotaExceededError');return original.apply(this,args);};}''')
    pg.get_by_role('button',name='この問題はあとで解く',exact=True).click();pg.wait_for_function('document.getElementById("save-state").textContent==="保存できていません"');assert pg.locator('#notice').is_visible();assert pg.get_by_role('radio').first.is_checked() and pg.locator('.hint-box').count()==1
    pg.evaluate('()=>{IDBObjectStore.prototype.put=window.__selectionOriginalPut;}');pg.get_by_role('button',name='回答する',exact=True).click();pg.locator('#result-heading').wait_for();assert current(pg)['id']==a['id'];assert not current(pg).get('deferred');done(ctx,'F02 failed-save rollback / same visible question retained')
    # History resume uses the saved scope, not the last entrance.
    ctx,pg=fresh();a=start(pg,'paperless');pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('radio').first.check();pg.get_by_role('button',name='中断',exact=True).click();b=start(pg,'desk');assert b['questionId']!=a['questionId'];pg.get_by_role('button',name='中断',exact=True).click();nav(pg,'history');open_answer_history(pg);pg.locator(f'[data-action=resume][data-id="{a["id"]}"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['id']==a['id'] and current(pg)['entryMode']=='paperless' and current(pg)['hintCount']==1 and current(pg)['selected']==0;assert state(pg)['session']['paperMode']=='paperless';done(ctx,'F03 history resume / unchanged entrance and work')
    # Explicit search bypasses automatic eligibility without changing the home preference.
    ctx,pg=fresh();start(pg,'paperless');pg.get_by_role('button',name='中断',exact=True).click();search(pg,'r07h-q18');assert current(pg)['questionId']=='r07h-q18' and state(pg)['session']['intent']=='direct';assert state(pg)['settings']['paperMode']=='paperless';answer(pg);pg.get_by_role('button',name='元の画面に戻る',exact=True).click();assert state(pg)['view']=='materials';nav(pg,'home');assert entry(pg,'paperless').get_attribute('data-last-entry')=='true';done(ctx,'F04 explicit calculation / return / unchanged home preference')
    # A real card retains its flipped state when returning from its referenced problem.
    ctx,pg=fresh();start(pg,'paperless');pg.get_by_role('button',name='中断',exact=True).click();pg.get_by_role('button',name='単語帳 · 681枚',exact=True).click();pg.locator('.flashcard').wait_for()
    pg.evaluate('''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),study=createLocalStore({qualificationId:'ap',rootPath:root.pathname}),identity=await study.identity();await study.close();const {createCardStore}=await import(new URL('src/storage/cards.js',root)),cards=createCardStore({rootPath:root.pathname,owner:identity.owner,qualificationId:'ap'});try{await cards.write({cardId:'da-conversion',cardVersion:1,flipped:true,seen:[],recent:[],topicId:'hardware'});}finally{await cards.close();}}''')
    pg.reload();pg.locator('.card-back').wait_for();front=pg.locator('.flashcard h2').inner_text();pg.locator('.flashcard details > summary').click();pg.get_by_role('button',name='過去問で確認する',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['questionId']=='r07h-q18';pg.get_by_role('button',name='単語帳に戻る',exact=True).click();assert pg.locator('.flashcard h2').inner_text()==front and pg.locator('.card-back').is_visible();assert state(pg)['settings']['paperMode']=='paperless';done(ctx,'F04 card-linked question / exact card return')
    # A review queue finishes instead of switching to a new problem.
    ctx,pg=fresh()
    for qid in ['r07h-q8','r07h-q18']:
        search(pg,qid);answer(pg,False);pg.get_by_role('button',name='ホーム',exact=True).click()
    nav(pg,'review');pg.locator('[data-action=review-start][data-id="r07h-q8"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert state(pg)['session']['intent']=='review';answer(pg);pg.get_by_role('button',name='もう1問',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['questionId']=='r07h-q18';answer(pg);assert pg.get_by_role('button',name='復習はここまで',exact=True).is_disabled();done(ctx,'F05 review-only continuation / stop')
    # Real valid synthetic completed records establish the due-order regression.
    ctx,pg=fresh();start(pg);pg.get_by_role('button',name='中断',exact=True).click();s=state(pg)
    fixture=pg.evaluate('''async()=>{const root=new URL('.',document.baseURI),{loadCatalog}=await import(new URL('src/content/catalog.js',root)),content=await loadCatalog('ap'),{createAttempt,selectAnswer,finalizeAttempt}=await import(new URL('src/domain/study.js',root)),attempts=[];for(const [i,id] of ['r07h-q1','r07h-q2','r07h-q3'].entries()){await content.ensure(id);const q=content.questions.find(q=>q.id===id),at=new Date(Date.now()-(i+1)*10*86400000).toISOString(),a=createAttempt(q,{at});selectAnswer(a,(q.answer+1)%4);finalizeAttempt(a,'incorrect',at);attempts.push(a);}return attempts;}''')
    s.update(attempts=fixture,currentId=None,view='home',session={'attemptIds':[],'topic':None});write_state(pg,s);pg.reload();a=start(pg);assert a['questionId']=='r07h-q3';answer(pg);pg.get_by_role('button',name='もう1問',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['questionId']=='r07h-q2';done(ctx,'F06 oldest due first and next')
    # Related questions return to the explicit field rather than widening it.
    ctx,pg=fresh();start(pg);pg.get_by_role('button',name='中断',exact=True).click();seed=state(pg)
    previous=pg.evaluate('''async()=>{const root=new URL('.',document.baseURI),{loadCatalog}=await import(new URL('src/content/catalog.js',root)),content=await loadCatalog('ap');await content.ensure('r06h-q36');const q=content.questions.find(q=>q.id==='r06h-q36'),{createAttempt,selectAnswer,finalizeAttempt}=await import(new URL('src/domain/study.js',root)),at=new Date(Date.now()-10*86400000).toISOString(),a=createAttempt(q,{at});selectAnswer(a,(q.answer+1)%4);finalizeAttempt(a,'incorrect',at);return a;}''')
    seed['attempts'].append(previous);write_state(pg,seed);pg.reload();nav(pg,'topics');button=pg.locator('[data-action=field-practice][data-topic="セキュリティ"]');topic=button.get_attribute('data-topic');button.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();answer(pg);related=pg.locator('#result details').filter(has=pg.locator('[data-action=start]')).first
    if related.count():
        related.locator('summary').click();related.locator('[data-action=start]').first.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert state(pg)['session']['intent']=='direct';linked=current(pg)['id'];pg.get_by_role('button',name='中断',exact=True).click();pg.reload();entry(pg,'all').wait_for();nav(pg,'history');open_answer_history(pg);pg.locator(f'[data-action=resume][data-id="{linked}"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();pg.get_by_role('button',name='元の学習に戻る',exact=True).click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert state(pg)['session']['topic']==topic and current(pg)['questionSnapshot']['topic']==topic
    else:raise AssertionError('Fixture requires a related original question')
    done(ctx,'F04 related question / original explicit field retained')
    # Synthetic remote ingestion exercises device fallback and conflict-safe continuation.
    ctx,pg=fresh();start(pg,'desk');pg.get_by_role('button',name='中断',exact=True).click();state(pg)
    remote=pg.evaluate('''async()=>{const root=new URL('.',document.baseURI),{loadCatalog}=await import(new URL('src/content/catalog.js',root)),content=await loadCatalog('ap');await content.ensure('r07h-q23');const q=content.questions.find(q=>q.id==='r07h-q23'),{createAttempt,openHint,selectAnswer}=await import(new URL('src/domain/study.js',root)),a=createAttempt(q,{topic:q.topic});openHint(a);selectAnswer(a,0);delete a.readingNote;delete a.scrollY;const {createLocalStore}=await import(new URL('src/storage/local.js',root)),store=createLocalStore({rootPath:root.pathname,qualificationId:'ap'});try{await store.mergeRemote([{id:a.id,deviceId:'synthetic-remote-device',revision:1,payload:a}],null);}finally{await store.close();}return a;}''')
    pg.reload();entry(pg,'all').wait_for();pg.wait_for_function('!document.getElementById("main").inert');assert any(a['id']==remote['id'] for a in state(pg)['attempts']);nav(pg,'history');open_answer_history(pg);pg.locator(f'[data-action=resume][data-id="{remote["id"]}"]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);assert a['id']!=remote['id'] and a['continuationOf']==remote['id'];assert a['entryMode']=='all' and a['hintCount']==1 and a['selected']==0;assert state(pg)['session']['topicId']==remote['topicId'];assert '入口の情報がない' in pg.locator('#notice').inner_text();done(ctx,'P2 synthetic remote fallback / independent continuation / saved field')
    browser.close()
(ART/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
print(f'PASS {len(cases)} audit regression flows; no production account used')
