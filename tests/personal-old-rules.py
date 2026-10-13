"""An un-deployed personal channel must not stop existing channels or learning."""
from pathlib import Path
exec(compile((Path(__file__).parent/'learning-old-rules.py').read_text().split("current=(ROOT/")[0],str(Path(__file__).parent/'learning-old-rules.py'),'exec'))
current=(ROOT/'firestore.rules').read_text();start=current.index('  function validPersonal(');end=current.index('  function cardId(',start);old=current[:start]+current[end:]
try:
 rules(old)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);pg=b.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for();login(pg,f'personal-old-{time.time_ns()}@example.test')
  close_settings(pg);pg.locator('.sidebar [data-view=history]').click();pg.locator('[data-reading-topic="ネットワーク"]').fill('旧ルールでも保存')
  pg.locator('.sidebar [data-view=home]').click();pg.locator('[data-action=cards-open]').click();pg.locator('[data-action=card-flip]').click();pg.locator('[data-action=card-rate][data-outcome=again]').click();pg.locator('[data-action=card-flip]').wait_for();settings(pg);pg.locator('#sync-now').click()
  pg.wait_for_function('document.getElementById("sync-state").dataset.personal==="rules"',timeout=30000)
  pg.wait_for_function('document.getElementById("sync-state").dataset.cards==="synced" && document.getElementById("sync-state").dataset.planning==="synced" && document.getElementById("sync-state").dataset.learning==="synced"')
  close_settings(pg);pg.locator('.sidebar [data-view=home]').click();pg.locator('.study-entrance[data-paper-mode=paperless]').click();pg.get_by_role('radio').first.check();pg.locator('[data-action=submit]').click();synced(pg);assert state(pg)['state']['attempts'][-1]['completedAt']
  rules(current);settings(pg);pg.locator('#sync-now').click();pg.wait_for_function('document.getElementById("sync-state").dataset.personal==="synced"',timeout=30000);close_settings(pg);pg.locator('.sidebar [data-view=history]').click();assert pg.locator('[data-reading-topic="ネットワーク"]').input_value()=='旧ルールでも保存';assert not errors,errors;b.close()
 print('PASS previous Rules: notes/checkpoints remain local / ratings, answers, planning and learning sync unaffected / new Rules replay personal outbox')
finally:rules(current)
