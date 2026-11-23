import {caseCorrectChoiceIds, caseReferenceAnswers} from './case-field.js';
import {normalizeAnswerText} from './answer-grading.js';

export function caseFeedback(field, revision, choiceField = field) {
  let answers;
  if (choiceField.choices) {
    answers = caseCorrectChoiceIds(choiceField).map(id => {
      const choice = choiceField.choices.find(option => option.id === id);
      const text = choice.text.trim() && choice.text.trim() !== choice.label
        ? choice.text
        : revision?.answerLabels?.[choice.label];
      return text ? {text, code: choice.label} : {text: choice.label};
    });
  } else if (revision?.answerLabels) {
    const codes = caseReferenceAnswers(field).flatMap(value => value.split(/[,，、／/]/).map(part => part.trim()));
    answers = codes.map(code => ({text: revision.answerLabels[code], code}));
  } else {
    answers = caseReferenceAnswers(field).map(text => ({text}));
  }
  const rubric = revision ? revision.rubric || [] : field.rubric.filter(point => !/公式採点・部分点基準ではない/.test(normalizeAnswerText(point)));
  return {
    answers,
    explanation: revision?.explanation ?? field.explanation,
    rubric,
    reviewPoint: revision?.reviewPoint,
    source: revision?.source
  };
}
