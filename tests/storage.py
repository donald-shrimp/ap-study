"""IndexedDB atomicity, concurrent study and durable owner-scoped outgoing work."""
import os
import shutil
from playwright.sync_api import sync_playwright

URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page();page.goto(URL);page.locator('.quick-start').wait_for()
    result=page.evaluate('''async()=>{
      const root=new URL('.',document.baseURI);
      const {createLocalStore}=await import(new URL('src/storage/local.js',root));
      const {makeState,createAttempt,selectAnswer,gradeAttempt,finalizeAttempt,openHint}=await import(new URL('src/domain/study.js',root));
      const {loadCatalog}=await import(new URL('src/content/catalog.js',root));
      const catalog=await loadCatalog('ap'),q=await catalog.ensure('r07h-q1');
      const assert=(test,message)=>{if(!test)throw new Error(message);};
      const options={qualificationId:'ap',rootPath:'/storage-contract/'};
      const first=createLocalStore(options),identity=await first.identity();
      const state=makeState(),a=createAttempt(q);state.attempts=[a];state.currentId=a.id;state.view='study';state.session.attemptIds=[a.id];
      await first.write(state);let pending=await first.pending();assert(pending.length===1&&pending[0].owner===identity.owner&&identity.owner.startsWith('guest:'),'guest queue scope');
      assert(!('scrollY' in pending[0].payload),'scroll must not sync');
      assert(!('readingNote' in pending[0].payload),'textbook notes must stay local');
      const initialOp=pending[0].operationId;state.attempts[0].scrollY=100;await first.write(state);assert((await first.pending())[0].operationId===initialOp,'scroll-only queued a new cloud operation');
      const staleRevision=pending[0].revision;openHint(a);await first.write(state);await first.acknowledge(a.id,staleRevision);assert((await first.pending()).length===1,'late acknowledgement discarded a newer save');
      const reopened=createLocalStore(options);const baseline=JSON.parse(await reopened.read());assert(baseline.attempts[0].hintCount===1&&(await reopened.pending()).length===1,'durable checkpoint/outbox');
      await first.close();
      // Two tabs begin from the same checkpoint and answer independently.
      const second=createLocalStore(options),s1=JSON.parse(await reopened.read()),s2=JSON.parse(await second.read());
      selectAnswer(s1.attempts[0],q.answer);finalizeAttempt(s1.attempts[0],gradeAttempt(s1.attempts[0]));await reopened.write(s1);
      selectAnswer(s2.attempts[0],(q.answer+1)%4);finalizeAttempt(s2.attempts[0],gradeAttempt(s2.attempts[0]));const fork=await second.write(s2);
      const records=JSON.parse(await second.snapshot()).attempts;assert(records.length===2&&records.some(a=>a.status==='assisted')&&records.some(a=>a.status==='incorrect'),'concurrent answers lost');
      assert(fork.remap[a.id]&&records.find(x=>x.id===fork.remap[a.id]).continuationOf===a.id,'continuation lineage');
      // Accounts and qualifications share infrastructure, never namespaces.
      const otherExam=createLocalStore({...options,qualificationId:'other'}),accountA=createLocalStore({...options,owner:'uid:account-a'}),accountB=createLocalStore({...options,owner:'uid:account-b'});
      assert(await otherExam.read()===null&&await accountA.read()===null&&await accountB.read()===null,'scope leak');
      await accountA.write(makeState());assert((await accountA.pending()).length===0&&(await accountB.pending()).length===0,'UID queue leak');
      // A failure after writing the attempt but before its queue item must roll
      // back both, and a later retry must not be skipped by an advanced baseline.
      const atomic=createLocalStore({...options,qualificationId:'atomic'}),fresh=makeState();fresh.attempts=[createAttempt({...q,qualificationId:"atomic"})];
      const put=IDBObjectStore.prototype.put;let injected=false;
      IDBObjectStore.prototype.put=function(...args){if(this.name==='outbox'&&!injected){injected=true;throw new DOMException('injected full','QuotaExceededError');}return put.apply(this,args);};
      let failed=false;try{await atomic.write(fresh);}catch{failed=true;}finally{IDBObjectStore.prototype.put=put;}
      assert(failed&&await atomic.snapshot()===null&&(await atomic.pending().catch(()=>[])).length===0,'partial transaction escaped');
      await atomic.write(fresh);assert(JSON.parse(await atomic.snapshot()).attempts.length===1&&(await atomic.pending()).length===1,'atomic retry lost');
      // Reset/import increments a generation so an older open tab cannot
      // resurrect records removed deliberately in another tab.
      await second.read();await reopened.write(makeState(),{replace:true});let refused=false;try{await second.write(s2);}catch{refused=true;}
      assert(refused&&JSON.parse(await reopened.snapshot()).attempts.length===0,'stale tab resurrected cleared history');
      const item=(await atomic.pending())[0];await atomic.acknowledge(item.id,item.revision);await atomic.acknowledge(item.id,item.revision);assert((await atomic.pending()).length===0,'duplicate acknowledgement');
      for(const store of [reopened,second,otherExam,accountA,accountB,atomic])await store.close();
      return 'atomic attempt/outbox + retry / scroll excluded / durable resume / late and duplicate ACK / concurrent answers / qualification and UID isolation / reset generation';
    }''')
    print('PASS',result,flush=True)
    # Real documents in two browser tabs use independent in-memory state.
    # The second tab starts from the first tab's saved unfinished checkpoint.
    context=browser.new_context();first=context.new_page();first.goto(URL);first.locator('.quick-start').wait_for()
    first.locator('.quick-start [data-count="1"]').click();first.get_by_role('radio').last.wait_for()
    from browser_storage import state as stored_state
    original=stored_state(first);attempt=original['attempts'][0];correct=attempt['questionSnapshot']['answer']
    second=context.new_page();second.goto(URL);second.get_by_role('radio').last.wait_for()
    first.get_by_role('radio').nth(correct).check();first.get_by_role('button',name='回答する',exact=True).click();stored_state(first)
    second.get_by_role('radio').nth((correct+1)%4).check();second.get_by_role('button',name='回答する',exact=True).click()
    saved=stored_state(second);assert len(saved['attempts'])==2 and {a['status'] for a in saved['attempts']}=={'correct','incorrect'}
    assert saved['currentId']!=original['currentId'] and any(a.get('continuationOf')==original['currentId'] for a in saved['attempts'])
    second.reload();second.locator('#result-heading').wait_for();assert len(stored_state(second)['attempts'])==2
    print('PASS two real tabs / concurrent correct and incorrect answers / continuation persists after reload',flush=True)
    # Copy the current, unmodified record format on first IndexedDB use. The
    # former localStorage value remains byte-for-byte intact as a backup.
    import json
    backup=json.dumps(saved,ensure_ascii=False);legacy=browser.new_context();legacy.add_init_script('localStorage.setItem("ap-study-mock.v1",'+json.dumps(backup)+');')
    restored=legacy.new_page();restored.goto(URL);restored.locator('#result-heading').wait_for();assert len(stored_state(restored)['attempts'])==2
    assert restored.evaluate('localStorage.getItem("ap-study-mock.v1")')==backup
    restored.locator('.sidebar [data-view=home]').click();stored_state(restored);restored.reload();restored.locator('.quick-start').wait_for();assert len(stored_state(restored)['attempts'])==2
    assert restored.evaluate('localStorage.getItem("ap-study-mock.v1")')==backup
    print('PASS existing current-format records retained / original browser value unchanged / no repeated import',flush=True)
    legacy.close();context.close();browser.close()
