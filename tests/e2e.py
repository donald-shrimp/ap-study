import json
import os
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(tempfile.mkdtemp(prefix='ap-study-e2e-'))
URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
KEY='ap-study-mock.v1'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.locator('.quick-start').wait_for()
 assert page.locator('select#session-size').count()==0
 for n in [1,3,5]:
  page.locator(f'.quick-start [data-count="{n}"]').click()
  s=page.evaluate('(k)=>JSON.parse(localStorage.getItem(k))',KEY)
  assert s['session']['goal']==n and s['session']['topic'] is None and len(s['session']['attemptIds'])==1
  page.get_by_role('button',name='← 中断してホームへ').click()
 print('PASS 1, 3, and 5 questions start with one click',flush=True)
 page.locator('.sidebar [data-view=topics]').click();assert page.locator('.topic-card').count()==4
 security=page.locator('.topic-card').filter(has=page.get_by_role('heading',name='セキュリティ',exact=True))
 security.locator('summary').click();security.locator('input').fill('第4章 p.120〜127 <script>alert(1)</script>')
 security.locator('[data-count="2"]').click()
 assert page.get_by_role('heading',name='DNSへの攻撃',exact=True).count()==1
 assert '<script>alert(1)</script>' in page.locator('.reading-context').inner_text()
 page.get_by_role('radio').nth(2).check();page.get_by_role('button',name='ヒントを1つ見る').click();page.reload()
 page.locator('.reading-context').wait_for();assert page.get_by_role('radio').nth(2).is_checked();assert 'セキュリティのみ' in page.locator('.study-toolbar').inner_text()
 page.get_by_role('button',name='この答えで確認する').click();page.get_by_role('button',name='次の問題へ').click()
 assert page.get_by_role('heading',name='DNSの応答を確かめる',exact=True).count()==1
 page.get_by_role('radio').nth(0).check();page.get_by_role('button',name='この答えで確認する').click()
 assert '2問に取り組みました' in page.locator('.session-milestone').inner_text()
 page.get_by_role('button',name='同じ分野をもう一度').click()
 assert page.get_by_role('heading',name='DNSへの攻撃',exact=True).count()==1
 page.get_by_role('button',name='解答を見て学ぶ').click();page.get_by_role('button',name='同じ分野をもう一度').click()
 assert page.get_by_role('heading',name='DNSの応答を確かめる',exact=True).count()==1
 assert page.locator('.question-meta .badge').first.inner_text()=='セキュリティ'
 s=page.evaluate('(k)=>JSON.parse(localStorage.getItem(k))',KEY)
 assert all(a['questionId'] in ['r06h-q36','r06h-q37'] for a in s['attempts'] if a.get('topic'))
 print('PASS textbook range note, scoped question sequence, reload, and scoped repeat',flush=True)
 page.get_by_role('button',name='← 中断してホームへ').click();assert page.get_by_role('heading',name='今日の一歩、達成。').count()==1
 page.locator('.quick-start [data-count="5"]').click();s=page.evaluate('(k)=>JSON.parse(localStorage.getItem(k))',KEY)
 assert s['session']['topic'] is None
 print('PASS all-topic practice clears scope; today reward includes assisted practice',flush=True)
 page.locator('.sidebar [data-view=materials]').click();page.locator('[data-action=start][data-id=r06h-q10]').click()
 page.get_by_role('button',name='ヒントを1つ見る').click();page.get_by_role('radio').nth(3).check();page.get_by_role('button',name='この答えで確認する').click()
 page.locator('.sidebar [data-view=materials]').click();page.locator('[data-action=start][data-id=r06h-q10]').click()
 page.get_by_role('radio').nth(3).check();page.get_by_role('button',name='この答えで確認する').click()
 assert '今回はヒントなし' in page.locator('.result .progress-feedback').inner_text()
 page.locator('.sidebar [data-view=materials]').click();page.locator('[data-action=start][data-id=r06h-q1]').click()
 page.get_by_role('radio').nth(0).check();page.get_by_role('button',name='この答えで確認する').click()
 page.locator('.sidebar [data-view=materials]').click();page.locator('[data-action=start][data-id=r06h-q1]').click()
 page.get_by_role('radio').nth(3).check();page.get_by_role('button',name='この答えで確認する').click()
 assert '前回の不正解から' in page.locator('.result .progress-feedback').inner_text()
 page.locator('.sidebar [data-view=home]').click();page.locator('.achievements summary').click()
 assert '解き直して正解' in page.locator('.achievement-list').inner_text()
 print('PASS hint reduction, recovery feedback, and earned achievements',flush=True)
 page.locator('.sidebar [data-view=history]').click()
 assert '第4章 p.120〜127' in page.locator('#main').inner_text()
 page.get_by_role('button',name='表示・データ',exact=True).click()
 with page.expect_download() as download:page.get_by_role('button',name='学習記録を書き出す').click()
 backup=ROOT/'topic-backup.json';download.value.save_as(str(backup))
 page.on('dialog',lambda d:d.accept());page.locator('#import-state').set_input_files(str(backup))
 page.wait_for_function('document.querySelector("#settings-status").textContent.includes("読み込みました")')
 page.get_by_role('button',name='設定を閉じる',exact=True).click()
 page.locator('.sidebar [data-view=home]').click();page.screenshot(path=str(ROOT/'updated-home-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ROOT/'updated-home-mobile.png'),full_page=True)
 page.locator('.sidebar [data-view=topics]').click();page.screenshot(path=str(ROOT/'updated-topics-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.evaluate('document.documentElement.style.fontSize="32px"')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS notes in history and backup, mobile layout, 200% font, no runtime errors',flush=True)
 b.close()

print("Browser check artifacts:", ROOT)
