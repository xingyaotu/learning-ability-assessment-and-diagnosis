import { scoreMece } from "./mece-scorer";
import { calculateMasteryStage } from "./mastery-stage-calculator";
import { MECE_DIMENSION_LABELS } from "./schemas";
import type { MeceAnswersInput, AssessmentResult } from "./schemas";

export function runAssessment(input: MeceAnswersInput): AssessmentResult {
  const mece_scores = scoreMece(input);
  const overall_mastery = calculateMasteryStage(mece_scores.overall);

  const per_dimension_mastery = {
    M: calculateMasteryStage(mece_scores.M),
    E: calculateMasteryStage(mece_scores.E),
    C: calculateMasteryStage(mece_scores.C),
    E2: calculateMasteryStage(mece_scores.E2),
  };

  const weakDim = mece_scores.weakest_dimension;
  const weakStage = per_dimension_mastery[weakDim];

  return {
    mece_scores,
    overall_mastery,
    per_dimension_mastery,
    priority_action: {
      focus_dimension: weakDim,
      focus_label_zh: MECE_DIMENSION_LABELS[weakDim],
      eight_step_id: weakStage.recommended_eight_step_id,
      eight_step_name_zh: weakStage.recommended_eight_step_name_zh,
      flywheel_id: weakStage.recommended_flywheel_id,
      flywheel_name_zh: weakStage.recommended_flywheel_name_zh,
    },
    assessed_at: new Date().toISOString(),
  };
}
