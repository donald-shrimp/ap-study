import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {sameAnswerSet} from '../src/domain/answer-grading.js';
import {validCaseField, caseReferenceAnswers} from '../src/domain/case-field.js';
import {
  buildWrittenAIPrompt, createCaseRun, rateCaseField, setCaseResponse,
  submitCaseField, validateCaseRun, viewCaseAnswer
} from '../src/domain/case-study.js';

const fixture = JSON.parse(readFileSync(new URL('./fixtures/case-grading.json', import.meta.url)));
const fields = fixture.fields.map(field => ({
  label: field.id, explanation: '形式検査用の解説', rubric: ['解答を確認'],
  ...field, ...(field.correctChoiceIds ? {choices: fixture.choices} : {})
}));
const qualification = {id: 'fixture', examParts: [{id: 'written', unit: 'cases'}]};
const material = {
  id: 'fixture-case', qualificationId: 'fixture', examPartId: 'written', version: 1,
  status: 'reviewed', title: '合成大問', source: '合成テスト', body: '共通本文。',
  sourceImages: [], bodyFigures: [],
  items: [{id: 'part', label: '設問', prompt: '回答してください。', fields}]
};

test('shared field examples are accepted while invalid keys, slots and references are rejected', () => {
  assert(fields.every(validCaseField));
  for (const {field, patch} of fixture.invalid) {
    assert(!validCaseField({...fields.find(candidate => candidate.id === field), ...patch}), JSON.stringify(patch));
  }
  assert(sameAnswerSet(['oak', 'cedar'], ['cedar', 'oak']));
  assert(!sameAnswerSet(['cedar', 'cedar'], ['cedar', 'oak']));
  assert(!sameAnswerSet(['cedar', 'oak'], ['cedar', 'cedar']));
});

test('direct case fields grade by stable IDs and validate a round-tripped answer snapshot', () => {
  const run = createCaseRun(material);
  const answers = {one: 'pine', all: ['oak', 'pine'], fixed: ['oak', 'cedar'], words: ['スギ', ' ナラ '], names: ['甲', '別表記']};
  for (const [id, value] of Object.entries(answers)) {
    const key = 'part--' + id;
    setCaseResponse(run, key, Array.isArray(value) ? JSON.stringify(value) : value);
    submitCaseField(run, key);
  }
  assert.deepEqual(Object.fromEntries(Object.entries(run.evaluations).map(([key, result]) => [key, result.outcome])), {
    'part--one': 'correct', 'part--all': 'incorrect', 'part--fixed': 'correct', 'part--words': 'correct'
  });
  viewCaseAnswer(run, 'part--names');
  rateCaseField(run, 'part--names', 'partial');
  const saved = JSON.parse(JSON.stringify(run));
  assert.equal(validateCaseRun(saved, qualification).progress.status, 'completed');
  const prompt = buildWrittenAIPrompt({question: run.material, attempt: {fieldKey: 'part--fixed', response: run.responses['part--fixed']}, baseURL: 'https://example.com/'});
  assert.match(prompt, /【公式解答例】\nスギ（ハ）\nナラ（イ）/);
  assert.match(prompt, /【私の回答】\nイ ナラ\nハ スギ/);

  const renamed = structuredClone(material);
  renamed.version++;
  renamed.items[0].fields[0].choices.find(choice => choice.id === 'pine').label = 'B';
  assert.deepEqual(caseReferenceAnswers(renamed.items[0].fields[0]), ['B']);
  assert.deepEqual(caseReferenceAnswers(saved.material.items[0].fields[0]), ['ロ']);
  assert.equal(validateCaseRun(saved, qualification).evaluations['part--one'].outcome, 'correct');
  saved.evaluations['part--one'].outcome = 'incorrect';
  assert.throws(() => validateCaseRun(saved, qualification));
});
