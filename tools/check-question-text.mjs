import fs from 'node:fs';
import {questionTextHTML} from '../src/ui/question-text.js';

let count=0;
for(const name of fs.readdirSync('data/transcriptions').filter(n=>n.endsWith('.json'))) {
  for(const record of JSON.parse(fs.readFileSync(`data/transcriptions/${name}`,'utf8'))) {
    for(const text of [record.stem,...record.choices.map(c=>c.text)]) {
      if(questionTextHTML(text).includes('class="math-error"'))throw new Error(`Invalid formula: ${record.id}: ${text}`);
      if((text.match(/\$/g)||[]).length%2)throw new Error(`Unpaired math delimiter: ${record.id}`);
      if((text.match(/^```/gm)||[]).length%2)throw new Error(`Unpaired code fence: ${record.id}`);
    }
    count++;
  }
}
console.log(`PASS ${count} transcription formulas render with KaTeX`);
