import test from 'node:test';
import assert from 'node:assert/strict';
import {buildAIPrompt,DESTINATIONS} from '../src/features/ai-handoff.js';

const question={
 id:'test-question',title:'ハミング符号',packLabel:'2022年 春期',number:4,
 stem:'符号1110011の誤りビットを訂正せよ。',
 choices:[{id:'a',label:'ア',text:'0110011'},{id:'b',label:'イ',text:'1010011'}],
 answer:0,summary:'偶数パリティ',
 explanation:'三つの検査式からX₁を反転する。',
 choiceReasons:['X₁が誤り','X₂ではない'],
 hints:[{title:'手順',text:'不一致の式の共通項を見る'}],
 sourceImages:['assets/questions/r04h/r04h-q4.webp'],
 questionUrl:'https://www.ipa.go.jp/test.pdf'
};
const qualification={name:'応用情報技術者試験'};
const baseURL='https://example.com/ap-study/';
const build=(q=question,a={status:'incorrect',selected:1},detail='なぜX₁？')=>
 buildAIPrompt({question:q,attempt:a,qualification,detail,baseURL});

test('解答後のスナップショットから選択肢・正解・解説・質問を作る',()=>{
 const value=build();
 assert.match(value,/2022年 春期 · 問4 · ハミング符号/);
 assert.match(value,/符号1110011の誤りビット/);
 assert.match(value,/【私の回答】\n\nイ：1010011/);
 assert.match(value,/【正解】\n\nア：0110011/);
 assert.match(value,/【ひと問の解答解説】\n\n三つの検査式/);
 assert.match(value,/選択肢の理由】\n\nア：X₁が誤り/);
 assert.match(value,/ヒント.*\n\n1\. 不一致の式の共通項を見る/);
 assert.match(value,/なぜX₁？/);
 assert.match(value,/https:\/\/example.com\/ap-study\/assets\/questions\/r04h\/r04h-q4.webp/);
 assert.match(value,/https:\/\/www.ipa.go.jp\/test.pdf/);
});

test('解答閲覧と自力正解は区別する',()=>{
 assert.match(build(question,{status:'revealed',selected:null},''),/回答せず、解答を確認/);
 assert.match(build(question,{status:'correct',selected:0},''),/【採点結果】\n\n自力正解/);
 assert.match(build(question,{status:'assisted',selected:0},''),/ヒントを使って正解/);
});

test('未回答や中断中の問題からは質問文を作らない',()=>{
 assert.throws(()=>build(question,{status:'in_progress',selected:1}),/解答後/);
 assert.throws(()=>build(question,{status:'postponed',selected:1}),/解答後/);
 assert.throws(()=>build({...question,choices:[]}),/選択肢と正解/);
});

test('文字起こし未確認の問題は未検証OCRを原文として出力しない',()=>{
 const unreviewed={...question,stem:'',searchText:'誤OCRあいう',sourceImages:['assets/source.webp']};
 const result=build(unreviewed);
 assert.match(result,/原文の文字起こしは確認できていません/);
 assert.doesNotMatch(result,/誤OCRあいう/);
 assert.match(result,/https:\/\/example.com\/ap-study\/assets\/source.webp/);
 assert.match(result,/画像を見られない場合は推測せず/);
});

test('図と画像選択肢、資格別の問題にも対応する',()=>{
 const withFigures={...question,image:'assets/figure.png',choices:[{label:'1',text:'',image:'assets/a.png'},{label:'2',text:'本文'}]};
 const value=buildAIPrompt({question:withFigures,attempt:{status:'revealed',selected:null},qualification:{name:'架空資格'},baseURL,detail:''});
 assert.match(value,/架空資格/);
 assert.match(value,/選択肢画像: https:\/\/example.com\/ap-study\/assets\/a.png/);
 assert.match(value,/原本・図 2：https:\/\/example.com\/ap-study\/assets\/figure.png/);
 assert.match(value,/基本からお願いします/);
});

test('3つの宛先はHTTPSの固定URLのみ',()=>{
 assert.deepEqual(Object.keys(DESTINATIONS),['chatgpt','gemini','claude']);
 for(const d of Object.values(DESTINATIONS))assert.ok(d.url.startsWith('https://'));
});
