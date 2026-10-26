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

def open_data_management(page, section=None):
    if not page.locator('#settings-dialog').evaluate('(el)=>el.open'):
        page.locator('#settings-button').click()
    ids=['data-management']+(['special-data'] if section in ['cards','diagnostics'] else [])
    for id in ids:
        details=page.locator('#'+id)
        if not details.evaluate('(el)=>el.open'):
            details.locator(':scope > summary').click()

def edit_material(page, question_id):
    button=page.locator(f'[data-action="edit"][data-id="{question_id}"]')
    if not button.is_visible():
        button.locator('xpath=ancestor::details[1]').locator(':scope > summary').click()
    button.click()

def select_target(page, part, qualification_id='ap', resume_written=False):
    page.locator('#qualification-switch').click()
    page.get_by_role('heading', name='資格・科目を選ぶ', exact=True).wait_for()
    page.locator(f'.qualification-option[data-qualification-id="{qualification_id}"][data-part-id="{part}"]').click()
    page.locator(f'#qualification-switch[data-part-id="{part}"]').wait_for()
    if 'firebase-emulator=1' in page.url:
        page.wait_for_function('!document.getElementById("google-login").disabled && !document.getElementById("google-logout").disabled')
    if resume_written and part == 'written' and page.locator('.study-entry [data-action=written-resume]').count():
        page.locator('.study-entry [data-action=written-resume]').click()
        page.locator('.written-layout').wait_for()

def written_list(page):
    nav(page, 'topics')
    page.locator('.case-topic').first.wait_for()
    page.locator('.case-topic details').evaluate_all('(els)=>els.forEach(el=>el.open=true)')

def open_written_case(page, case_id, mode='learning'):
    written_list(page)
    page.locator('.case-options').evaluate('(el)=>el.open=true')
    page.locator('[name=written-study-mode]').select_option(mode)
    page.locator(f'.written-case-option [data-action=written-start][data-id="{case_id}"]').click()
    page.locator('.written-layout').wait_for()
