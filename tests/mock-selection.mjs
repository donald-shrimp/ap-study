import {canUseQuestion} from '../src/domain/content-policy.js';
// Exercise the real reviewed bank repeatedly with a reproducible sampling seed.
// This is admission/balance coverage, not a content review or difficulty claim.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {selectDiagnostic, diagnosticFamily, createDiagnostic, validateDiagnostic} from '../src/domain/diagnostic.js';

const read=async path=>JSON.parse(await readFile(new URL('../'+path,import.meta.url),'utf8'));
const config=await read('content/ap/qualification.json');
const manifest=await read('data/qualifications/ap/manifest.json');
const originals=await read('data/qualifications/ap/'+manifest.index.url);
const variants=await read('data/qualifications/ap/'+manifest.assessment.url);
const observed=new Set(),compositions=new Set();
let seed=0x20261008;
const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
for(let run=0;run<1000;run++){
  const selected=selectDiagnostic(originals,config,[],random,variants);
  assert.equal(selected.length,30);
  assert.equal(new Set(selected.map(diagnosticFamily)).size,30);
  const derived=selected.filter(q=>!canUseQuestion(q,'practice'));
  assert.ok(derived.length>=20&&derived.length<=24);compositions.add(derived.length);
  assert.ok(selected.some(q=>!!canUseQuestion(q,'practice')));
  for(const topic of config.topics)assert.ok(derived.filter(q=>q.topicId===topic.id).length<=(config.diagnosticBlueprint.variantLimits[topic.id]??1));
  assert.equal(new Set(derived.map(q=>q.topicId)).size,17);
  for(const q of derived)observed.add(q.id);
}
assert.deepEqual([...observed].sort(),variants.map(q=>q.id).sort(),'Every reviewed derivative can enter the unchanged 30-question diagnostic.');
console.log(`PASS 1000 real-bank selections / all ${variants.length} derivatives admitted / selective cap2 / distinct source parents / mixed composition ${[...compositions].sort().join(",")}`);

// A run started under v2 keeps its own cap1 policy after the new manifest arrives.
const previous={...config,diagnosticBlueprint:{...config.diagnosticBlueprint,version:2,variantLimits:{}}};
const fullOriginals=(await Promise.all(manifest.packs.map(pack=>read('data/qualifications/ap/'+pack.url)))).flat();
const oldRun=createDiagnostic(selectDiagnostic(fullOriginals,previous,[],random,variants),previous);
// Reproduce the previously saved v2 contract, not a new v4 session.
oldRun.blueprintVersion=2;delete oldRun.selectionPolicy.weights;
oldRun.selectionPolicy.preference=['unseen-derived','unseen-original','seen-derived','seen-original'];
const frozen=structuredClone(oldRun);
assert.equal(oldRun.slots.filter(s=>s.kind==='derived').length,17);
assert.deepEqual(validateDiagnostic(oldRun,config,()=>{}),frozen);
assert.equal(oldRun.blueprintVersion,2);
console.log('PASS saved v2 diagnostic unchanged after selective cap2/v3 manifest');
