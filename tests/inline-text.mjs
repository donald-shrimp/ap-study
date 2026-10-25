import test from 'node:test';
import assert from 'node:assert/strict';
import {inlineTextHTML} from '../src/ui/inline-text.js';

test('emphasis preserves text, line breaks and adjacent emphasis',()=>{
  assert.equal(inlineTextHTML('通常 **条件**：**5年以下**。\n次の行'), '通常 <strong>条件</strong>：<strong>5年以下</strong>。\n次の行');
  assert.equal(inlineTextHTML('**甲****乙**'),'<strong>甲</strong><strong>乙</strong>');
  assert.equal(inlineTextHTML('行1\r\n行2'),'行1\r\n行2');
});
test('unmatched and empty markers remain readable without joining lines',()=>{
  for(const text of ['前 **未完','****','**行1\n行2**','**行1\r行2**','a * b'])assert.equal(inlineTextHTML(text),text);
});
test('raw HTML and executable attributes are escaped inside and outside emphasis',()=>{
  for(const text of ['<script>alert(1)</script>','**<img src=x onerror=alert(1)>**','**<strong onclick="x()">語</strong>**','<br> & "引用"']){
    const html=inlineTextHTML(text);
    assert.doesNotMatch(html,/<(?:script|img|br)|<strong\s/i);
    assert.match(html,/&lt;/);
  }
  assert.equal(inlineTextHTML('**&lt;img&gt;**'),'<strong>&amp;lt;img&amp;gt;</strong>');
});
test('explanations do not interpret links, images, math or underline syntax',()=>{
  const text='[リンク](javascript:alert(1)) ![図](x) $x$ ++文字++';
  assert.equal(inlineTextHTML(text),text);
  assert.equal(inlineTextHTML(), '');
});
