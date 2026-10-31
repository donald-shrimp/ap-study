"""Actual selection, including answer-revealing hints, controls the result colour."""
import json,shutil,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import nav
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/qualifications/ap/manifest.json').read_text())
questions=[q for p in manifest['packs'] for q in json.loads((ROOT/'data/qualifications/ap'/p['url']).read_text())]
q=next(q for q in questions if q['id']=='r04h-q18')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  for width in (320,390,1440):
   for mode in ('correct','incorrect','reveal-empty','hint-correct','hint-wrong'):
    ctx=browser.new_context(viewport={'width':width,'height':900});pg=ctx.new_page();pg.goto(f'http://127.0.0.1:{server.server_port}/ap-study/ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for()
    nav(pg,'materials');pg.locator('[data-action=reset-filters]').click();pg.locator('[name=year]').select_option(str(q['year']));pg.locator('[name=season]').select_option(q['season']);pg.locator('[name=query]').fill(q['title']);pg.locator(f'[data-action=start][data-id="{q["id"]}"]').click();pg.locator('.choices').wait_for()
    if mode.startswith('hint-'):
     for _ in q['hints']:pg.locator('[data-action=hint]').click()
    if mode=='reveal-empty':pg.locator('[data-action=reveal]').click()
    else:
     answer=q['answer'] if mode in ('correct','hint-correct') else (q['answer']+1)%len(q['choices'])
     pg.get_by_role('radio').nth(answer).check();pg.locator('[data-action=submit]').click()
    result=pg.locator('#result');result.wait_for();expected='result-correct' if mode in ('correct','hint-correct') else 'result-incorrect'
    assert expected in result.get_attribute('class'),(width,mode,result.get_attribute('class'))
    assert result.evaluate('(el)=>getComputedStyle(el).backgroundColor')==('rgb(237, 248, 244)' if expected=='result-correct' else 'rgb(255, 243, 244)')
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,mode)
    ctx.close()
  browser.close()
finally:server.shutdown()
print('PASS objective result colours: correct, incorrect, reveal without selection, answer-revealing hint with correct/incorrect selection; 320/390/1440px')
