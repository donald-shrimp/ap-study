import json,os,shutil,tempfile,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state as stored_state, write_state
ROOT=Path(tempfile.mkdtemp(prefix='ap-study-e2e-'))
URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')
KEY='ap-study-mock.v1'
bank=json.loads((Path(__file__).resolve().parents[1]/'data/questions.json').read_text());by_id={q['id']:q for q in bank}
reveal_fixture=next(q for q in bank if not q['hints'][0]['revealsAnswer'] and q['hints'][1]['revealsAnswer'])
pending_fixture=next(q for q in bank if q['enrichment']=='topic-guide' and q['answer']!=0 and q['sourceImages'])
pending_id=pending_fixture['id']
pending_hint_fixture=next(q for q in bank if q['enrichment']=='topic-guide' and q['id']!=pending_id and not q['hints'][0]['revealsAnswer'])
reviewed_count=sum(q['enrichment']=='reviewed' for q in bank)
complete_exams=[file.stem for file in (Path(__file__).resolve().parents[1]/'data/lessons').glob('*.json')]
with sync_playwright() as p:
 options={'executable_path':shutil.which('chromium'),'headless':True,'args':['--no-sandbox']}
 if URL.startswith('https://') and os.environ.get('HTTPS_PROXY'):options['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**options);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.locator('.quick-start').wait_for()
 def state():
  return stored_state(page)
 def nav(view):page.locator(f'.sidebar [data-view={view}]').click()
 def open_q(id):
  nav('materials');page.locator('[data-action=reset-filters]').click();q=by_id[id]
  page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=query]').fill(q['title'])
  page.locator(f'[data-action=start][data-id="{id}"]').click();page.wait_for_function('document.querySelector("#main").getAttribute("aria-busy")!=="true"')
 def answer(index=None):
  s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);correct=by_id[a['questionId']]['answer']
  page.get_by_role('radio').nth(correct if index is None else index).check();page.get_by_role('button',name='回答する',exact=True).click()
 for n in [1,3,5]:
  page.locator(f'.quick-start [data-count="{n}"]').click();s=state();assert s['session']['goal']==n and s['session']['topic'] is None
  page.get_by_role('button',name='中断',exact=True).click()
 print('PASS 1 / 3 / 5 start with one click',flush=True)
 nav('materials');assert page.locator('.page-heading .badge').inner_text()=='800問';assert page.locator('#catalog-results .row').count()==20
 page.locator('[name=year]').select_option('2022');page.locator('[name=season]').select_option('spring')
 assert page.locator('.catalog-count').inner_text().startswith('80問');page.get_by_role('button',name='次の20問').click();assert '21〜40' in page.locator('.catalog-count').inner_text()
 page.locator('[name=query]').fill('存在しない検索条件ABCXYZ');assert page.locator('#catalog-results .row').count()==0
 page.locator('[data-action=reset-filters]').click();page.locator('[name=query]').fill('DNS');assert page.locator('#catalog-results .row').count()>0
 page.locator('[data-action=reset-filters]').click();page.locator('[name=query]').fill('二乗のビット数');assert page.locator('[data-action=start][data-id=r04a-q1]').count()==1
 page.locator('[data-action=reset-filters]').click();page.locator('[name=enriched]').check();assert page.locator('#catalog-results .row').count()==20;assert page.locator('.catalog-count').inner_text().startswith(f'{reviewed_count}問')
 print(f'PASS 800-question list / year-season filters / pagination / no results / OCR keyword search / {reviewed_count} reviewed',flush=True)
 for exam in complete_exams:
  page.locator('[data-action=reset-filters]').click();q=by_id[f'{exam}-q1']
  page.locator('[name=year]').select_option(str(q['year']));page.locator('[name=season]').select_option(q['season']);page.locator('[name=enriched]').check()
  assert page.locator('.catalog-count').inner_text().startswith('80問'),exam
 nav('topics');assert page.locator('.topic-card').count()==17
 security=page.locator('.topic-card').filter(has=page.get_by_role('heading',name='セキュリティ',exact=True));security.locator('summary').click();security.locator('input').fill('第4章 p.120 <script>alert(1)</script>');security.locator('[data-count="3"]').click()
 scoped=[]
 for i in range(3):
  s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);scoped.append(a['questionId']);assert by_id[a['questionId']]['topic']=='セキュリティ'
  assert '<script>alert(1)</script>' in page.locator('.reading-context').inner_text()
  if i==0:
   page.get_by_role('button',name='ヒントを1つ見る').click();page.get_by_role('radio').nth(by_id[a['questionId']]['answer']).check();state();page.reload();page.locator('.reading-context').wait_for();assert page.get_by_role('radio').nth(by_id[a['questionId']]['answer']).is_checked();assert 'セキュリティのみ' in page.locator('.study-toolbar').inner_text()
  answer()
  if i<2:page.get_by_role('button',name='次の問題',exact=True).click()
 assert len(set(scoped))==3 and '3問の目安完了' in page.locator('.session-milestone').inner_text()
 page.get_by_role('button',name='終了',exact=True).click();page.locator('.quick-start [data-count="1"]').click();assert state()['session']['topic'] is None
 print('PASS textbook note / three different scoped questions / hint-selection resume / scope reset',flush=True)
 open_q('r06h-q10');page.get_by_role('button',name='ヒントを1つ見る').click();answer();open_q('r06h-q10');answer();assert 'ヒントなしで正解' in page.locator('.result .progress-feedback').inner_text()
 open_q('r06h-q1');answer(0);open_q('r06h-q1');answer();assert '不正解 → 自力で正解' in page.locator('.result .progress-feedback').inner_text()
 page.get_by_role('button',name='ヒントを1つ見る').click();s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['status']=='correct' and a['hintsBeforeAnswer']==0 and a['hintEvents'][-1]['phase']=='after'
 nav('home');page.locator('.achievements summary').click();assert '解き直して正解' in page.locator('.achievement-list').inner_text()
 print('PASS individual hints / wrong-to-correct recovery / motivation / after-answer hints',flush=True)
 # A complete 2025 spring lesson and its staged hints survive resume.
 open_q('r07h-q30');assert page.locator('.hint-head h3').inner_text()=='ヒント'
 page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
 page.get_by_role('button',name='次のヒントを見る',exact=True).click()
 page.get_by_role('button',name='次のヒントを見る',exact=True).click()
 assert '1,500−20−20' in page.locator('#hints').inner_text()
 snapshot=next(a for a in state()['attempts'] if a['id']==state()['currentId'])['materialSnapshot']
 assert snapshot['hintStatus']=='individual' and snapshot['enrichment']=='reviewed' and snapshot['choiceReasons']==by_id['r07h-q30']['choiceReasons']
 page.reload();page.locator('.hint-box').first.wait_for();assert page.locator('.hint-box').count()==3
 answer();s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['status']=='assisted' and a['hintsBeforeAnswer']==3
 # New lessons have four reasons and no pending-explanation label.
 assert page.locator('.reason-list li').count()==4 and '個別の解答解説は未追加' not in page.locator('.result').inner_text()
 # A fully specified AVL result is warned about before it is opened.
 open_q('r07h-q6');page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
 page.get_by_role('button',name='次のヒントを見る',exact=True).click()
 page.get_by_role('button',name='次のヒントを見る（答えを含む）',exact=True).click();answer()
 a=next(a for a in state()['attempts'] if a['id']==state()['currentId']);assert a['status']=='revealed' and a['hintsBeforeAnswer']==3
 # A sample from each newly completed exam is persisted and graded with reveal flags.
 for exam in sorted(set(complete_exams)-{'r07h'}):
  candidates=[q for q in bank if q['id'].startswith(exam+'-')]
  samples=[next((q for q in candidates if not any(h['revealsAnswer'] for h in q['hints'])),candidates[0]),next(q for q in candidates if any(h['revealsAnswer'] for h in q['hints']))]
  for q in samples:
   open_q(q['id'])
   for stage,hint in enumerate(q['hints']):
    buttons=page.locator('[data-action=hint]');assert buttons.count()==1
    assert ('答えを含む' in buttons.inner_text())==hint['revealsAnswer']
    buttons.click();assert page.locator('.hint-box').count()==stage+1
    assert hint['text'] in page.locator('#hints').inner_text()
    if stage==0:
     page.get_by_role('radio').nth(q['answer']).check();page.get_by_role('button',name='中断',exact=True).click()
     page.get_by_role('button',name='再開する',exact=True).click();state();page.reload();page.locator('.hint-box').wait_for()
     assert page.get_by_role('radio').nth(q['answer']).is_checked() and page.locator('.hint-box').count()==1
   answer();a=next(a for a in state()['attempts'] if a['id']==state()['currentId'])
   expected='revealed' if any(h['revealsAnswer'] for h in q['hints']) else 'assisted'
   assert a['status']==expected and a['hintsBeforeAnswer']==3,q['id']
   assert a['materialSnapshot']['choiceReasons']==q['choiceReasons'] and page.locator('.reason-list li').count()==4
   assert q['summary'] in page.locator('.result').inner_text() and '個別の解答解説は未追加' not in page.locator('.result').inner_text()
   open_q(q['id']);a=next(a for a in state()['attempts'] if a['id']==state()['currentId'])
   assert a['hintCount']==0 and a['selected'] is None and not a['answerViewedBefore']
 print('PASS complete-exam 80-question filters / new lessons / all three stages / reveal warning / pause-resume / saved choice reasons / closed retry',flush=True)
 # Hints also remain available for questions whose full explanation is pending.
 open_q(pending_hint_fixture['id']);page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
 a=next(a for a in state()['attempts'] if a['id']==state()['currentId']);assert a['materialSnapshot']['enrichment']=='topic-guide'
 page.reload();page.locator('.hint-box').wait_for();assert page.locator('.hint-box').count()==1
 # An answer-revealing hint is labelled before opening and counts as answer viewing.
 open_q(reveal_fixture['id']);page.get_by_role('button',name='ヒントを1つ見る',exact=True).click()
 page.get_by_role('button',name='次のヒントを見る（答えを含む）',exact=True).click();answer()
 s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['status']=='revealed' and a['answerViewedBefore'] and a['hintsBeforeAnswer']==2
 nav('review');assert page.locator(f'[data-action=start][data-id="{reveal_fixture["id"]}"]').count()==1
 # Reproduce the reported question reopened with an older common guide.
 open_q('r07h-q18');page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();page.get_by_role('radio').nth(1).check();page.locator('#confidence').check()
 legacy=state();a=next(a for a in legacy['attempts'] if a['id']==legacy['currentId']);old_id=a['id']
 a['materialSnapshot'].pop('hintStatus');a['materialSnapshot']['enrichment']='topic-guide';a['materialSnapshot']['hints'][0]['text']='以前の分野共通ガイド'
 # Prevent the old page's pagehide handler from overwriting this fixture.
 write_state(page,legacy);page.reload();page.locator('.hint-head h3').wait_for()
 assert '分野共通' in page.locator('.hint-head h3').inner_text() and '以前の分野共通ガイド' in page.locator('.hint-box').inner_text()
 assert '以前の分野共通ガイドが保存されています' in page.locator('.hint-update').inner_text()
 page.get_by_role('button',name='最新のヒントで続ける',exact=True).click()
 s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);old=next(a for a in s['attempts'] if a['id']==old_id)
 assert a['id']!=old_id and a['questionId']=='r07h-q18' and a['selected']==1 and a['confidence']
 assert a['hintCount']==0 and a['hintEvents']==[] and a['materialSnapshot']['hintStatus']=='individual'
 assert old['status']=='postponed' and old['hintCount']==1 and old['materialSnapshot']['hints'][0]['text']=='以前の分野共通ガイド'
 assert page.locator('.hint-head h3').inner_text()=='ヒント' and page.locator('.hint-update').count()==0 and page.get_by_role('radio').nth(1).is_checked()
 page.get_by_role('button',name='ヒントを1つ見る',exact=True).click();state();page.reload();page.locator('.hint-box').wait_for();assert '入力が1増えると10ミリV' in page.locator('.hint-box').inner_text()
 page.get_by_role('button',name='次のヒントを見る',exact=True).click();assert '16の位' in page.locator('#hints').inner_text()
 page.get_by_role('button',name='次のヒントを見る',exact=True).click();assert '130×10' in page.locator('#hints').inner_text() and 'V単位なら' not in page.locator('#hints').inner_text()
 answer();assert '1,300ミリV' in page.locator('.result').inner_text() and page.locator('.reason-list li').count()==4
 # Completed attempts with an older individual hint can restart too; no answer is carried.
 completed=state();a=next(a for a in completed['attempts'] if a['id']==completed['currentId']);a['materialSnapshot']['hints'][0]['text']='更新前の個別ヒント'
 write_state(page,completed);page.reload();page.locator('.hint-head h3').wait_for()
 page.get_by_role('button',name='最新のヒントで解き直す',exact=True).click();s=state();a=next(a for a in s['attempts'] if a['id']==s['currentId']);assert a['selected'] is None and a['hintCount']==0 and not a['answerViewedBefore']
 print('PASS reported DAC question / decimal place-value reasoning / old guide to latest hints / selection preserved / old history unchanged / completed retry starts closed',flush=True)
 exam_name=f"{pending_fixture['year']}年 {'春期' if pending_fixture['season']=='spring' else '秋期'}"
 open_q(pending_id);assert page.locator('.source-question img').count()==1;assert exam_name in page.locator('.question-meta').inner_text()
 answer(0);assert '不正解' in page.locator('#result-heading').inner_text();assert '正解：'+pending_fixture['choices'][pending_fixture['answer']]['label'] in page.locator('.result').inner_text();assert '個別の解答解説は未追加' in page.locator('.result').inner_text();assert '分野の復習メモ' in page.locator('.result').inner_text();assert page.locator('.reason-list').count()==0
 nav('review');assert page.locator(f'[data-action=start][data-id={pending_id}]').count()==1
 nav('materials');page.locator('[data-action=reset-filters]').click();page.locator('[name=year]').select_option(str(pending_fixture['year']));page.locator('[name=season]').select_option(pending_fixture['season']);page.locator('[name=query]').fill(pending_fixture['title']);page.locator(f'[data-action=edit][data-id={pending_id}]').click()
 page.locator('[name=hint0]').fill('自分用メモ <script>alert(1)</script>');page.locator('[name=explanation]').fill('教科書 p.60 を確認');page.get_by_role('button',name='編集を保存する').click()
 # An old attempt keeps its original hints and pending explanation after editing.
 nav('history');old=next(a for a in state()['attempts'] if a['questionId']==pending_id);page.locator(f'[data-action=resume][data-id="{old["id"]}"]').click();assert '個別の解答解説は未追加' in page.locator('.result').inner_text()
 open_q(pending_id);page.get_by_role('button',name='ヒントを1つ見る').click();assert '<script>alert(1)</script>' in page.locator('.hint-box').inner_text();assert page.locator('.hint-box script').count()==0
 nav('materials');page.locator('[data-action=reset-filters]').click();page.locator('[name=enriched]').check();assert page.locator('#catalog-results .row').count()==20;assert page.locator('.catalog-count').inner_text().startswith(f'{reviewed_count+1}問');page.locator('[name=query]').fill(pending_fixture['title']);assert '自分で編集した教材' in page.locator('#catalog-results').inner_text();open_q(pending_id)
 print('PASS scanned source / official key / pending-explanation honesty / retry / personal notes / immutable snapshot',flush=True)
 page.set_viewport_size({'width':390,'height':844});page.locator('.source-question img').evaluate('(img)=>img.decode()');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.get_by_role('button',name='問題を拡大').click();assert page.locator('#image-dialog').is_visible();initial=page.locator('#image-scroll img').evaluate('(img)=>img.clientWidth');page.get_by_role('button',name='画像を拡大',exact=True).click();assert page.locator('#image-scroll img').evaluate('(img)=>img.clientWidth')>initial
 assert page.locator('#image-scroll').evaluate('(e)=>e.scrollWidth>e.clientWidth');page.screenshot(path=str(ROOT/'question-zoom-mobile.png'));page.keyboard.press('Escape');assert not page.locator('#image-dialog').is_visible()
 page.screenshot(path=str(ROOT/'question-mobile.png'),full_page=True)
 page.get_by_role('button',name='表示・データ',exact=True).click()
 with page.expect_download() as download:page.get_by_role('button',name='学習記録を書き出す',exact=True).click()
 backup=ROOT/'record.json';download.value.save_as(str(backup));page.on('dialog',lambda d:d.accept());page.locator('#import-state').set_input_files(str(backup));page.wait_for_function('document.querySelector("#settings-status").textContent.includes("読み込みました")')
 original=state();bad=json.loads(backup.read_text());bad['attempts'][0]['materialSnapshot']['stem']='<img src=x onerror=alert(1)>';bad_path=ROOT/'bad.json';bad_path.write_text(json.dumps(bad));page.locator('#settings-status').evaluate('(e)=>e.textContent=""');page.locator('#import-state').set_input_files(str(bad_path));page.wait_for_function('document.querySelector("#settings-status").textContent.includes("現在の記録は変更していません")');assert '現在の記録は変更していません' in page.locator('#settings-status').inner_text();assert state()==original
 bad=json.loads(backup.read_text());bad['attempts'][0]['materialSnapshot']['hintStatus']='invalid';bad_path.write_text(json.dumps(bad));page.locator('#settings-status').evaluate('(e)=>e.textContent=""');page.locator('#import-state').set_input_files(str(bad_path));page.wait_for_function('document.querySelector("#settings-status").textContent.includes("現在の記録は変更していません")');assert '現在の記録は変更していません' in page.locator('#settings-status').inner_text();assert state()==original
 page.get_by_role('button',name='設定を閉じる',exact=True).click();nav('home');page.screenshot(path=str(ROOT/'home-mobile.png'),full_page=True);nav('topics');page.evaluate('document.documentElement.style.fontSize="32px"');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS mobile image zoom / 200% text / valid backup import / hostile snapshot rejection / no runtime errors',flush=True)
 b.close()
print('Artifacts:',ROOT)
