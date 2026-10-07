"""Reject unreviewed/stale/ordinary-pool contamination; keep separate hashed bank."""
import copy,json,tempfile
from pathlib import Path
from diagnostic_fixtures import builder,prepare,write,review

with tempfile.TemporaryDirectory(prefix='hitomon-diagnostic-content-') as directory:
 root=Path(directory);config,variants=prepare(root);path=root/'content/fixture'
 manifest=json.loads((root/'data/qualifications/fixture/manifest.json').read_text())
 assert manifest['count']==40 and manifest['diagnostic']['count']==12
 index=(root/'data/qualifications/fixture'/manifest['index']['url']).read_bytes()
 assert not any(q.get('diagnosticOnly') for q in json.loads(index))
 assert len(json.loads((root/'data/qualifications/fixture'/manifest['diagnostic']['url']).read_text()))==12
 # Each invalid authored object is rehashed to ensure semantic validation, not
 # simply a stale hash, rejects the change.
 for change in [lambda q:q.update(parentQuestionId='missing'),lambda q:q.update(topicId='two'),lambda q:q.update(examPartId='missing'),lambda q:q.update(diagnosticOnly=False),lambda q:q.update(enrichment='topic-guide'),lambda q:q.update(choiceReasons=['','']),lambda q:q.update(adaptation='')]:
  bad=copy.deepcopy(variants);change(bad[0]);write(path/'diagnostic-questions.json',bad);write(path/'diagnostic-reviews.json',[review(q) for q in bad])
  try:builder.build(root)
  except ValueError:pass
  else:raise AssertionError('Invalid diagnostic content accepted')
 write(path/'diagnostic-questions.json',variants)
 for change in [lambda r:r.update(sha256='0'*64),lambda r:r.update(reviewer=r['author']),lambda r:r['checks'].update(calculation=False),lambda r:r.update(notes=''),lambda r:r.update(checkedAt='2026-10-07')]:
  reviews=[review(q) for q in variants];change(reviews[0]);write(path/'diagnostic-reviews.json',reviews)
  try:builder.build(root)
  except ValueError:pass
  else:raise AssertionError('Invalid diagnostic review accepted')
 write(path/'diagnostic-reviews.json',[review(q) for q in variants]);builder.build(root)
 assert (root/'data/qualifications/fixture'/manifest['index']['url']).read_bytes()==index
 originals=json.loads((path/'questions.json').read_text());originals.append(variants[0]);write(path/'questions.json',originals)
 try:builder.build(root)
 except ValueError:pass
 else:raise AssertionError('Diagnostic material mixed into ordinary source')
print('PASS separate 40 ordinary / 12 diagnostic fixtures / original index preserved / invalid parent, scope, review, hash and pool contamination rejected')
