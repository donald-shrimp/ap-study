"""Failed case saves retain typed answers in a portable v2 backup and recover."""
import json,shutil,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import open_data_management,wait_for_async,select_target
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:4173/ap/');select_target(page,'written');page.locator('[data-action=written-start]').first.click();page.locator('textarea[data-written-key]').wait_for()
 page.evaluate("()=>{window.caseOriginalPut=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='documents')throw new DOMException('合成テストの保存失敗','QuotaExceededError');return window.caseOriginalPut.apply(this,args);};}")
 page.locator('textarea[data-written-key]').fill('保存失敗の入力');page.get_by_role('button',name='保存を再試行',exact=True).wait_for();assert page.locator('textarea[data-written-key]').input_value()=='保存失敗の入力';open_data_management(page)
 with page.expect_download() as event:page.locator('#export-state').click()
 path=Path(tempfile.mkdtemp())/'failed-case.json';event.value.save_as(path);data=json.loads(path.read_text());assert data['writtenBackup']['runs'][0]['responses']['q1--answer']['value']=='保存失敗の入力';assert data['writtenBackup']['runs'][0]['progress']['status']=='in_progress'
 page.get_by_role('button',name='設定を閉じる',exact=True).click();page.evaluate('()=>{IDBObjectStore.prototype.put=window.caseOriginalPut;}');page.get_by_role('button',name='保存を再試行',exact=True).click();page.locator('.written-save-actions').wait_for(state='hidden');page.reload();page.locator('textarea[data-written-key]').wait_for();assert page.locator('textarea[data-written-key]').input_value()=='保存失敗の入力';assert not errors,errors;b.close()
print('PASS failed B write retains DOM and pending snapshot / v2 backup includes unsaved work / explicit retry and reload / no false case completion')
