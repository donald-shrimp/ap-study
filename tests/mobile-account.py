"""Real Firebase Auth account changes keep local flashcard namespaces apart."""
import json,shutil,uuid
from pathlib import Path
DECK_COUNT=len(json.loads((Path(__file__).resolve().parents[1]/'content/ap/flashcards.json').read_text())['cards'])
from playwright.sync_api import sync_playwright
URL='http://127.0.0.1:4173/?firebase-emulator=1'
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる').click()
def login(page,email):
 settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 popup=event.value;popup.wait_for_url('**/emulator/auth/handler?**');popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
 if popup.get_by_text(email,exact=True).count():popup.get_by_text(email,exact=True).click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('Card test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');close(page)
def logout(page):
 settings(page);page.locator('#google-logout').click();page.wait_for_function('!document.getElementById("google-login").disabled');close(page)
def cards(page):page.get_by_role('button',name=f'単語帳 · {DECK_COUNT}枚',exact=True).click();page.locator('.flashcard').wait_for()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context();page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL);page.locator('.hero-start .primary').wait_for();cards(page);page.get_by_role('button',name='意味を見る',exact=True).click();page.get_by_role('button',name='もう一度 → 次へ',exact=True).click();page.wait_for_function('document.querySelector("#main").textContent.includes("確認済み 1")');page.get_by_role('button',name='ホーム',exact=True).click()
 email='cards-'+uuid.uuid4().hex+'@example.test';login(page,email);cards(page);assert '確認済み 0' in page.locator('#main').inner_text();page.get_by_role('button',name='意味を見る',exact=True).click();page.get_by_role('button',name='思い出せた → 次へ',exact=True).click();page.wait_for_function('document.querySelector("#main").textContent.includes("確認済み 1")');page.reload();page.locator('.flashcard').wait_for();assert 'また確認 0' in page.locator('#main').inner_text()
 logout(page);cards(page);assert '確認済み 1' in page.locator('#main').inner_text() and 'また確認 1' in page.locator('#main').inner_text();page.get_by_role('button',name='ホーム',exact=True).click();login(page,email);cards(page);assert '確認済み 1' in page.locator('#main').inner_text() and 'また確認 0' in page.locator('#main').inner_text()
 assert not errors,errors;b.close()
print('PASS real Auth guest/UID separation / guest cards not silently imported / logout restores own deck / reload restores signed-in checkpoint')
