"""Browser regression test for the post-answer AI handoff.

Run after starting: python -m http.server 4173
Then: python tests/ai-handoff-e2e.py
A test-only external route prevents any real AI request or text submission.
"""
import os
import shutil
import time
from playwright.sync_api import sync_playwright
from browser_storage import nav, state

BASE = os.environ.get("AP_STUDY_URL", "http://127.0.0.1:4173/")


def open_answered_question(page):
    page.goto(BASE)
    page.wait_for_function('document.querySelector("#main")?.getAttribute("aria-busy")==="false"')
    nav(page, "home")
    page.locator(".study-entrance").first.wait_for()
    page.locator(".study-entrance").first.click()
    page.locator('[data-action="reveal"]').wait_for()
    assert page.locator('[data-action="ask-ai"]').count() == 0, "AI question button must not be visible before answer"
    page.locator('[data-action="reveal"]').click()
    page.locator('[data-action="ask-ai"]').wait_for()
    assert page.locator('[data-action="next"]').count() == 1, "Normal next-question action must remain"


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=shutil.which("chromium"), headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 390, "height": 844},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Mobile Safari/537.36')
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    copied = []
    copy_times=[]
    def capture_copy(value):
        copied.append(value);copy_times.append(time.monotonic())
    page.expose_function("captureAICopy",capture_copy)

    open_answered_question(page)
    page.locator('[data-action="ask-ai"]').click()
    page.locator("#ai-handoff-dialog[open]").wait_for()
    page.locator("#ai-handoff-detail").fill("式の意味をもっと説明して")
    preview = page.locator("#ai-handoff-preview").input_value()
    before = state(page)
    assert "式の意味をもっと説明して" in preview
    assert "【正解】" in preview
    assert "【私の回答】" in preview
    context.grant_permissions(['clipboard-read','clipboard-write'],origin=page.evaluate('location.origin'))
    context.route('https://chatgpt.com/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<h1>AI handoff navigation fixture</h1>'))
    page.evaluate('navigator.clipboard.writeText("前回コピーした別の文章")')
    page.locator('#ai-handoff-prompt-details>summary').click()
    page.locator('#ai-handoff-copy-only').click()
    page.wait_for_function('document.querySelector("#ai-handoff-status").textContent.includes("質問文をコピーしました")')
    assert page.evaluate('navigator.clipboard.readText()') == preview, "Native Chromium clipboard must receive the exact prompt"

    # Native copying must finish while the study tab is focused, before opening.
    page.evaluate('navigator.clipboard.writeText("前回の文章を再設定")')
    with context.expect_page() as opened:
        page.locator('#ai-handoff-open').click()
    ai=opened.value;ai.wait_for_url('https://chatgpt.com/')
    assert ai.evaluate('window.opener===null'), 'External AI must not control the original tab'
    assert page.url.startswith(BASE) and not page.locator('#ai-handoff-dialog').is_visible()
    page.bring_to_front()
    assert page.evaluate('navigator.clipboard.readText()')==preview
    assert state(page)['currentId']==before['currentId']
    ai.close();page.locator('[data-action="ask-ai"]').click()
    page.locator('#ai-handoff-detail').fill('式の意味をもっと説明して')

    page.locator('[data-ai-provider="gemini"]').click()
    assert "Gemini" in page.locator("#ai-handoff-open").inner_text()
    page.locator('[data-ai-provider="chatgpt"]').click()
    page.evaluate("""() => {
        Object.defineProperty(navigator, 'clipboard', {
            configurable:true,
            value:{writeText: async value => {await window.captureAICopy(value);window.aiCopiedAt=performance.now()}}
        });
    }""")
    elapsed=[]
    def reached_ai(route):
        elapsed.append((time.monotonic()-copy_times[-1])*1000)
        route.fulfill(status=200,content_type="text/html",body="<h1>AI handoff navigation fixture</h1>")
    context.route("https://chatgpt.com/**",reached_ai)
    with context.expect_page() as opened:
        page.locator("#ai-handoff-open").click()
    ai=opened.value;ai.wait_for_url('https://chatgpt.com/')
    assert copied == [preview], "Question must be copied before new-tab navigation"
    assert elapsed[0]>=480, elapsed
    assert page.url.startswith(BASE)
    ai.close();page.reload()
    page.locator('[data-action="ask-ai"]').wait_for()
    after = state(page)
    assert after['currentId'] == before['currentId']
    assert len(after['attempts']) == len(before['attempts'])
    for left, right in zip(before['attempts'], after['attempts']):
        assert {k:v for k,v in left.items() if k not in ['scrollY','updatedAt']} == {k:v for k,v in right.items() if k not in ['scrollY','updatedAt']}, "Returning from AI must retain answers and hints"

    # Clipboard rejection must leave the question and provide the manual text.
    other = context.new_page()
    other.on("pageerror", lambda error: errors.append(str(error)))
    open_answered_question(other)
    other.locator('[data-action="ask-ai"]').click()
    other.evaluate("""() => {
        Object.defineProperty(navigator, 'clipboard', {
            configurable:true,
            value:{writeText: async () => {throw new DOMException('blocked','NotAllowedError')}}
        });
    }""")
    other.locator("#ai-handoff-open").click()
    other.locator("#ai-handoff-manual:visible").wait_for()
    assert len(context.pages)==2, 'Rejected copy must not open any tab'
    assert other.url.startswith(BASE)
    assert "NotAllowedError" in other.locator("#ai-handoff-status").inner_text()
    assert "【問題文】" in other.locator("#ai-handoff-manual-text").input_value()
    other.locator('#ai-handoff-select').click()
    assert other.evaluate('document.activeElement.id') == 'ai-handoff-manual-text'
    other.keyboard.press('Escape')
    assert not other.locator('#ai-handoff-dialog').is_visible()
    assert other.evaluate('document.activeElement.dataset.action') == 'ask-ai'

    # Permission prompts can settle after the dialog has been dismissed.
    # Neither closing nor opening a new dialog may cause a late navigation.
    for dismiss in ['escape', 'close']:
        other.locator('[data-action="ask-ai"]').click()
        other.evaluate("""() => {
            Object.defineProperty(navigator, 'clipboard', {configurable:true,
                value:{writeText: value => new Promise(resolve => {window.finishAICopy=resolve})}});
        }""")
        other.locator('#ai-handoff-open').click()
        assert other.locator('#ai-handoff-open').is_disabled()
        assert other.locator('[data-ai-provider="gemini"]').is_disabled()
        assert other.locator('#ai-handoff-detail').is_disabled()
        if dismiss == 'escape': other.keyboard.press('Escape')
        else: other.locator('#ai-handoff-close').click()
        other.locator('[data-action="ask-ai"]').click()
        other.evaluate('async()=>{window.finishAICopy();await new Promise(r=>setTimeout(r,100))}')
        assert other.url.startswith(BASE), "Canceled clipboard operation must not navigate later"
        assert len(context.pages)==2, 'Canceled pending copy must never open a tab'
        assert other.locator('#ai-handoff-dialog').is_visible()
        assert other.locator('#ai-handoff-open').is_enabled()
        other.locator('#ai-handoff-close').click()

    # Closing during the 500ms settlement window never causes a late redirect.
    other.locator('[data-action="ask-ai"]').click()
    other.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{window.aiDelayCopy=true}}})")
    other.clock.install()
    other.locator('#ai-handoff-open').click()
    other.wait_for_function('Boolean(window.aiDelayCopy)')
    assert other.url.startswith(BASE)
    assert other.locator('#ai-handoff-open').is_disabled()
    other.keyboard.press('Escape')
    other.locator('[data-action="ask-ai"]').click()
    other.clock.run_for(600)
    assert other.url.startswith(BASE) and other.locator('#ai-handoff-dialog').is_visible()
    assert len(context.pages)==2, 'Cancel during settlement must close the reserved tab'
    other.locator('#ai-handoff-close').click()
    other.clock.resume()

    # All providers use the same guarded clipboard-first route.
    other.expose_function('captureAICopy',lambda value:copied.append(value))
    for provider, url in [('gemini','https://gemini.google.com/'),('claude','https://claude.ai/')]:
        other.locator('[data-action="ask-ai"]').click()
        other.locator(f'[data-ai-provider="{provider}"]').click()
        other.evaluate("""() => {Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>await window.captureAICopy(value)}})}""")
        context.route(url+'**',lambda route:route.fulfill(status=200,content_type='text/html',body='<h1>Provider fixture</h1>'))
        with context.expect_page() as opened:
            other.locator('#ai-handoff-open').click()
        ai=opened.value;ai.wait_for_url(url)
        assert ai.evaluate('window.opener===null') and other.url.startswith(BASE)
        ai.close();other.locator('[data-action="ask-ai"]').wait_for()

    # A browser blocking asynchronous popups must never replace the study tab.
    other.locator('[data-action="ask-ai"]').click()
    other.locator('[data-ai-provider="chatgpt"]').click()
    other.evaluate('window.realOpen=window.open;window.open=()=>null')
    other.locator('#ai-handoff-open').click()
    other.locator('#ai-handoff-manual:visible').wait_for()
    assert '別タブを開けません' in other.locator('#ai-handoff-status').inner_text()
    assert other.url.startswith(BASE) and len(context.pages)==2
    other.evaluate('()=>{window.open=window.realOpen}')
    with context.expect_page() as opened:
        other.locator('#ai-handoff-fallback').click()
    ai=opened.value;ai.wait_for_url('https://chatgpt.com/');ai.close()
    assert other.url.startswith(BASE)

    # Closing the reserved tab is cancellation, rather than a silent redirect.
    other.locator('[data-action="ask-ai"]').click()
    other.clock.install()
    with context.expect_page() as opened:
        other.locator('#ai-handoff-open').click()
    opened.value.close();other.clock.run_for(600)
    other.locator('#ai-handoff-manual:visible').wait_for()
    assert 'タブが閉じられました' in other.locator('#ai-handoff-status').inner_text()
    assert other.url.startswith(BASE) and len(context.pages)==2
    other.clock.resume()
    assert not errors, "Browser errors: " + repr(errors)
    browser.close()
    print("AI handoff browser regression passed: native clipboard before new tab, opener detached, mobile, gating, 500ms copy-to-navigation delay, cancellation closes reserved tab, all providers, original tab retains records after reload, popup blocked/manual retry, keyboard, cancel/reopen during pending copy, user closes tab.")
