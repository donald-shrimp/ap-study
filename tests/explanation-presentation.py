"""Synthetic saved explanations through real practice, assessment and case views.

No published question data or personal records are edited. Can also target Pages.
"""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import state,write_state

ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-explanation-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
errors=[];checks=[]
try:
 with sync_playwright() as p:
  options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https://') and os.getenv('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  browser=p.chromium.launch(**options)
  for qual,outcome in [('ap','correct'),('ab730','incorrect'),('fp2','revealed')]:
   ctx=browser.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(BASE+qual+'/?part=objective&entry=home');pg.locator('.quick-start').wait_for()
   pg.locator('.study-entrance[data-paper-mode=all]').click();pg.locator('.question-panel').wait_for()
   saved=state(pg);attempt=next(a for a in saved['attempts'] if a['id']==saved['currentId']);q=attempt['questionSnapshot'];m=attempt['materialSnapshot']
   m.update(summary='検証用の**判断軸**。',explanation='**根拠**を確認。\n**<img src=x onerror=alert(1)>**',takeaway='クレジット＝**後払い**、デビット＝**即時払い**。',choiceReasons=['**各肢の理由**。' for c in q['choices']])
   if m['hints']:m['hints'][0]['text']='**比較の軸**を確認する。'
   write_state(pg,saved);pg.reload();pg.locator('.question-panel').wait_for();assert pg.locator('#result').count()==0
   assert '判断軸' not in pg.locator('#main').inner_text()
   if m['hints']:
    pg.locator('[data-action=hint]').click();assert pg.locator('.hint-box strong').inner_text()=='比較の軸'
   if outcome=='revealed':pg.locator('[data-action=reveal]').click()
   else:
    correct=q.get('correctChoiceId') or q['choices'][q['answer']]['id'];index=next(i for i,c in enumerate(q['choices']) if (c['id']==correct)==(outcome=='correct'))
    pg.get_by_role('radio').nth(index).check();pg.locator('[data-action=submit]').click()
   pg.locator('#result').wait_for();assert pg.locator('#result > p.explanation strong').first.inner_text()=='判断軸'
   assert pg.locator('#result img,#result script').count()==0
   assert '<img src=x onerror=alert(1)>' in pg.locator('#result .explanation').all_text_contents()[-1]
   pg.locator('#result details').evaluate_all('(nodes)=>nodes.forEach(n=>n.open=true)');assert pg.locator('.reason-list strong').count()==len(q['choices'])
   for width,scale in [(320,100),(390,100),(1440,100),(390,200)]:
    pg.set_viewport_size({'width':width,'height':1000});pg.evaluate('(s)=>document.documentElement.style.fontSize=s+"%"',scale)
    metric=pg.locator('.takeaway strong:not(.takeaway-label)').first.evaluate('(e)=>({inline:getComputedStyle(e).display==="inline",size:getComputedStyle(e).fontSize===getComputedStyle(e.parentElement).fontSize})')
    assert metric=={'inline':True,'size':True},metric
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   pg.screenshot(path=str(ART/(qual+'-result.png')),full_page=True)
   before=state(pg);snap=next(a for a in before['attempts'] if a['id']==before['currentId'])['materialSnapshot']
   pg.evaluate('async()=>await navigator.serviceWorker.ready');pg.wait_for_function('!!navigator.serviceWorker.controller');ctx.set_offline(True)
   pg.reload();pg.locator('#result').wait_for();assert pg.locator('.takeaway strong:not(.takeaway-label)').count()==2
   after=state(pg);assert next(a for a in after['attempts'] if a['id']==after['currentId'])['materialSnapshot']==snap
   checks.append(qual+': practice, disclosure, emphasis, XSS, widths, offline snapshot');ctx.close()
  # Exercise both assessment modes with saved synthetic material; no answers in
  # the in-progress DOM, even after one response has been submitted.
  ctx=browser.new_context();pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(BASE+'ap/');pg.locator('.quick-start').wait_for()
  result=pg.evaluate('''async()=>{
   const {loadCatalog}=await import('./src/content/catalog.js'),{createDiagnostic,submitDiagnostic,finishDiagnostic}=await import('./src/domain/diagnostic.js'),{createMock}=await import('./src/domain/mock.js'),{createPlanningViews}=await import('./src/ui/planning.js');
   const catalog=await loadCatalog('ap',{requestedPartId:'objective'});await catalog.loadAll();const qual=catalog.manifest,questions=structuredClone(catalog.questions.slice(0,30));
   for(const q of questions)Object.assign(q,{uses:['practice','diagnostic','mock'],summary:'**診断の論点**',explanation:'**診断の根拠**',choiceReasons:q.choices.map(()=> '**肢の根拠**'),takeaway:'次回も**条件を比較**'});
   const set={id:'synthetic-emphasis',label:'合成の表示検証',size:questions.length,status:'ready',slots:questions.map((q,i)=>({number:i+1,questionId:q.id,topicId:q.topicId}))};
   const report=[];for(const mode of ['diagnostic','mock']){
    const run=mode==='mock'?createMock(set,questions,qual):createDiagnostic(questions,qual),before=JSON.stringify(run.slots);
    const views=()=>createPlanningViews({qualification:qual,documents:[{id:run.id,kind:mode,payload:run}],attempts:[],currentRunId:run.id});
    if(views().diagnosticHTML().includes('診断の論点'))throw Error('answer leak before submission');
    submitDiagnostic(run,questions[0].correctChoiceId);if(views().diagnosticHTML().includes('診断の根拠'))throw Error('answer leak before finish');
    finishDiagnostic(run);const host=document.createElement('div');host.innerHTML=views().diagnosticHTML();
    if(host.querySelectorAll('.takeaway strong:not(.takeaway-label)').length!==30)throw Error('missing takeaways');
    if(host.querySelector('.explanation strong')?.textContent!=='診断の論点')throw Error('missing summary emphasis');
    if(JSON.stringify(run.slots)!==before)throw Error('renderer mutated saved slots');
    const legacy=structuredClone(run);for(const s of legacy.slots){delete s.attempt.materialSnapshot.takeaway;delete s.attempt.materialSnapshot.summary;}
    const old=createPlanningViews({qualification:qual,documents:[{id:legacy.id,kind:mode,payload:legacy}],attempts:[],currentRunId:legacy.id});
    host.innerHTML=old.diagnosticHTML();if(host.querySelector('.takeaway'))throw Error('empty legacy takeaway');report.push(mode);
   }return report;
  }''');assert result==['diagnostic','mock'];checks+=result;ctx.close()
  # Real written-feature views restore an isolated synthetic run through the
  # production storage adapter, retaining rich explanation blocks.
  for qual,part in [('ap','written'),('fp2','jafp-practical')]:
   ctx=browser.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(BASE+qual+'/?part='+part+'&entry=home');pg.locator('.study-entry').wait_for()
   info=pg.evaluate('''async({qual,part})=>{
    const {loadCatalog}=await import('./src/content/catalog.js'),{createLocalStore}=await import('./src/storage/local.js'),{createWorkspaceStore}=await import('./src/storage/workspace.js'),{createCaseRun,validateCaseRun}=await import('./src/domain/case-study.js');
    const root=new URL('.',document.baseURI),catalog=await loadCatalog(qual,{requestedPartId:part}),c=structuredClone((await catalog.loadCases()).find(c=>c.examPartId===part)),f=c.items[0].fields[0];
    f.explanation='**ケース条件**を確認。\\n\\n$$x_1=2$$\\n\\n| A | B |\\n| --- | --- |\\n| **表の条件** | 2 |\\n\\n```\\n**literal** <tag>\\n```';
    const run=createCaseRun(c),local=createLocalStore({qualificationId:qual,rootPath:root.pathname}),identity=await local.identity(),ws=createWorkspaceStore({...identity,rootPath:root.pathname,namespaceName:'written',validate:(_,r)=>validateCaseRun(r,catalog.manifest)});
    await ws.write('case',run.id,run,0);const suffix=catalog.manifest.examParts.filter(p=>p.unit==='cases').length>1?':'+part:'';
    localStorage.setItem(`hitomon-v2:${root.pathname}:${identity.owner}:${qual}:written-view${suffix}`,JSON.stringify({currentId:run.id,view:'study'}));await ws.close();await local.close();
    return {key:c.items[0].id+'--'+f.id,type:f.type,answer:f.type==='singleChoice'?f.choices.find(c=>c.label===f.referenceAnswers[0]).id:f.referenceAnswers[0]};
   }''',{'qual':qual,'part':part})
   pg.reload();pg.locator('.written-layout').wait_for();field=pg.locator('section.written-field[data-written-key="'+info['key']+'"]');assert field.locator('.written-answer').count()==0
   if info['type']=='singleChoice':field.locator('input[value="'+info['answer']+'"]').check()
   elif info['type']=='numeric':field.locator('input').fill(info['answer'])
   else:field.locator('textarea').fill(info['answer'])
   field.locator('[data-action=written-submit]').click();field.locator('[data-action=written-answer]').click();field.locator('.written-answer').wait_for()
   assert field.locator('.written-answer strong').first.inner_text()=='ケース条件';assert field.locator('.katex').count()==1;assert field.locator('td strong').inner_text()=='表の条件';assert field.locator('pre code').inner_text()=='**literal** <tag>'
   assert field.locator('p p').count()==0
   pg.reload();field.locator('.written-answer').wait_for();assert field.locator('.katex').count()==1
   pg.screenshot(path=str(ART/(qual+'-case.png')),full_page=True);checks.append(qual+': case rich blocks, disclosure, snapshot resume');ctx.close()
  assert not errors,errors;browser.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({'checks':checks,'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
print('PASS explanation presentation:',checks);print('Artifacts:',ART)
