// Exercise the real reviewed bank repeatedly with a reproducible sampling seed.
// This is admission/balance coverage, not a content review or difficulty claim.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {selectDiagnostic, diagnosticFamily} from '../src/domain/diagnostic.js';

const read=async path=>JSON.parse(await readFile(new URL('../'+path,import.meta.url),'utf8'));
const config=await read('content/ap/qualification.json');
const manifest=await read('data/qualifications/ap/manifest.json');
const originals=await read('data/qualifications/ap/'+manifest.index.url);
const variants=await read('data/qualifications/ap/'+manifest.diagnostic.url);
const observed=new Set();
let seed=0x20261008;
const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
for(let run=0;run<1000;run++){
  const selected=selectDiagnostic(originals,config,[],random,variants);
  assert.equal(selected.length,30);
  assert.equal(new Set(selected.map(diagnosticFamily)).size,30);
  const derived=selected.filter(q=>q.diagnosticOnly);
  assert.equal(derived.length,17);
  assert.equal(new Set(derived.map(q=>q.topicId)).size,17);
  for(const q of derived)observed.add(q.id);
}
assert.deepEqual([...observed].sort(),variants.map(q=>q.id).sort(),'Every reviewed derivative can enter the unchanged 30-question diagnostic.');
console.log(`PASS 1000 real-bank selections / all ${variants.length} derivatives admitted / per-field cap1 / distinct source parents / 17+13 composition`);
