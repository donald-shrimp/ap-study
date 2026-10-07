"""Published card edition must match the actual independent review and retained corpus."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
review=read('content/ap/flashcard-reviews/20261007-expansion.json')
deck=read('content/ap/flashcards.json');cards={c['id']:c for c in deck['cards']}
assert review['publishedDeckSha256']==hashlib.sha256((ROOT/'content/ap/flashcards.json').read_bytes()).hexdigest()
assert review['publishedCount']==len(cards)==len(deck['cards'])
assert len(review['publishedCards'])==len(cards)
assert {r['cardId'] for r in review['publishedCards']}==set(cards)
for record in review['publishedCards']:
 assert record['cardSha256']==sha(cards[record['cardId']]),record['cardId']
 if record['isNew']:
  assert record['author']!=record['reviewer']
  assert record['reviewStatus'] in ['approved','corrected']
  assert record['evidence']
for path,expected in review['preservedContentSha256'].items():
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
old={c['id']:c for c in review['originalCards']}
assert set(old)<=set(cards) and len(old)==20
changed=[]
for id,previous in old.items():
 if cards[id]!=previous:
  changed.append(id);assert cards[id]['version']==previous['version']+1
 else:assert cards[id]['version']==previous['version']
assert set(changed)==set(review['updatedExistingCardIds'])
assert set(c['topicId'] for c in cards.values())==set(t['id'] for t in read('content/ap/qualification.json')['topics'])
for worker in review['independentReviews']:
 assert worker['sourceAuthor']!=worker['reviewer']
 assert worker['authorCardsSha256']==sha(worker['authorCards'])
 assert worker['reviewedCardsSha256']==sha(worker['reviewedCards'])
 if worker['sourceAuthor']!='root':
  assert len(worker['cards'])==len(worker['authorCards'])==len(worker['reviewedCards'])
 else:assert len(worker['cards'])==len(review['updatedExistingCardIds'])
 reviewed={c['id']:c for c in worker['reviewedCards']}
 for published in review['publishedCards']:
  if published['author']!=worker['sourceAuthor']:continue
  expected=dict(reviewed[published['sourceCardId']])
  for change in published['rootChanges']:
   assert expected[change['field']]==change['from'];expected[change['field']]=change['to']
  assert expected==cards[published['cardId']]

 assert len(worker['cards'])==worker['reviewedCount'] and worker['complete']
 for r in worker['cards']:
  for image in r.get('originalImagesViewed',[]):
   assert hashlib.sha256((ROOT/image.get('imagePath',image.get('path'))).read_bytes()).hexdigest()==image.get('imageSha256',image.get('sha256'))
print(f"PASS {len(cards)} published cards match individual review / 17 topics / original 20 IDs / versioned revisions / unchanged 800-question corpus")
