"""Exercise approved field/record UI with real IndexedDB and fixed valid snapshots."""
import json,os,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state,write_state,nav
ROOT=Path(__file__).resolve().parents[1];URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/')
ART=Path(os.getenv('AP_STUDY_ARTIFACTS','/workspace/scratch/field-implementation/browser'));ART.mkdir(parents=True,exist_ok=True)
bank=json.loads((ROOT/'data/questions.json').read_text());qualification=json.loads((ROOT/'content/ap/qualification.json').read_text())
ids=[next(q['id'] for q in bank if q['topic']==topic and q['hints'][0]['revealsAnswer']==False) for topic in ['データベース','データベース','ネットワーク','セキュリティ']]
ids[1]=next(q['id'] for q in bank if q['topic']=='データベース' and q['id']!=ids[0] and not q['hints'][0]['revealsAnswer'])
def current(pg):
 s=state(pg);return next(a for a in s['attempts'] if a['id']==s['currentId'])
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.set_default_timeout(20000)
 errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for()
 assert pg.locator('.study-entrance').count()==3
 assert pg.locator('.home-shortcuts [data-view=review]').count()==1
 pg.locator('.home-shortcuts [data-view=review]').click();assert pg.get_by_role('heading',name='解き直し',exact=True).is_visible()
 pg.get_by_role('button',name='⌂ ホーム',exact=True).click();nav(pg,'history');assert pg.locator('.overall-rate').inner_text()=='未確認'
 seeded=pg.evaluate('''async ids=>{
  const root=new URL('.',document.baseURI),{loadCatalog}=await import(new URL('src/content/catalog.js',root)),catalog=await loadCatalog('ap');
  const {makeState,createAttempt,openHint,selectAnswer,finalizeAttempt}=await import(new URL('src/domain/study.js',root)),s=makeState(),at=new Date().toISOString();
  for(let i=0;i<ids.length;i++){
   const q=await catalog.ensure(ids[i]),a=createAttempt(q,{at,id:'fixture-'+i});
   selectAnswer(a,i===2?(q.answer+1)%4:q.answer);
   if(i===1)openHint(a,at);if(i===3)a.answerViewedBefore=true;
   finalizeAttempt(a,['correct','assisted','incorrect','revealed'][i],at);s.attempts.push(a);
  }
  const old=structuredClone(s.attempts[0]);old.id='older-result';old.selected=(old.questionSnapshot.answer+1)%4;old.selectedChoiceId=old.questionSnapshot.choices[old.selected].id;old.status='incorrect';old.startedAt=old.updatedAt=old.completedAt=new Date(Date.now()-86400000).toISOString();s.attempts.unshift(old);
  return s;
 }''',ids)
 write_state(pg,seeded);pg.reload();pg.locator('.study-entrance').first.wait_for();nav(pg,'history')
 assert pg.locator('.overall-rate').inner_text()=='25%'
 assert pg.locator('.overall-count').inner_text()=='4問に取り組み · 自力正解 1問'
 assert pg.locator('.overall-accuracy > *').count()==3
 assert 'ヒント' not in pg.locator('.overall-accuracy').inner_text()
 assert pg.locator('.field-note-input').count()==17
 assert pg.locator('.field-note-input').first.get_attribute('placeholder')=='メモを書く'
 note=pg.locator('#record-field-network .field-note-input');note.fill('第3章 p.40 <script>alert(1)</script>');state(pg)
 note.evaluate('(el)=>el.setSelectionRange(6,6)');pg.evaluate('window.dispatchEvent(new Event("online"))')
 pg.wait_for_function('document.activeElement?.matches("#record-field-network .field-note-input") && document.activeElement.selectionStart===6')
 assert pg.locator('#record-field-network .field-note-input').input_value()=='第3章 p.40 <script>alert(1)</script>'
 pg.reload();note=pg.locator('#record-field-network .field-note-input');note.wait_for();assert '<script>' in note.input_value()
 nav(pg,'topics');assert pg.locator('.topic-card').count()==17
 assert pg.locator('.topic-card').evaluate_all('(rows)=>rows.map(r=>r.id)')==['field-'+t['id'] for t in qualification['topics']]
 assert pg.locator('[data-action=field-mode]').count()==0 and pg.locator('input[data-reading-topic]').count()==0
 assert '教科書：第3章 p.40 <script>alert(1)</script>' in pg.locator('#field-network').inner_text()
 assert pg.locator('#field-network script').count()==0
 assert pg.locator('.field-start').first.bounding_box()['y']<350
 target=pg.locator('#field-network [data-action=field-practice]');qid=target.get_attribute('data-id');target.click();pg.get_by_role('button',name='回答する',exact=True).wait_for()
 a=current(pg);assert a['questionId']==qid and a['practiceScope']['topicId']=='network' and a['entryMode']=='all'
 pg.get_by_role('radio').first.check();pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('button',name='中断',exact=True).click()
 assert pg.locator('.study-entrance[data-paper-mode=all]').get_attribute('data-id')==a['id']
 nav(pg,'topics');target=pg.locator('#field-network [data-action=field-practice]');assert target.get_attribute('data-resume-id')==a['id'];assert '続きから' in target.inner_text()
 target.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['id']==a['id'] and current(pg)['hintCount']==1 and current(pg)['selected']==0
 pg.get_by_role('button',name='中断',exact=True).click();nav(pg,'topics');pg.locator('[data-action=paper-mode][data-mode=paperless]').click();pg.locator('[data-mode=paperless][aria-pressed=true]').wait_for()
 target=pg.locator('#field-network [data-action=field-practice]');assert not target.get_attribute('data-resume-id');target.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['entryMode']=='paperless';assert current(pg)['id']!=a['id'];pg.get_by_role('button',name='中断',exact=True).click()
 nav(pg,'history');pg.locator('[data-action=field-mode][data-mode=diagnostic]').click();assert '完了した診断はありません' in pg.locator('#main').inner_text()
 nav(pg,'topics');assert pg.locator('[data-action=field-mode]').count()==0;assert '自力正解 1 / 2問' in pg.locator('#field-database').inner_text()
 nav(pg,'history');assert pg.locator('[data-action=field-mode][data-mode=learning]').get_attribute('aria-pressed')=='true'
 pg.locator('#record-field-database [data-action=field-review]').click();assert pg.get_by_role('heading',name='データベースの解き直し',exact=True).is_visible()
 assert pg.locator('[data-action=review-start]').count()==1
 pg.locator('[data-action=review-start]').first.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert state(pg)['session']['intent']=='review' and state(pg)['session']['topicId']=='database'
 answer=current(pg)['questionSnapshot']['answer'];pg.get_by_role('radio').nth(answer).check();pg.get_by_role('button',name='回答する',exact=True).click();assert pg.get_by_role('button',name='復習はここまで',exact=True).is_disabled();pg.get_by_role('button',name='解き直しに戻る',exact=True).click();assert pg.get_by_role('heading',name='データベースの解き直し',exact=True).is_visible()
 pg.get_by_role('button',name='全分野の解き直し',exact=True).click();assert pg.get_by_role('heading',name='解き直し',exact=True).is_visible()
 assert pg.locator('[data-action=review-start]').count()>=2
 nav(pg,'history');note=pg.locator('#record-field-network .field-note-input');note.fill('');state(pg);nav(pg,'topics');assert pg.locator('#field-network .field-note').count()==0
 nav(pg,'history');pg.locator('.answer-history > summary').click();pg.locator('[data-action=resume][data-id="fixture-0"]').click();pg.locator('#result-heading').wait_for();assert current(pg)['readingNote']=='' and current(pg)['status']=='correct'
 for view in ['home','topics','history','review']:
  nav(pg,view)
  for width in [320,390,1280]:
   pg.set_viewport_size({'width':width,'height':844});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),(view,width)
   if width==390:pg.screenshot(path=str(ART/(view+'.png')),full_page=False)
   pg.evaluate('document.documentElement.style.fontSize="32px"');assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),(view,width,'200%');pg.evaluate('document.documentElement.style.fontSize=""')
 nav(pg,'topics');pg.evaluate('async()=>await navigator.serviceWorker.ready');ctx.set_offline(True);pg.reload();pg.locator('.field-list').wait_for();nav(pg,'history');assert pg.locator('#record-field-network .field-note-input').input_value()=='';ctx.set_offline(False)
 assert not errors,errors;b.close()
print('PASS home/field/record/review routes / fixed ordering / 25% self-only latest unique records / inline notes and escaping / scope-owned resume / paper conditions / diagnostic separation / field-limited review and return / snapshot preserved / mobile and 200% / offline records')
