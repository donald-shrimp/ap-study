// One entry point for the accumulating local editorial library.
import {readFile} from 'node:fs/promises';
import {buildPreview} from './pilot-2025-spring/build-preview.mjs';

const {batches}=JSON.parse(await readFile(new URL('catalog.json',import.meta.url),'utf8'));
const cases=batches.flatMap(batch=>batch.cases.map(c=>({
 ...c,
 label:batch.examLabel+' '+c.label,
 examLabel:batch.examLabel,
 directoryURL:new URL((c.draftDirectory||batch.directory)+'/',import.meta.url)
})));
if(!cases.length||new Set(cases.map(c=>c.id)).size!==cases.length)throw Error('Empty or duplicate draft catalog');
await buildPreview({cases,outputURL:new URL('preview.html',import.meta.url)});
