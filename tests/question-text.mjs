import test from 'node:test';
import assert from 'node:assert/strict';
import {questionTextHTML} from '../src/ui/question-text.js';

test('fractions, nested negation and subscripts generate accessible math',()=>{
  const out=questionTextHTML('式 $\\frac{a+b}{c}$ と $\\overline{Q\\to\\overline{P}}$\n\n$$X_{1}\\oplus P_{1}=0$$');
  assert.equal((out.match(/class="katex"/g)||[]).length,3);
  assert.match(out,/<mfrac>/);assert.match(out,/<mover\b/);assert.match(out,/<msub>/);assert.doesNotMatch(out,/math-error/);
});
test('tables preserve rows and render formulas in cells',()=>{
  const out=questionTextHTML('| A | B |\n| --- | --- |\n| $\\overline{A}$ | 1 |\n| 0 | 2 |');
  assert.match(out,/<table/);assert.equal((out.match(/<tr>/g)||[]).length,3);assert.match(out,/<mover\b/);
});
test('question content is escaped and LaTeX cannot inject links or HTML',()=>{
  const out=questionTextHTML('<img src=x onerror=alert(1)>\n\n$\\href{javascript:alert(1)}{x}$\n\n$\\htmlClass{evil}{x}$');
  assert.doesNotMatch(out,/<img|<a\b|class="evil"/);assert.match(out,/&lt;img/);
});
test('unknown formula is visible instead of crashing or disappearing',()=>{
  assert.match(questionTextHTML('$\\unknownmacro{x}$'),/math-error/);
});
test('pseudocode remains literal and paragraphs retain deliberate line breaks',()=>{
  const out=questionTextHTML('第一段落\n第二行\n\n```\nif (a < b) {\n  x = 1;\n}\n```');
  assert.match(out,/第一段落\n第二行/);assert.match(out,/<pre/);assert.match(out,/a &lt; b/);
});
