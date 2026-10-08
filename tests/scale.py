import json,time,shutil,tempfile,os
from pathlib import Path
from datetime import datetime,timedelta,timezone
from playwright.sync_api import sync_playwright
from browser_storage import state as stored_state,write_state,nav
bank=json.loads((Path(__file__).resolve().parents[1]/'data/questions.json').read_text());key='ap-study-mock.v1';URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173');ARTIFACTS=Path(tempfile.mkdtemp(prefix='ap-study-scale-'))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errs=[];page.on('pageerror',lambda e:errs.append(str(e)));page.goto(URL);page.locator('.quick-start').wait_for();page.locator('.quick-start [data-action=entry-start][data-paper-mode=all]').click();s=stored_state(page);model=s['attempts'][0];page.get_by_role('button',name='中断',exact=True).click();attempts=[]
 for i in range(1200):
  q=bank[i%800];at=(datetime.now(timezone.utc)-timedelta(days=5,minutes=1200-i)).isoformat();a={**model,'id':f'scale-{i}','questionId':q['id'],'status':'correct' if i%4 else 'incorrect','selected':q['answer'] if i%4 else (q['answer']+1)%4,'startedAt':at,'updatedAt':at,'completedAt':at,'hintsBeforeAnswer':0,'materialSnapshot':{k:q[k] for k in ['enrichment','hintStatus','hints','summary','explanation','takeaway','choiceReasons']}}
  # Existing-format histories have no question snapshot or stable choice field.
  a.pop('questionSnapshot',None);a.pop('selectedChoiceId',None);attempts.append(a)
 s.update(attempts=attempts,currentId=None,view='home',session={'goal':1,'attemptIds':[],'topic':None});write_state(page,s);start=time.perf_counter();page.reload();page.locator('.quick-start').wait_for(timeout=5000);assert len(stored_state(page)['attempts'])==1200;print('1200-attempt home:',round(time.perf_counter()-start,3),'seconds')
 for view in ['materials','topics','review','history','home']:
  start=time.perf_counter();nav(page,view);page.locator('#main').wait_for();print(view,round(time.perf_counter()-start,3),'seconds',flush=True)
 assert not errs,errs
 page.screenshot(path=str(ARTIFACTS/'home-desktop.png'),full_page=True)
 # Corrupt existing data and unavailable IndexedDB do not block learning.
 for kind,script in [('unavailable','IDBFactory.prototype.open=function(){throw new DOMException("blocked","SecurityError")};'),('corrupt','localStorage.setItem("ap-study-mock.v1","{broken");')]:
  ctx=b.new_context();ctx.add_init_script(script);t=ctx.new_page();t.goto(URL);t.locator('.quick-start').wait_for();t.locator('.quick-start [data-action=entry-start][data-paper-mode=all]').click();t.get_by_role('radio').nth(3).check();t.get_by_role('button',name='回答する',exact=True).click();t.locator('#notice').wait_for();assert t.locator('#result-heading').count()==1;ctx.close();print('PASS',kind,'storage: learning continues',flush=True)
 b.close()
