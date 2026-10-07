"""Expanded deck: all fields, prior card editions, long meanings, resume and offline."""
import os,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state
ROOT=Path(__file__).resolve().parents[1]
DECK=json.loads((ROOT/'content/ap/flashcards.json').read_text())
URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/')
ART=Path(os.getenv('AP_STUDY_ARTIFACTS','/workspace/scratch/cards-expansion/browser'));ART.mkdir(parents=True,exist_ok=True)
# Only test records are created in an isolated browser profile.
SEED="""async ({card,events=[],reset=false})=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),{createCardStore}=await import(new URL('src/storage/cards.js',root));const main=createLocalStore({rootPath:root.pathname,qualificationId:'ap'}),{owner}=await main.identity();await main.close();const s=createCardStore({rootPath:root.pathname,owner,qualificationId:'ap'});try{if(reset)await s.clear();await s.importEvents(events);await s.write({cardId:card.id,cardVersion:card.version,flipped:false,seen:[],topicId:card.topicId});return await s.read();}finally{await s.close();}}"""
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https://') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':320,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.set_default_timeout(20000)
 pg.goto(URL);pg.locator('.hero-start .primary').wait_for()
 # Keep a real partially answered question while exploring the enlarged deck.
 pg.locator('.hero-start .primary').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();pg.get_by_role('radio').first.check();pg.get_by_role('button',name='ヒントを1つ見る',exact=True).click();pg.get_by_role('button',name='中断',exact=True).click();before=state(pg);assert before['attempts'][-1]['hintCount']==1

 pg.get_by_role('button',name=f"単語帳 · {len(DECK['cards'])}枚",exact=True).click();pg.locator('.flashcard').wait_for()
 topics=sorted({c['topicId'] for c in DECK['cards']})
 assert set(pg.locator('[name=card-topic] option').evaluate_all('(items)=>items.map(i=>i.value)'))==set(topics)|{''}
 for topic in topics:
  pg.locator('[name=card-topic]').select_option(topic);pg.get_by_role('button',name='意味を見る',exact=True).wait_for()
  allowed=[c for c in DECK['cards'] if c['topicId']==topic];front=pg.locator('.flashcard h2').inner_text();assert front in [c['front'] for c in allowed]
  pg.get_by_role('button',name='意味を見る',exact=True).click();pg.locator('.card-back').wait_for();assert pg.locator('.card-back').inner_text() in [c['back'] for c in allowed]
  pg.get_by_role('button',name='もう一度 → 次へ',exact=True).click();pg.get_by_role('button',name='意味を見る',exact=True).wait_for()
 # Old edition events remain exportable, while updated meanings need fresh confirmation.
 dma=next(c for c in DECK['cards'] if c['id']=='dma');assert dma['version']==2
 old={'id':'old-dma-1','cardId':'dma','cardVersion':1,'outcome':'recalled','at':'2026-10-01T01:00:00.000Z'}
 seeded=pg.evaluate(SEED,{'card':dma,'events':[old],'reset':True});assert old in seeded['events']
 pg.reload();pg.get_by_role('button',name='意味を見る',exact=True).wait_for();assert pg.locator('.flashcard h2').inner_text()==dma['front'];assert '確認済み 0 /' in pg.locator('#main').inner_text()
 pg.get_by_role('button',name='意味を見る',exact=True).click();pg.locator('.card-back').wait_for();assert 'Direct Memory Access' in pg.locator('.card-back').inner_text()
 pg.get_by_role('button',name='思い出せた → 次へ',exact=True).click();pg.get_by_role('button',name='意味を見る',exact=True).wait_for()
 revised=pg.evaluate(SEED,{'card':dma});assert any(e['cardId']=='dma' and e['cardVersion']==2 for e in revised['events']);assert old in revised['events']
 # English acronym expansions and the longest meanings wrap at 320px and 200% text.
 longest=sorted(DECK['cards'],key=lambda c:len(c['back']),reverse=True)[:4]
 for i,card in enumerate(longest):
  pg.evaluate(SEED,{'card':card});pg.reload();pg.get_by_role('button',name='意味を見る',exact=True).click();pg.locator('.card-back').wait_for();assert pg.locator('.card-back').inner_text()==card['back']
  pg.evaluate('document.documentElement.style.fontSize="32px"');assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),card['id']
  if i==0:pg.screenshot(path=str(ART/'long-meaning-320-200.png'),full_page=True)
  pg.evaluate('document.documentElement.style.fontSize=""')
 savedfront=pg.locator('.flashcard h2').inner_text();pg.evaluate('navigator.serviceWorker.ready');ctx.set_offline(True);pg.reload();pg.locator('.card-back').wait_for();assert pg.locator('.flashcard h2').inner_text()==savedfront
 assert pg.locator('[name=card-topic] option').count()==18;ctx.set_offline(False)
 assert state(pg)['attempts']==before['attempts'] and state(pg)['session']==before['session']
 assert not errors,errors;b.close()
print('PASS all 17 card fields / prior edition events kept / revised edition rating / long acronym meanings 320px 200% / offline resume / no MCQ record changes')
