import { z } from "zod";

export const MASTERY_STAGE_NAMES = [
  "不会",
  "模糊",
  "清晰",
  "框架",
  "运用",
  "熟练",
  "创新",
] as const;

export const EIGHT_STEP_NAMES = [
  "穿透",
  "提取",
  "整理",
  "审题",
  "流程",
  "批改",
  "分析",
  "估分",
] as const;

export const SIX_FLYWHEEL_NAMES = [
  "计划飞轮",
  "预习飞轮",
  "复习飞轮",
  "听课飞轮",
  "作业飞轮",
  "考试飞轮",
] as const;

export const MECE_DIMENSION_KEYS = ["M", "E", "C", "E2"] as const;
export type MeceDimensionKey = (typeof MECE_DIMENSION_KEYS)[number];

export const MECE_DIMENSION_LABELS: Record<MeceDimensionKey, string> = {
  M: "动机",
  E: "执行",
  C: "能力",
  E2: "环境",
};

export const StageIdSchema = z.number().int().min(1).max(7);
export const EightStepIdSchema = z.number().int().min(1).max(8);
export const FlywheelIdSchema = z.number().int().min(1).max(6);

export const DimensionAnswersSchema = z.array(z.number().int().min(0).max(4)).min(1);

export const MeceAnswersInputSchema = z.object({
  M: DimensionAnswersSchema,
  E: DimensionAnswersSchema,
  C: DimensionAnswersSchema,
  E2: DimensionAnswersSchema,
});
export type MeceAnswersInput = z.infer<typeof MeceAnswersInputSchema>;

export const MeceScoreSchema = z.object({
  M: z.number().min(0).max(100),
  E: z.number().min(0).max(100),
  C: z.number().min(0).max(100),
  E2: z.number().min(0).max(100),
  overall: z.number().min(0).max(100),
  weakest_dimension: z.enum(MECE_DIMENSION_KEYS),
  weakest_label_zh: z.string(),
});
export type MeceScore = z.infer<typeof MeceScoreSchema>;

export const MasteryStageOutputSchema = z.object({
  stage_id: StageIdSchema,
  stage_name_zh: z.enum(MASTERY_STAGE_NAMES),
  recommended_eight_step_id: EightStepIdSchema,
  recommended_eight_step_name_zh: z.enum(EIGHT_STEP_NAMES),
  recommended_flywheel_id: FlywheelIdSchema,
  recommended_flywheel_name_zh: z.enum(SIX_FLYWHEEL_NAMES),
});
export type MasteryStageOutput = z.infer<typeof MasteryStageOutputSchema>;

export const AssessmentResultSchema = z.object({
  mece_scores: MeceScoreSchema,
  overall_mastery: MasteryStageOutputSchema,
  per_dimension_mastery: z.object({
    M: MasteryStageOutputSchema,
    E: MasteryStageOutputSchema,
    C: MasteryStageOutputSchema,
    E2: MasteryStageOutputSchema,
  }),
  priority_action: z.object({
    focus_dimension: z.enum(MECE_DIMENSION_KEYS),
    focus_label_zh: z.string(),
    eight_step_id: EightStepIdSchema,
    eight_step_name_zh: z.enum(EIGHT_STEP_NAMES),
    flywheel_id: FlywheelIdSchema,
    flywheel_name_zh: z.enum(SIX_FLYWHEEL_NAMES),
  }),
  assessed_at: z.string(),
});
export type AssessmentResult = z.infer<typeof AssessmentResultSchema>;
