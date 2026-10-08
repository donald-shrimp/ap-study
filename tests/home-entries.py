"""Three direct starts: eligibility, exact resume, compact plan and offline behaviour."""
import json,os,shutil,re
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from browser_storage import state,nav,open_plan_ai
ROOT=Path(__file__).resolve().parents[1];URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/')
ART=Path(os.getenv('AP_STUDY_ARTIFACTS','/workspace/scratch/entry-home/browser'));ART.mkdir(parents=True,exist_ok=True)
classification={i['questionId']:i['mode'] for i in json.loads((ROOT/'content/ap/study-context.json').read_text())['items']}
labels={'paperless':'身軽に1問','desk':'書いて考える1問','all':'おまかせで1問'}
def entrance(pg,mode):return pg.locator(f'.study-entrance[data-paper-mode="{mode}"]')
def current(pg):
 s=state(pg);return next(a for a in s['attempts'] if a['id']==s['currentId'])
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.set_default_timeout(20000);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for()
 assert pg.locator('.study-entrance').count()==3 and pg.locator('.hero-start [data-action=paper-mode]').count()==0
 assert '紙・ペンなし' not in pg.locator('.hero-start').inner_text()
 assert pg.locator('.hero-start').bounding_box()['y']<200
 for mode in ['paperless','desk','all']:
  btn=entrance(pg,mode);assert labels[mode] in btn.inner_text();qid=btn.get_attribute('data-id');assert qid
  btn.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);assert a['questionId']==qid and a['entryMode']==mode
  assert state(pg)['session']['paperMode']==mode
  if mode!='all':assert classification[qid]==mode,(mode,qid)
  pg.get_by_role('radio').first.check();pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('button',name='中断',exact=True).click();pg.reload();btn=entrance(pg,mode);btn.wait_for();assert btn.get_attribute('data-action')=='entry-resume' and '続きから' in btn.inner_text();assert btn.get_attribute('data-last-entry')=='true'
  saved=state(pg);btn.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['id']==a['id'] and current(pg)['hintCount']==1 and current(pg)['selected']==0
  pg.get_by_role('button',name='中断',exact=True).click()
 # All three pending questions are distinct records; a paperless question begun in all stays under all.
 assert len(state(pg)['attempts'])==3
 # Completed work returns its entrance to an ordinary start.
 entrance(pg,'all').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);pg.get_by_role('radio').nth(a['questionSnapshot']['answer']).check();pg.get_by_role('button',name='回答する',exact=True).click();pg.get_by_role('button',name='ホーム',exact=True).click();assert entrance(pg,'all').get_attribute('data-action')=='entry-start'
 # Individual desk reclassification retains hints/selection and offers the writing entrance for resume.
 entrance(pg,'paperless').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);pg.get_by_role('button',name='この問題は紙ペンが必要',exact=True).click();assert entrance(pg,'desk').get_attribute('data-id')==a['id'];assert entrance(pg,'paperless').get_attribute('data-id')!=a['id'];entrance(pg,'desk').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['id']==a['id'] and current(pg)['hintCount']==1 and current(pg)['selected']==0;pg.get_by_role('button',name='中断',exact=True).click()
 # A long plan with many focus fields cannot push the essentials below the first mobile screen.
 pg.get_by_role('button',name='計画を登録',exact=True).click();today=datetime.now(ZoneInfo('Asia/Tokyo')).date();date=lambda n:(today+timedelta(days=n)).isoformat();plan=json.loads((ROOT/'schemas/study-plan.example.json').read_text());plan['examDates']=[{'examPartId':'objective','date':date(27)}];phase=plan['phases'][0];phase.update(name='母数を増やして全体像を作る',start=date(0),end=date(11),focusTopicIds=[t['id'] for t in json.loads((ROOT/'content/ap/qualification.json').read_text())['topics']],targets={'completedAttempts':70});phase.pop('weeklyTargets',None);phase.pop('milestones',None)
 open_plan_ai(pg);pg.locator('#plan-json').fill(json.dumps(plan));pg.get_by_role('button',name='検証してプレビュー',exact=True).click();pg.get_by_role('button',name='この内容で登録',exact=True).click();pg.get_by_text('受験日と計画を登録しました。',exact=True).wait_for();nav(pg,'home')
 assert '27日' in pg.locator('.compact-plan').inner_text() and 'この期間' in pg.locator('.compact-plan').inner_text() and '今日：' in pg.locator('.compact-plan').inner_text()
 assert phase['name'] not in pg.locator('.compact-plan').inner_text()
 for width in [320,390]:
  pg.set_viewport_size({'width':width,'height':844});pg.evaluate('document.documentElement.style.fontSize=""');bounds=pg.locator('.home-core').bounding_box();assert bounds['y']+bounds['height']<844,(width,bounds);assert pg.locator('.home-shortcuts').bounding_box()['y']<pg.locator('.compact-plan').bounding_box()['y'];assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth');pg.screenshot(path=str(ART/f'home-plan-{width}.png'),full_page=True)
  pg.evaluate('document.documentElement.style.fontSize="32px"');assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth');pg.screenshot(path=str(ART/f'home-plan-{width}-200.png'),full_page=True)
 pg.evaluate('document.documentElement.style.fontSize=""');chip=pg.locator('.quick-topics [data-action=topic-session]').first;topic=chip.get_attribute('data-topic');chip.click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=current(pg);assert a['questionSnapshot']['topic']==topic and state(pg)['session']['paperMode']=='desk';assert classification[a['questionId']]=='desk' or a['questionId'] in state(pg)['settings']['deskQuestionIds'];pg.get_by_role('button',name='中断',exact=True).click();entrance(pg,'desk').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();saved=current(pg);pg.get_by_role('button',name='中断',exact=True).click();pg.evaluate('navigator.serviceWorker.ready');ctx.set_offline(True);pg.reload();entrance(pg,'desk').wait_for();entrance(pg,'desk').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();assert current(pg)['id']==saved['id'] and state(pg)['session']['paperMode']=='desk';ctx.set_offline(False)
 assert not errors,errors;b.close()
print('PASS three one-click entrances / source eligibility / entrance-owned resume / partial work and personal desk designation retained / compact long plan 320 and 390px / 200% / offline writing resume')
