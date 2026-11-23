"""Compare case controls to the real subject-A UI, including exam disclosure."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
from browser_storage import nav,open_written_case,open_written_field_actions
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-design-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.environ.get('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
def style(el):return el.evaluate('el=>{const s=getComputedStyle(el);return Object.fromEntries(["backgroundColor","color","borderTopColor","fontSize","paddingTop","paddingRight","minHeight"].map(k=>[k,s[k]]));}')
def screenshot(pg,name):
 for width in [320,390,1440]:
  pg.set_viewport_size({'width':width,'height':1000});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,width)
  if width in [390,1440]:pg.screenshot(path=str(ART/(name+'-'+str(width)+'.png')),full_page=False)
 pg.set_viewport_size({'width':390,'height':844})
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(BASE+'ap/?part=objective&entry=home');pg.locator('.quick-start').wait_for();a_start=style(pg.locator('.hero-start .primary'));a_secondary=style(pg.locator('.hero-start .secondary').first);pg.locator('.hero-start').screenshot(path=str(ART/'ap-home.png'))
  assert a_start['backgroundColor']=='rgb(255, 255, 255)' and a_start['color']=='rgb(20, 45, 78)';assert a_secondary['backgroundColor']=='rgb(32, 61, 97)' and a_secondary['color']=='rgb(255, 255, 255)'
  nav(pg,'materials');pg.locator('[data-action=start]').first.click();pg.locator('.question-panel').wait_for();a_back=style(pg.locator('.study-back-button'));a_body=pg.locator('.question-stem').evaluate('e=>getComputedStyle(e).fontSize');a_choice=pg.locator('.choice-text').first.evaluate('e=>getComputedStyle(e).fontSize');a_submit=style(pg.locator('[data-action=submit]'));pg.locator('.question-panel').screenshot(path=str(ART/'ap-question.png'))
  assert a_back['backgroundColor']=='rgb(232, 238, 247)' and a_submit['backgroundColor']=='rgb(8, 125, 121)'
  pg.goto(BASE+'fp2/?part=jafp-practical&entry=home');pg.locator('.quick-start').wait_for();assert style(pg.locator('.hero-start .primary'))==a_start
  assert style(pg.locator('.hero-start .secondary').first)==a_secondary;assert pg.locator('.hero-start select').count()==0;screenshot(pg,'fp-home')
  open_written_case(pg,'fp2-202605-jafp-q01');assert style(pg.locator('.study-back-button'))==a_back;assert pg.locator('.study-toolbar').evaluate('e=>e.firstElementChild.classList.contains("study-back-button")')
  assert pg.locator('.written-item-nav').count()==0;assert pg.locator('.written-body .question-stem').evaluate('e=>getComputedStyle(e).fontSize')==a_body;assert pg.locator('.choice-text').first.evaluate('e=>getComputedStyle(e).fontSize')==a_choice
  expect(pg.locator('.written-individual-actions button:visible')).to_have_count(0)
  expect(pg.locator('.written-items .button.primary:visible')).to_have_count(1)
  open_written_field_actions(pg)
  field=pg.locator('.written-field').first;submit=field.locator('[data-action=written-submit]');assert submit.is_disabled();assert style(pg.locator('[data-action=written-check-item]'))==a_submit
  inputs=field.locator('input[type=radio]');inputs.first.focus();inputs.first.press('ArrowDown');expect(submit).to_be_enabled();assert inputs.nth(1).is_checked();assert field.locator('.choice').nth(1).evaluate('e=>getComputedStyle(e).backgroundColor')!='rgb(255, 255, 255)'
  inputs.first.check();submit.click();field.locator('.written-answer').wait_for();assert field.locator('.wrong-choice').count()==1 and field.locator('.correct-choice').count()==1;assert field.locator('.written-explanation').evaluate('e=>e.open');assert pg.locator('.written-ai-entry [data-action=written-ai]').inner_text()=='AIに聞く';screenshot(pg,'fp-feedback')
  second=pg.locator('.written-field').nth(1)
  open_written_field_actions(pg)
  second.locator('input[type=radio]').first.check()
  second.locator('[data-action=written-submit]').click()
  expect(pg.locator('.written-ai-entry [data-action=written-ai]')).to_have_count(1)
  choices=pg.locator('[name=written-ai-field]')
  field_key=second.get_attribute('data-written-key')
  choices.select_option(field_key)
  pg.locator('[data-action=written-ai]').click()
  expect(pg.locator('#ai-handoff-dialog')).to_be_visible()
  assert second.locator('h3').inner_text() in pg.locator('#ai-handoff-preview').input_value()
  pg.locator('#ai-handoff-close').click()
  open_written_case(pg,'fp2-202605-jafp-q01',mode='exam');open_written_field_actions(pg);field=pg.locator('.written-field').first;field.locator('input').first.check();field.locator('[data-action=written-submit]').click();field.get_by_text('回答済み',exact=True).wait_for();assert field.locator('.badge.good,.badge.wrong,.badge.help,.correct-choice,.wrong-choice,.written-answer,[data-action=written-answer]').count()==0
  pg.goto(BASE+'ap/?part=written&entry=home');pg.locator('.quick-start').wait_for();assert style(pg.locator('.hero-start .primary'))==a_start;open_written_case(pg,'ap-r07h-pm1');assert pg.locator('.written-item-nav [aria-current=step]').count()==1
  field=pg.locator('.written-field').first;answer=field.locator('textarea');assert pg.locator('.written-items .button.primary:not([disabled])').count()==0;answer.fill('デザイン検証用の回答');expect(field.locator('[data-action=written-submit]')).to_be_enabled();assert pg.locator('.written-items .button.primary:not([disabled])').count()==1;pg.reload();pg.locator('.written-layout').wait_for();assert pg.locator('textarea').first.input_value()=='デザイン検証用の回答'
  expect(pg.locator('#main')).not_to_contain_text('2000字')
  expect(field.locator('h3')).to_have_count(0)
  pg.locator('[data-action=written-pane][data-pane=body]').click();expect(pg.locator('.written-body')).to_be_visible();screenshot(pg,'ap-body');pg.locator('[data-action=written-pane][data-pane=questions]').click();screenshot(pg,'ap-fields')
  pg.locator('[data-action=written-submit]').click();expect(pg.locator('.written-answer h4').first).to_be_focused()
  expect(pg.locator('.written-explanation').first).to_have_attribute('open','')
  expect(pg.get_by_role('button',name='次の小問')).to_have_count(0)
  pg.locator('[data-action=written-rate][data-outcome=unsure]').click()
  pg.get_by_role('button',name='次の小問').click()
  expect(pg.locator('.written-item-nav [aria-current=step]')).to_have_text('設問2')
  # Learning text follows A's scale while controls and editable mobile inputs remain usable.
  for width in [320,390,1440]:
   pg.set_viewport_size({'width':width,'height':1000})
   for scale in [50,140]:
    pg.evaluate('(v)=>document.documentElement.style.setProperty("--study-text-scale",v)',str(scale/100));assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    assert pg.locator('.study-back-button').evaluate('e=>e.getBoundingClientRect().height')>=44
  assert not errors,errors;b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({'aHomeMainAndSecondaryStylesMatched':True,'aBackAndSubmitStylesMatched':True,'bodyAndChoiceTypographyMatched':True,'keyboardSelection':True,'wrongAndCorrectFeedback':True,'examNoDisclosure':True,'typedAnswerReload':True,'widths':[320,390,1440],'studyTextSettings':[50,140],'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
print('PASS AP-A design parity / case hierarchy and controls / exam disclosure / keyboard / input resume / responsive and text scale');print('Artifacts:',ART)
