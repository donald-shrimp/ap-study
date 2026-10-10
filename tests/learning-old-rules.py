"""A missing learning collection rule must leave existing study/sync functional."""
from pathlib import Path
import json,shutil,time,subprocess,tempfile,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
exec(compile((ROOT/'tests/sync.py').read_text().split('with sync_playwright() as p:')[0],str(ROOT/'tests/sync.py'),'exec'))
def rules(value):
 with tempfile.NamedTemporaryFile(mode='w',suffix='.rules') as f:
  f.write(value);f.flush()
  code="import {readFileSync} from 'node:fs';import {initializeTestEnvironment} from '@firebase/rules-unit-testing';const env=await initializeTestEnvironment({projectId:'hito-mon',firestore:{host:'127.0.0.1',port:8080,rules:readFileSync(process.env.RULES_FILE,'utf8')}});await env.cleanup();"
  subprocess.run(['node','--input-type=module','-e',code],cwd=ROOT,env={**os.environ,'RULES_FILE':f.name},check=True,capture_output=True)
current=(ROOT/'firestore.rules').read_text();start=current.index('  function validLearning(');end=current.index('  match /users/{uid}/qualifications/{qualificationId}/attempts/',start);old=current[:start]+current[end:]
try:
 rules(old)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);pg=b.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for();email=f'old-rules-{time.time_ns()}@example.test';login(pg,email)
  pg.locator('.study-entrance[data-paper-mode=paperless]').click();pg.get_by_role('radio').first.check();pg.locator('[data-action=hint]').click();pg.locator('[data-action=desk-later]').click();synced(pg);settings(pg);pg.wait_for_function('document.getElementById("learning-sync-state").textContent.includes("ルールの更新が必要") && document.getElementById("workspace-sync-state").textContent==="計画・診断も同期済み。"');assert pg.locator('#sync-state').inner_text()=='同期済み';close_settings(pg)
  assert state(pg)['state']['settings']['deskQuestionIds'];pg.locator('.study-entrance[data-paper-mode=desk]').click();pg.get_by_role('button',name='回答する',exact=True).wait_for();a=next(a for a in state(pg)['state']['attempts'] if a['id']==state(pg)['state']['currentId']);pg.get_by_role('radio').nth(a['questionSnapshot']['answer']).check();pg.locator('[data-action=submit]').click();synced(pg);assert state(pg)['state']['attempts'][-1]['status']=='assisted';assert not errors,errors
  rules(current);settings(pg);pg.locator('#sync-now').click();pg.wait_for_function('document.getElementById("learning-sync-state").textContent==="学習設定も同期済み。"');b.close()
 print('PASS missing new Rules: local designation/resume/answer and existing attempt/plan sync continue; new-channel notice; Rules update retries successfully')
finally:rules(current)
