import {normalizeAnswerText, sameAnswerSet} from './answer-grading.js';
import {answerSetTextLimit, answerSetValues, canSubmitAnswerSet, validAnswerSetValue} from './case-answer-set.js';
import {decimalValue, validNumericField} from './decimal-answer.js';

const safeId = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$/.test(value);
const text = (value, limit) => typeof value === 'string' && [...value].length <= limit;
const unique = values => new Set(values).size === values.length;

export function caseCorrectChoiceIds(field) {
  if (field.grading.method === 'exactChoiceSet') return field.correctChoiceIds;
  // Saved materials used the displayed labels as their answer key.
  const labels = field.referenceAnswers.map(normalizeAnswerText);
  return field.choices.filter(choice => labels.includes(normalizeAnswerText(choice.label))).map(choice => choice.id);
}

export function caseReferenceAnswers(field) {
  if (field.grading.method !== 'exactChoiceSet') return field.referenceAnswers;
  return field.correctChoiceIds.map(id => field.choices.find(choice => choice.id === id).label);
}

export function validCaseFieldResponse(field, value) {
  if (typeof value !== 'string') return false;
  if (field.type === 'answerSet') return validAnswerSetValue(field, value);
  if (field.type === 'singleChoice') return field.choices.some(choice => choice.id === value);
  return [...value].length <= field.maxLength;
}

export function canSubmitCaseField(field, value) {
  return field.type === 'answerSet' ? canSubmitAnswerSet(field, value) : Boolean(value?.trim());
}

export function evaluateCaseField(field, response) {
  const {value} = response;
  if (field.choices) {
    const ids = field.type === 'answerSet' ? answerSetValues(value)?.filter(Boolean) : [value];
    if (response.skipped) return 'incorrect';
    if (!ids) return null;
    const expectedIds = caseCorrectChoiceIds(field);
    if (field.grading.method === 'exactChoiceSet') return sameAnswerSet(ids, expectedIds) ? 'correct' : 'incorrect';
    if (field.type === 'singleChoice') return expectedIds.includes(value) ? 'correct' : 'incorrect';
    const selectedLabels = ids.map(id => normalizeAnswerText(field.choices.find(choice => choice.id === id)?.label ?? id));
    return sameAnswerSet(selectedLabels, field.referenceAnswers.map(normalizeAnswerText)) ? 'correct' : 'incorrect';
  }
  switch (field.grading.method) {
    case 'exactText':
      return field.referenceAnswers.some(answer => normalizeAnswerText(answer) === normalizeAnswerText(value)) ? 'correct' : null;
    case 'exactDecimal': {
      const decimal = decimalValue(value);
      if (decimal === null) return null;
      return field.referenceAnswers.some(answer => decimalValue(answer) === decimal) ? 'correct' : 'incorrect';
    }
    case 'unordered': {
      if (response.skipped) return 'incorrect';
      const terms = answerSetValues(value)?.map(normalizeAnswerText).filter(Boolean);
      if (!terms) return null;
      if (terms.length !== field.referenceAnswers.length || !unique(terms)) return 'incorrect';
      return sameAnswerSet(terms, field.referenceAnswers.map(normalizeAnswerText)) ? 'correct' : null;
    }
    default:
      return null;
  }
}

function validChoices(field) {
  const {choices, grading, correctChoiceIds, referenceAnswers} = field;
  if (!Array.isArray(choices) || choices.length < 2 || choices.length > 20
      || !choices.every(choice => choice && safeId(choice.id) && text(choice.label, 50) && text(choice.text, field.type === 'singleChoice' ? 20000 : 2000))) return false;
  const ids = choices.map(choice => choice.id);
  if (!unique(ids)) return false;
  const max = field.type === 'singleChoice' ? 1 : choices.length;
  if (grading.method === 'exactChoiceSet') {
    return referenceAnswers === undefined && Array.isArray(correctChoiceIds)
      && correctChoiceIds.length >= 1 && correctChoiceIds.length <= max
      && unique(correctChoiceIds) && correctChoiceIds.every(id => ids.includes(id));
  }
  const min = field.type === 'singleChoice' ? 1 : 2;
  const legacyMethod = field.type === 'singleChoice' ? 'exactText' : 'unordered';
  const labels = choices.map(choice => choice.label);
  return grading.method === legacyMethod && referenceAnswers.length >= min && referenceAnswers.length <= max
    && referenceAnswers.every(label => labels.includes(label))
    && (field.type === 'singleChoice' || unique(labels) && labels.every(Boolean)
      && unique(referenceAnswers.map(normalizeAnswerText)));
}

function validAnswerSet(field) {
  const config = field.answerSet;
  if (!config || typeof config !== 'object' || Array.isArray(config)
      || Object.keys(config).some(key => !['slots', 'sourceFieldIds', 'maxLength'].includes(key))) return false;
  const {slots, sourceFieldIds, maxLength} = config;
  const answerCount = field.correctChoiceIds?.length ?? field.referenceAnswers.length;
  if (slots !== undefined && (!Array.isArray(slots) || slots.length < 2 || slots.length !== answerCount
      || !unique(slots) || !slots.every(slot => text(slot, 50) && slot.trim()))) return false;
  if (sourceFieldIds !== undefined && (!Array.isArray(sourceFieldIds) || sourceFieldIds[0] !== field.id
      || !unique(sourceFieldIds) || !sourceFieldIds.every(safeId)
      || sourceFieldIds.length > 1 && sourceFieldIds.length !== slots?.length)) return false;
  if (field.choices) return maxLength === undefined;
  const terms = field.referenceAnswers.map(normalizeAnswerText);
  return field.grading.method === 'unordered' && unique(terms) && terms.every(Boolean)
    && (maxLength === undefined || !!slots && Number.isInteger(maxLength) && maxLength >= 1 && maxLength <= 200)
    && field.referenceAnswers.every(value => text(value, answerSetTextLimit(field)));
}

export function validCaseField(field) {
  if (!field || !safeId(field.id) || !text(field.label, 100) || !text(field.explanation, 20000)
      || !Array.isArray(field.rubric) || !field.rubric.length || field.rubric.length > 20
      || !field.rubric.every(point => text(point, 2000))
      || !field.grading || Object.keys(field.grading).length !== 1) return false;
  const {type, grading, referenceAnswers, choices, maxLength} = field;
  if (grading.method !== 'exactChoiceSet' && (!Array.isArray(referenceAnswers)
      || !referenceAnswers.length || referenceAnswers.length > 20
      || !referenceAnswers.every(value => text(value, 2000)))) return false;
  if (grading.method !== 'exactChoiceSet' && field.correctChoiceIds !== undefined) return false;
  if (type !== 'answerSet' && field.answerSet !== undefined || type !== 'numeric' && field.numeric !== undefined) return false;
  if (choices !== undefined && (!['singleChoice', 'answerSet'].includes(type) || !validChoices(field))) return false;
  if (type === 'singleChoice') return Array.isArray(choices);
  if (type === 'answerSet') return (grading.method !== 'exactChoiceSet' || Array.isArray(choices)) && validAnswerSet(field);
  if (type === 'numeric') return validNumericField(field);
  const methods = type === 'shortText' ? ['exactText', 'self'] : type === 'freeText' ? ['self'] : [];
  return methods.includes(grading.method) && Number.isInteger(maxLength) && maxLength >= 1 && maxLength <= 2000
    && referenceAnswers.every(value => text(value, maxLength));
}
