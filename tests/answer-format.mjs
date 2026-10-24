import test from 'node:test';
import assert from 'node:assert/strict';
import {answerTextHTML} from '../src/utils.js';

test('重要な判断基準だけを安全なstrongとして描画する',()=>{
 const value='この問題は**相続登記の申請期限**を問う。原則**3年以内**。';
 const html=answerTextHTML(value);
 assert.equal(html,'この問題は<strong class="answer-emphasis">相続登記の申請期限</strong>を問う。原則<strong class="answer-emphasis">3年以内</strong>。');
});
test('入力HTMLと属性は強調の内外を問わずエスケープする',()=>{
 const value='**<img src=x onerror=alert(1)>** と <script>alert(1)</script> &';
 const html=answerTextHTML(value);
 assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
 assert.match(html,/&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
 assert.match(html,/&amp;$/);
 assert.doesNotMatch(html,/<img|<script/);
});
test('任意Markdown・不完全な太字マーカーは文字列として残す',()=>{
 assert.equal(answerTextHTML('閉じていない **重要'), '閉じていない **重要');
 assert.equal(answerTextHTML('[link](javascript:alert(1))'), '[link](javascript:alert(1))');
 assert.equal(answerTextHTML('***italic?***'), '***italic?***');
});
test('既存の普通の解説、改行、数値表記は変化させない',()=>{
 const text='前提と条件\n計算式＝3×100＝300円。';
 assert.equal(answerTextHTML(text),text);
 assert.equal(answerTextHTML(null),'');
});
