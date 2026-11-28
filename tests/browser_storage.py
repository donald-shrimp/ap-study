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
    page.locator('#main:not([inert]):not(:has(> .loading))').wait_for()
    if page.locator('#main > .written-layout, #main > .question-panel').count():
        back = page.locator('#main > .study-toolbar .study-back-button')
        if back.is_visible():
            back.click()
        else:
            page.locator('.topbar .brand').click()
        page.locator('.sidebar').wait_for(state='visible')
        if view == 'home':
            return
    if view == 'materials':
        page.locator('.sidebar [data-view=topics]').click()
        page.get_by_role('button', name='問題を探す', exact=True).click()
    elif view == 'review':
        page.locator('.sidebar [data-view=history]').click()
        entry = page.locator('.record-tools [data-view=review]')
        if not entry.count():
            page.locator('.sidebar [data-view=home]').click()
            entry = page.locator('.home-shortcuts [data-view=review]')
        entry.click()
    else:
        page.locator(f'.sidebar [data-view={view}]').click()

def open_plan_editor(page):
    editor = page.locator('#plan-editor')
    if not editor.evaluate('(el)=>el.open'):
        editor.locator(':scope > summary').click()

def open_plan_ai(page):
    ai = page.locator('#plan-ai')
    if ai.locator('xpath=parent::*[@id="plan-editor"]').count():
        open_plan_editor(page)
    if not ai.evaluate('(el)=>el.open'):
        ai.locator(':scope > summary').click()

def open_written_field_actions(page):
    toggle=page.locator('.written-individual-toggle')
    if toggle.count() and not toggle.evaluate('(el)=>el.open'):
        toggle.locator('summary').click()


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

def open_offline(page, *, choose=False):
    dialog=page.locator('#settings-dialog')
    if not dialog.evaluate('(el)=>el.open'):
        page.locator('#settings-button').click()
    dialog.locator('[data-action=offline-open]').click()
    manager=page.locator('#offline-dialog')
    manager.locator('[data-offline-save]').wait_for()
    if choose:
        manager.locator('.offline-selection > summary').click()
    return manager


def assessment_action(page, action):
    menu=page.locator('.assessment-menu')
    if not menu.evaluate('(el)=>el.open'):
        menu.locator(':scope > summary').click()
    menu.locator(f'[data-action={action}]').click()


def open_plan_conditions(page):
    open_plan_editor(page)
    section=page.locator('.plan-context')
    if not section.evaluate('(el)=>el.open'):
        section.locator(':scope > summary').click()
    more=section.locator('details')
    if not more.evaluate('(el)=>el.open'):
        more.locator(':scope > summary').click()
    return page.locator('#exam-form')

def read_written_material(page):
    return page.evaluate("""async()=> {
        const root=new URL('.',document.baseURI),qualificationId=document.documentElement.dataset.qualification;
        const {createLocalStore}=await import(new URL('src/storage/local.js',root));
        const store=createLocalStore({qualificationId,rootPath:root.pathname});
        try{
            const identity=await store.identity();
            const key=Object.keys(localStorage).find(k=>k.startsWith(`hitomon-v2:${root.pathname}:${identity.owner}:${qualificationId}:written-view`)&&
                (!k.includes('written-view:')||k.endsWith(':'+document.documentElement.dataset.examPart)));
            const id=JSON.parse(localStorage.getItem(key)).currentId;
            const {createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root));
            const workspace=createWorkspaceStore({...identity,rootPath:root.pathname,namespaceName:'written',validate:(_kind,payload)=>payload});
            try{return (await workspace.read()).find(row=>row.id===id).payload.material;}
            finally{await workspace.close();}
        }finally{await store.close();}
    }""")


def check_written_choice(slot, choice_id):
    choice = slot.locator(f'input[value="{choice_id}"]')
    if not choice.is_checked():
        slot.locator(f'label:has(input[value="{choice_id}"])').click()
    assert choice.is_checked()


def fill_written_field(slot, field):
    answers=field['referenceAnswers']
    if field['type']=='answerSet':
        if 'choices' in field:
            ids=[next(choice['id'] for choice in field['choices'] if choice['label']==answer) for answer in answers]
            if field['answerSet'].get('slots'):
                for index, choice in enumerate(ids):
                    slot.locator('[data-answer-set-entry]').nth(index).select_option(choice)
            else:
                for choice in ids:
                    check_written_choice(slot, choice)
        else:
            inputs=slot.locator('[data-answer-set-entry]')
            for index, answer in enumerate(answers):
                if index>=inputs.count():
                    slot.locator('[data-action=written-set-add]').click()
                    inputs.nth(index).wait_for()
                inputs.nth(index).fill(answer)
    elif field['type']=='singleChoice':
        choice=next(choice for choice in field['choices'] if choice['label']==answers[0])
        check_written_choice(slot, choice['id'])
    else:
        slot.locator('textarea, input[type=text]').fill(answers[0])
