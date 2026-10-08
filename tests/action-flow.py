"""Action-first UI using real persisted attempts, plans and diagnostic slots."""
import json, shutil, os
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from browser_storage import state,nav,open_plan_ai
ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
ART=Path(os.environ.get('AP_STUDY_ARTIFACTS','/workspace/scratch/action-implementation'));ART.mkdir(exist_ok=True)
today=datetime.now(ZoneInfo('Asia/Tokyo')).date()
date=lambda n:(today+timedelta(days=n)).isoformat()
plan=json.loads((ROOT/'schemas/study-plan.example.json').read_text())
plan['examDates']=[{'examPartId':'objective','date':date(28)}]
phase=plan['phases'][0];phase.update(start=date(0),end=date(11),focusTopicIds=['database'])
phase['weeklyTargets']=[{'id':'week-1','start':date(0),'end':date(6),'completedAttempts':10}]
phase['milestones']=[{'id':'mock','name':'手元の教材で模試','date':date(10),'examPartId':'objective','completed':False}]
def register(page,value):
 open_plan_ai(page);page.locator('#plan-json').fill(json.dumps(value));page.get_by_role('button',name='検証してプレビュー',exact=True).click();page.get_by_role('button',name='この内容で登録',exact=True).click();page.get_by_text('受験日と計画を登録しました。',exact=True).wait_for()
def current(page):
 s=state(page);return next(a for a in s['attempts'] if a['id']==s['currentId'])
def answer(page,correct=True):
 a=current(page);q=a['questionSnapshot'];page.get_by_role('radio').nth(q['answer'] if correct else (q['answer']+1)%len(q['choices'])).check();page.get_by_role('button',name='回答する',exact=True).click();page.locator('#result-heading').wait_for()
def open_q(page,id):
 nav(page,'materials');page.locator('[data-action=reset-filters]').click();q=next(q for q in json.loads((ROOT/'data/questions.json').read_text()) if q['id']==id);page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title']);page.locator(f'[data-action=start][data-id="{id}"]').click();page.get_by_role('button',name='回答する',exact=True).wait_for()
with sync_playwright() as p:
 options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**options);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];requests=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('request',lambda r:requests.append(r.url));pg.on('dialog',lambda d:d.accept());pg.goto(URL)
 pg.set_default_timeout(15000);main=pg.locator('.hero-start .primary');main.wait_for();assert main.bounding_box()['y']+main.bounding_box()['height']<844
 assert pg.locator('.sidebar .nav-item').count()==3
 pg.get_by_role('button',name='計画を登録',exact=True).click();assert not pg.locator('#plan-editor').evaluate('(d)=>d.open') and not pg.locator('#plan-ai').evaluate('(d)=>d.open');assert not pg.locator('[name=exam-objective]').is_visible();register(pg,plan)
 nav(pg,'home');assert '28日' in pg.locator('.planning-entry').inner_text();assert 'データベース' in pg.locator('.planning-entry').inner_text();assert 'あと10回' in pg.locator('.week-progress').inner_text()
 assert 'データベース' in pg.locator('.plan-next').inner_text();pg.locator('.quick-topics [data-action=topic-session][data-topic="データベース"]').click();a=current(pg);candidate=a['questionId'];assert a['questionSnapshot']['topicId']=='database';assert state(pg)['session']['topicId']=='database';answer(pg,False);pg.get_by_role('button',name='もう1問',exact=True).click();assert current(pg)['questionSnapshot']['topicId']=='database'
 # Changing the saved plan mid-session cannot silently change the next question's scope.
 state(pg);other=ctx.new_page();other.goto(URL);other.get_by_role('button',name='回答する',exact=True).wait_for();nav(other,'home');other.get_by_role('button',name='計画を見る',exact=True).click();changed=json.loads(json.dumps(plan));changed['phases'][0]['focusTopicIds']=['network'];register(other,changed);other.close();pg.reload();pg.get_by_role('button',name='回答する',exact=True).wait_for()
 answer(pg);pg.get_by_role('button',name='もう1問',exact=True).click();assert current(pg)['questionSnapshot']['topicId']=='database';pg.get_by_role('button',name='中断',exact=True).click()
 # Normal resume is the main action even with a diagnostic checkpoint.
 paused=state(pg)['attempts'][-1]['id'];pg.get_by_role('button',name='実力診断（30問）',exact=True).click();pg.get_by_role('button',name='30問の診断をはじめる',exact=True).click();pg.locator('[name=diagnostic-answer]').first.wait_for();assert pg.locator('.hint-section').count()==0;pg.get_by_role('button',name='中断',exact=True).click();assert pg.locator('.hero-start .primary').get_attribute('data-action')=='entry-resume';assert pg.locator('.hero-start .primary').get_attribute('data-id')==paused;assert pg.get_by_role('button',name='診断の続きから',exact=True).is_visible()
 pg.locator('.hero-start .primary').click();assert state(pg)['currentId']==paused;pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('radio').nth(current(pg)['questionSnapshot']['answer']).check();pg.get_by_role('button',name='中断',exact=True).click();pg.reload();pg.locator('.hero-start .primary[data-action=entry-resume]').click();assert current(pg)['hintCount']==1 and pg.get_by_role('radio').nth(current(pg)['questionSnapshot']['answer']).is_checked();answer(pg);pg.get_by_role('button',name='ホーム',exact=True).click()
 # The same question's latest completed result replaces the old one in the graph.
 id=candidate;open_q(pg,id);answer(pg);pg.get_by_role('button',name='ホーム',exact=True).click();nav(pg,'topics');card=pg.locator('#field-database');before=card.locator('.field-score').inner_text();assert '記録少なめ' in card.inner_text();normal_count=sum(a['completedAt'] is not None and a['questionSnapshot']['topicId']=='database' for a in state(pg)['attempts']);assert normal_count>=3
 open_q(pg,id);pg.get_by_role('button',name='解答を見る',exact=True).click();pg.locator('#result-heading').wait_for()
 nav(pg,'topics');card=pg.locator('#field-database');after=card.locator('.field-score').inner_text();assert before.split(' / ')[1]==after.split(' / ')[1];assert '解答閲覧 1' in card.inner_text()
 pg.locator('[data-action=field-mode][data-mode=diagnostic]').click();assert '完了した診断はありません' in pg.locator('#main').inner_text();assert '未確認' in pg.locator('#field-database').inner_text()
 nav(pg,'home');pg.get_by_role('button',name='診断の続きから',exact=True).click();pg.locator('[name=diagnostic-answer]').first.check();pg.get_by_role('button',name='回答して次へ',exact=True).click();pg.get_by_role('button',name='ここまでで診断終了',exact=True).click();nav(pg,'topics');pg.locator('[data-action=field-mode][data-mode=diagnostic]').click();assert '1 / 30問に回答' in pg.locator('.field-overview').inner_text();assert sum(int(t.split(' / ')[-1].split('問')[0]) for t in pg.locator('.field-score').all_inner_texts())==1
 pg.locator('[data-action=field-mode][data-mode=learning]').click();assert pg.locator('#field-database .field-score').inner_text()==after
 for view in ['home','topics','history']:
  nav(pg,view);pg.evaluate('document.documentElement.style.fontSize="32px"');assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),view;pg.screenshot(path=str(ART/f'{view}-200.png'),full_page=True);pg.evaluate('document.documentElement.style.fontSize=""')
 nav(pg,'home');pg.screenshot(path=str(ART/'home-plan.png'),full_page=True);pg.get_by_role('button',name='計画を見る',exact=True).click();assert not pg.locator('#plan-editor').evaluate('(d)=>d.open');pg.screenshot(path=str(ART/'plan-overview.png'),full_page=True)
 assert not errors,errors;b.close()
print('PASS visible candidate opens exact question / plan scope frozen during session / normal resume beats diagnostic / hints and selection persist / latest-question graph deduplicates / diagnostic separated / overview before edit / 390px 200%')
