import { MASTERY_STAGE_NAMES, EIGHT_STEP_NAMES, SIX_FLYWHEEL_NAMES } from "./schemas";
import type { MasteryStageOutput } from "./schemas";

const STAGE_MIN_SCORES = [0, 15, 30, 45, 60, 75, 90] as const;

// Stage → eight step (⑤=流程 is the core rule: stage 5 运用 → step 5 流程)
const STAGE_EIGHT_STEP_MAP: [number, number, number, number, number, number, number] =
  [1, 2, 3, 4, 5, 7, 8];
// 不会→穿透 | 模糊→提取 | 清晰→整理 | 框架→审题 | 运用→流程★ | 熟练→分析 | 创新→估分

// Stage → flywheel (六飞轮: 计划/预习/复习/听课/作业/考试)
const STAGE_FLYWHEEL_MAP: [number, number, number, number, number, number, number] =
  [1, 2, 3, 4, 5, 6, 1];
// 不会→计划 | 模糊→预习 | 清晰→复习 | 框架→听课 | 运用→作业 | 熟练→考试 | 创新→计划(循环)

export function scoreToStageId(score: number): 1 | 2 | 3 | 4 | 5 | 6 | 7 {
  const clamped = Math.min(100, Math.max(0, score));
  for (let i = STAGE_MIN_SCORES.length - 1; i >= 0; i--) {
    if (clamped >= STAGE_MIN_SCORES[i]) {
      return (i + 1) as 1 | 2 | 3 | 4 | 5 | 6 | 7;
    }
  }
  return 1;
}

export function calculateMasteryStage(score: number): MasteryStageOutput {
  const stage_id = scoreToStageId(score);
  const idx = stage_id - 1;
  const eight_step_id = STAGE_EIGHT_STEP_MAP[idx];
  const flywheel_id = STAGE_FLYWHEEL_MAP[idx];

  return {
    stage_id,
    stage_name_zh: MASTERY_STAGE_NAMES[idx],
    recommended_eight_step_id: eight_step_id,
    recommended_eight_step_name_zh: EIGHT_STEP_NAMES[eight_step_id - 1],
    recommended_flywheel_id: flywheel_id,
    recommended_flywheel_name_zh: SIX_FLYWHEEL_NAMES[flywheel_id - 1],
  };
}
