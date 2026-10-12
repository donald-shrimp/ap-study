"""Browser regression test for the post-answer AI handoff.

Run after starting: python -m http.server 4173
Then: python tests/ai-handoff-e2e.py
A test-only external route prevents any real AI request or text submission.
"""
import os
import shutil
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
    page.expose_function("captureAICopy", lambda value: copied.append(value))

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
    page.evaluate('navigator.clipboard.writeText("前回コピーした別の文章")')
    page.locator('#ai-handoff-prompt-details>summary').click()
    page.locator('#ai-handoff-copy-only').click()
    page.wait_for_function('document.querySelector("#ai-handoff-status").textContent.includes("質問文をコピーしました")')
    assert page.evaluate('navigator.clipboard.readText()') == preview, "Native Chromium clipboard must receive the exact prompt"
    assert page.url.startswith(BASE), "Copying alone must never navigate"
    assert page.locator('#ai-handoff-open').inner_text() == 'ChatGPTを開く ↗'

    page.locator('[data-ai-provider="gemini"]').click()
    assert "Gemini" in page.locator("#ai-handoff-open").inner_text()
    page.locator('[data-ai-provider="chatgpt"]').click()
    # Editing after a copy invalidates readiness; never open with stale text.
    page.locator('#ai-handoff-detail').fill('式の意味をもっと説明して。例も見たい')
    preview=page.locator('#ai-handoff-preview').input_value()
    assert page.locator('#ai-handoff-open').inner_text() == '質問文をコピー'
    page.evaluate("""() => {
        Object.defineProperty(navigator, 'clipboard', {
            configurable:true,
            value:{writeText: async value => await window.captureAICopy(value)}
        });
    }""")
    page.route("https://chatgpt.com/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<h1>AI handoff navigation fixture</h1>"))
    page.locator("#ai-handoff-open").click()
    page.wait_for_function('document.querySelector("#ai-handoff-open").textContent.includes("ChatGPTを開く")')
    assert page.url.startswith(BASE)
    assert copied == [preview], "Copy must finish before a separate open gesture"
    page.locator("#ai-handoff-open").click()
    page.wait_for_url("https://chatgpt.com/")
    assert copied == [preview], "Question must be copied before same-tab navigation"
    page.go_back()
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
    other.route("https://chatgpt.com/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<h1>Unexpected late navigation</h1>"))
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
        assert other.locator('#ai-handoff-dialog').is_visible()
        assert other.locator('#ai-handoff-open').is_enabled()
        other.locator('#ai-handoff-close').click()

    # All providers use the same guarded clipboard-first route.
    other.expose_function('captureAICopy',lambda value:copied.append(value))
    for provider, url in [('gemini','https://gemini.google.com/'),('claude','https://claude.ai/')]:
        other.locator('[data-action="ask-ai"]').click()
        other.locator(f'[data-ai-provider="{provider}"]').click()
        other.evaluate("""() => {Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>await window.captureAICopy(value)}})}""")
        other.route(url+'**',lambda route:route.fulfill(status=200,content_type='text/html',body='<h1>Provider fixture</h1>'))
        other.locator('#ai-handoff-open').click()
        other.wait_for_function('document.querySelector("#ai-handoff-open").textContent.includes("を開く")')
        assert other.url.startswith(BASE)
        other.locator('#ai-handoff-open').click()
        other.wait_for_url(url)
        other.go_back();other.locator('[data-action="ask-ai"]').wait_for()
    assert not errors, "Browser errors: " + repr(errors)
    browser.close()
    print("AI handoff browser regression passed: native clipboard, separate copy/open gestures, edited-text invalidation, mobile, gating, all providers, return preserves records, fallback, keyboard, cancel/reopen during pending copy.")
