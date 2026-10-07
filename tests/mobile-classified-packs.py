"""Every classified exam starts paperless questions and refuses writing cases."""
import os,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state,nav
ROOT=Path(__file__).resolve().parents[1]
URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/')
questions={q['id']:q for q in json.loads((ROOT/'data/questions.json').read_text())}
context=json.loads((ROOT/'content/ap/study-context.json').read_text())
def current(page):
 s=state(page);return next(a for a in s['attempts'] if a['id']==s['currentId'])
def locate(page,q):
 nav(page,'materials');page.locator('[data-action=reset-filters]').click();page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title']);return page.locator(f'[data-action=start][data-id="{q["id"]}"]')
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844});page=ctx.new_page();page.set_default_timeout(20000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL);page.locator('.hero-start .primary').wait_for();page.wait_for_function('navigator.serviceWorker.controller');page.locator('[data-action=paper-mode][data-mode=paperless]').click();page.locator('[data-mode=paperless][aria-pressed=true]').wait_for();paperless=sum(i['mode']=='paperless' for i in context['items']);assert f'原本確認済みの{paperless}問' in page.locator('.hero-start').inner_text()
 visited=set()
 for exam in context['completedExamIds']:
  items=[i for i in context['items'] if i['questionId'].startswith(exam+'-q')];assert len(items)==80
  readable=next(i for i in items if i['mode']=='paperless');q=questions[readable['questionId']];locate(page,q).click();page.get_by_role('button',name='回答する',exact=True).wait_for();assert current(page)['questionId']==q['id'];assert state(page)['session']['paperMode']=='paperless';page.locator('.source-question img').evaluate_all('(images)=>Promise.all(images.map(img=>img.decode()))');visited.add(q['id']);page.locator('[data-action=hint]').click();page.get_by_role('radio').first.check();page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='続きから',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for();assert current(page)['hintCount']==1 and page.get_by_role('radio').first.is_checked();page.get_by_role('button',name='中断',exact=True).click()
  writing=next((i for i in items if i['mode']=='desk'),None)
  if writing:
   button=locate(page,questions[writing['questionId']]);before=len(state(page)['attempts']);button.click();page.get_by_text('この問題は紙・ペンなしの候補ではありません。ホームで「すべて」に切り替えると解けます。記録は変更していません。',exact=True).wait_for();assert len(state(page)['attempts'])==before
  print('PASS',exam,'paperless source / hint-selection resume / writing excluded',flush=True)
 nav(page,'home');page.get_by_role('button',name='続きから',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for();ctx.set_offline(True);page.reload();page.get_by_role('button',name='回答する',exact=True).wait_for();assert current(page)['hintCount']==1 and page.get_by_role('radio').first.is_checked();page.get_by_role('button',name='中断',exact=True).click();candidate=page.locator('.hero-start [data-action=start-session]').first
 if candidate.count():assert candidate.get_attribute('data-id') in visited
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844});page.evaluate('document.documentElement.style.fontSize="32px"');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors;b.close()
print('PASS all classified exams / offline cached-only candidate / preserved partial work / 320px 200%')
