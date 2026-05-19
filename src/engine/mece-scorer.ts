import { MeceAnswersInputSchema, MECE_DIMENSION_KEYS, MECE_DIMENSION_LABELS } from "./schemas";
import type { MeceAnswersInput, MeceScore, MeceDimensionKey } from "./schemas";

function averageScore(answers: number[]): number {
  if (answers.length === 0) return 0;
  const total = answers.reduce((sum, v) => sum + v, 0);
  return Math.round((total / (answers.length * 4)) * 100);
}

export function scoreMece(input: MeceAnswersInput): MeceScore {
  const parsed = MeceAnswersInputSchema.parse(input);
  const M = averageScore(parsed.M);
  const E = averageScore(parsed.E);
  const C = averageScore(parsed.C);
  const E2 = averageScore(parsed.E2);
  const overall = Math.round((M + E + C + E2) / 4);

  const scores: Record<MeceDimensionKey, number> = { M, E, C, E2 };
  const dimensionEntries = MECE_DIMENSION_KEYS.map(
    (k) => [k, scores[k]] as [MeceDimensionKey, number]
  );
  const weakest_dimension = dimensionEntries.reduce((weakest, current) =>
    current[1] < weakest[1] ? current : weakest
  )[0];

  return {
    M,
    E,
    C,
    E2,
    overall,
    weakest_dimension,
    weakest_label_zh: MECE_DIMENSION_LABELS[weakest_dimension],
  };
}
