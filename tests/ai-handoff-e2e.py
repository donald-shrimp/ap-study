"""Browser regression test for the post-answer AI handoff.

Run after starting: python -m http.server 4173
Then: python tests/ai-handoff-e2e.py
A test-only external route prevents any real AI request or text submission.
"""
import os
import shutil
from playwright.sync_api import sync_playwright

BASE = os.environ.get("AP_STUDY_URL", "http://127.0.0.1:4173/")


def open_answered_question(page):
    page.goto(BASE)
    page.locator(".study-entrance").first.wait_for()
    page.locator(".study-entrance").first.click()
    page.locator('[data-action="reveal"]').wait_for()
    assert page.locator('[data-action="ask-ai"]').count() == 0, "AI question button must not be visible before answer"
    page.locator('[data-action="reveal"]').click()
    page.locator('[data-action="ask-ai"]').wait_for()
    assert page.locator('[data-action="next"]').count() == 1, "Normal next-question action must remain"


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=shutil.which("chromium"), headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 390, "height": 844})
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
    assert "式の意味をもっと説明して" in preview
    assert "【正解】" in preview
    assert "【私の回答】" in preview

    page.locator('[data-ai-provider="gemini"]').click()
    assert "Gemini" in page.locator("#ai-handoff-open").inner_text()
    page.locator('[data-ai-provider="chatgpt"]').click()
    page.evaluate("""() => {
        Object.defineProperty(navigator, 'clipboard', {
            configurable:true,
            value:{writeText: async value => await window.captureAICopy(value)}
        });
    }""")
    page.route("https://chatgpt.com/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<h1>AI handoff navigation fixture</h1>"))
    page.locator("#ai-handoff-open").click()
    page.wait_for_url("https://chatgpt.com/")
    assert copied == [preview], "Question must be copied before same-tab navigation"

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
    assert not errors, "Browser errors: " + repr(errors)
    browser.close()
    print("AI handoff browser regression passed: mobile, gating, clipboard first, fallback.")
