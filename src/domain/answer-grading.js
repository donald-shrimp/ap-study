export const normalizeAnswerText = value => value.normalize('NFKC').trim();

export function sameAnswerSet(response, expected) {
  if (response.length !== expected.length) return false;
  const unique = new Set(expected);
  return unique.size === expected.length
    && new Set(response).size === response.length
    && response.every(value => unique.has(value));
}
