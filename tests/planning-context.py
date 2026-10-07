from browser_storage import nav as action_nav, open_plan_editor, open_plan_ai
"""User assumptions survive AI import, preview, offline editing and backup."""
import json,shutil,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
READ='''async()=>{
 const {createLocalStore}=await import('/src/storage/local.js');const study=createLocalStore({qualificationId:'ap',rootPath:'/'});
 try{const identity=await study.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return {study:JSON.parse(await study.snapshot()),documents:await workspace.read()};}finally{await workspace.close();}}finally{await study.close();}
}'''
def plan(page):return next(r['payload'] for r in page.evaluate(READ)['documents'] if r['kind']=='planning')
def edit(page):
 page.locator('#context-form').evaluate('(form)=>{for(let d=form.parentElement;d;d=d.parentElement)if(d.tagName==="DETAILS")d.open=true;}')
 return page.locator('#context-form')

with tempfile.TemporaryDirectory(prefix='hitomon-context-') as directory,sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write']);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto('http://127.0.0.1:4173/')
 page.get_by_role('button',name='とりあえずはじめる',exact=True).click();page.get_by_role('button',name='回答する',exact=True).wait_for();page.get_by_role('button',name='中断',exact=True).click();page.get_by_role('button',name='受験日・計画を登録',exact=True).click()
 open_plan_editor(page);open_plan_ai(page)
 form=edit(page);form.locator('[name=studiedScope]').fill('教科書を一周');form.locator('[name=materials]').fill('手元の教科書');form.locator('[name=weeklyMinutes]').fill('180');form.locator('[name=constraints]').fill('土日は休む');form.locator('[name=rationale]').fill('<script id="injected-context">throw new Error("bad")</script>\nまず広く確認する');form.get_by_role('button',name='前提を保存',exact=True).click();page.get_by_text('計画の前提を保存しました。',exact=True).wait_for();before=plan(page);assert before['context']['weeklyMinutes']==180 and not page.locator('#injected-context').count()
 open_plan_ai(page);example=json.loads((ROOT/'schemas/study-plan.example.json').read_text());example.pop('context');page.locator('#plan-json').fill(json.dumps(example));page.get_by_role('button',name='検証してプレビュー',exact=True).click();page.get_by_text('JSONに前提がないため',exact=False).wait_for();assert '教科書を一周' in page.locator('#plan-preview').inner_text();page.get_by_role('button',name='この内容で登録',exact=True).click();page.get_by_text('受験日と計画を登録しました。',exact=True).wait_for();assert plan(page)['context']==before['context']
 open_plan_ai(page);invalid=plan(page);invalid['context']['weeklyMinutes']=-1;saved=plan(page);page.locator('#plan-json').fill(json.dumps(invalid));page.get_by_role('button',name='検証してプレビュー',exact=True).click();page.get_by_text('0〜10080分の整数',exact=False).wait_for();assert plan(page)==saved and not page.locator('[data-action=register-plan]').count()
 page.get_by_text('AIへ渡す内容を確認',exact=True).click();assert '教科書を一周' in page.locator('.summary-preview').inner_text();page.get_by_role('button',name='AI用プロンプトをコピー',exact=True).click();page.get_by_text('コピーしました。',exact=True).wait_for();assert 'まず広く確認する' in page.evaluate('navigator.clipboard.readText()')
 page.get_by_role('button',name='学習状況JSONをコピー',exact=True).click();page.get_by_text('コピーしました。',exact=True).wait_for();summary=json.loads(page.evaluate('navigator.clipboard.readText()'));assert summary['context']==saved['context'];assert summary['examDates'][0]['daysUntil'] is not None;assert 'questionSnapshot' not in json.dumps(summary) and 'uid' not in summary
 page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener("controllerchange",r,{once:true}));}')
 context.set_offline(True);page.reload();page.get_by_role('heading',name='受験日・学習計画',exact=True).wait_for();form=edit(page);form.locator('[name=rationale]').fill('診断を見てから調整');form.get_by_role('button',name='前提を保存',exact=True).click();page.get_by_text('計画の前提を保存しました。',exact=True).wait_for();saved=plan(page);assert saved['context']['rationale']=='診断を見てから調整'
 page.evaluate('document.querySelectorAll("#main details").forEach(d=>d.open=true);document.documentElement.style.fontSize="32px"');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(Path(directory)/'context-mobile-200.png'),full_page=True)
 page.locator('#settings-button').click()
 with page.expect_download() as event:page.get_by_role('button',name='学習記録を書き出す',exact=True).click()
 backup=Path(directory)/'backup.json';event.value.save_as(str(backup));assert json.loads(backup.read_text())['workspaceBackup']['plan']['context']==saved['context']
 second=browser.new_context();other=second.new_page();other.on('dialog',lambda d:d.accept());other.goto('http://127.0.0.1:4173/');other.get_by_role('button',name='とりあえずはじめる',exact=True).wait_for();other.locator('#settings-button').click();other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=True).wait_for();assert plan(other)['context']==saved['context'];second.close()
 open_plan_ai(page);context.set_offline(False);page.get_by_role('button',name='設定を閉じる').click();cleared=plan(page);cleared['context']={};page.locator('#plan-json').fill(json.dumps(cleared));page.get_by_role('button',name='検証してプレビュー',exact=True).click();assert '計画の前提は未登録です' in page.locator('#plan-preview').inner_text();page.get_by_role('button',name='この内容で登録',exact=True).click();page.get_by_text('受験日と計画を登録しました。',exact=True).wait_for();assert plan(page)['context']=={}
 assert not errors,errors;browser.close()
print('PASS optional context / no setup gate / text escaping / AI import retains omitted context / explicit clear preview / invalid unchanged / external preview and summary / offline edit / backup restore / mobile 200%')
