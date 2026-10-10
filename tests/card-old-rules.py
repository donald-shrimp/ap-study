"""Cards channel is optional until its new Firebase Rules are deployed."""
from pathlib import Path
exec(compile((Path(__file__).parent/'learning-old-rules.py').read_text().split("current=(ROOT/")[0],str(Path(__file__).parent/'learning-old-rules.py'),'exec'))
current=(ROOT/'firestore.rules').read_text();start=current.index('  function cardId(');end=current.index('  match /users/{uid}/qualifications/{qualificationId}/attempts/',start);old=current[:start]+current[end:]
try:
 rules(old)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);pg=b.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for();login(pg,f'cards-old-{time.time_ns()}@example.test')
  pg.locator('[data-action=cards-open]').click();pg.locator('[data-action=card-flip]').click();pg.locator('[data-action=card-rate][data-outcome=again]').click();pg.locator('[data-action=card-flip]').wait_for();settings(pg);pg.wait_for_function('document.getElementById("card-sync-state").textContent.includes("最新のFirebaseルール")');assert pg.locator('#sync-state').inner_text()=='同期済み';pg.wait_for_function('document.getElementById("learning-sync-state").textContent==="学習設定も同期済み。" && document.getElementById("workspace-sync-state").textContent==="計画・診断も同期済み。"');close_settings(pg)
  pg.locator('.sidebar [data-view=home]').click();pg.locator('.study-entrance[data-paper-mode=paperless]').click();pg.get_by_role('radio').first.check();pg.locator('[data-action=submit]').click();synced(pg);assert state(pg)['state']['attempts'][-1]['completedAt']
  rules(current);settings(pg);pg.locator('#sync-now').click();pg.wait_for_function('document.getElementById("card-sync-state").textContent.includes("自己評価も同期済み")',timeout=30000);assert not errors,errors;b.close()
 print('PASS old Rules: local card rating / existing answer, planning and learner sync unaffected / updated Rules replay pending ratings')
finally:rules(current)
