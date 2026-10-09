"""Inspect the real IndexedDB adapter; no test-only application globals."""
import time
READ_STATE = '''async()=>{
 const root=new URL('.',document.baseURI),id=document.documentElement.dataset.qualification||'ap';
 const {createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:id,rootPath:root.pathname});
 try{return JSON.parse(await store.snapshot());}finally{await store.close();}
}'''
WRITE_STATE = '''async state=>{
 const root=new URL('.',document.baseURI),id=document.documentElement.dataset.qualification||'ap';
 const {createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:id,rootPath:root.pathname});
 try{await store.write(state,{replace:true});}finally{await store.close();}
}'''

def state(page):
    page.wait_for_function('document.querySelector("#main").getAttribute("aria-busy")!=="true" && document.querySelector("#save-state").textContent!=="保存中…"')
    return page.evaluate(READ_STATE)

def write_state(page, value):
    state(page)
    page.evaluate(WRITE_STATE, value)

def wait_for_async(page, expression, timeout=10000):
    """Await each async predicate; a Promise itself is always truthy.

    Playwright wait_for_function polls a synchronous predicate. Using async
    there can finish before the cache/IndexedDB operation has actually finished.
    """
    deadline=time.monotonic()+timeout/1000
    while time.monotonic()<deadline:
        if page.evaluate(expression):return
        page.wait_for_timeout(50)
    raise AssertionError('Async condition did not complete: '+expression)


def nav(page, view):
    """Navigate through the three visible destinations and their real actions."""
    if view == 'materials':
        page.locator('.sidebar [data-view=topics]').click()
        page.get_by_role('button', name='問題を探す', exact=True).click()
    elif view == 'review':
        page.locator('.sidebar [data-view=history]').click()
        page.locator('.record-tools [data-view=review]').click()
    else:
        page.locator(f'.sidebar [data-view={view}]').click()

def open_plan_editor(page):
    editor = page.locator('#plan-editor')
    if not editor.evaluate('(el)=>el.open'):
        editor.locator(':scope > summary').click()

def open_plan_ai(page):
    ai = page.locator('#plan-ai')
    if not ai.evaluate('(el)=>el.open'):
        ai.locator(':scope > summary').click()


def open_answer_history(page):
    history=page.locator('.answer-history')
    if not history.evaluate('(el)=>el.open'):
        history.locator(':scope > summary').click()
