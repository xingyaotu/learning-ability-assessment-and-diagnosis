import { describe, it, expect } from "vitest";
import { runAssessment } from "../../src/engine/assessment-runner";

const sampleInput = {
  M: [3, 2, 4],
  E: [1, 2, 1],
  C: [4, 4, 3],
  E2: [2, 3, 2],
};

describe("道层守护 — 集成测试", () => {
  it("priority_action.focus_label_zh 为中文维度名", () => {
    const result = runAssessment({ M: [0], E: [4], C: [4], E2: [4] });
    expect(result.priority_action.focus_label_zh).toBe("动机");
  });

  it("E 最弱时 focus=E/执行", () => {
    const result = runAssessment({ M: [4], E: [0], C: [4], E2: [4] });
    expect(result.priority_action.focus_dimension).toBe("E");
    expect(result.priority_action.focus_label_zh).toBe("执行");
  });

  it("运用阶段(score≈60)的 priority_action → 八步⑤=流程", () => {
    const result = runAssessment({
      M: [4, 4, 4],
      E: [4, 4, 4],
      C: [4, 4, 4],
      E2: [3, 2, 3],
    });
    if (result.priority_action.focus_dimension === "E2") {
      const e2Stage = result.per_dimension_mastery.E2;
      if (e2Stage.stage_id === 5) {
        expect(result.priority_action.eight_step_name_zh).toBe("流程");
      }
    }
  });
});

describe("runAssessment — 完整结构", () => {
  it("返回 mece_scores 含四维", () => {
    const result = runAssessment(sampleInput);
    expect(result.mece_scores.M).toBeGreaterThanOrEqual(0);
    expect(result.mece_scores.E).toBeGreaterThanOrEqual(0);
    expect(result.mece_scores.C).toBeGreaterThanOrEqual(0);
    expect(result.mece_scores.E2).toBeGreaterThanOrEqual(0);
    expect(result.mece_scores.overall).toBeGreaterThanOrEqual(0);
  });

  it("overall_mastery stage_id 在 1-7", () => {
    const result = runAssessment(sampleInput);
    expect(result.overall_mastery.stage_id).toBeGreaterThanOrEqual(1);
    expect(result.overall_mastery.stage_id).toBeLessThanOrEqual(7);
  });

  it("per_dimension_mastery 含 M/E/C/E2 四维", () => {
    const result = runAssessment(sampleInput);
    expect(result.per_dimension_mastery.M).toBeDefined();
    expect(result.per_dimension_mastery.E).toBeDefined();
    expect(result.per_dimension_mastery.C).toBeDefined();
    expect(result.per_dimension_mastery.E2).toBeDefined();
  });

  it("priority_action.focus_dimension = mece_scores.weakest_dimension", () => {
    const result = runAssessment(sampleInput);
    expect(result.priority_action.focus_dimension).toBe(result.mece_scores.weakest_dimension);
  });

  it("assessed_at 是 ISO datetime", () => {
    const result = runAssessment(sampleInput);
    expect(() => new Date(result.assessed_at).toISOString()).not.toThrow();
  });

  it("全满分 → stage 7 创新", () => {
    const result = runAssessment({ M: [4, 4, 4], E: [4, 4, 4], C: [4, 4, 4], E2: [4, 4, 4] });
    expect(result.overall_mastery.stage_id).toBe(7);
    expect(result.overall_mastery.stage_name_zh).toBe("创新");
  });

  it("全零分 → stage 1 不会", () => {
    const result = runAssessment({ M: [0, 0], E: [0, 0], C: [0, 0], E2: [0, 0] });
    expect(result.overall_mastery.stage_id).toBe(1);
    expect(result.overall_mastery.stage_name_zh).toBe("不会");
  });

  it("priority_action.eight_step_id 在 1-8", () => {
    const result = runAssessment(sampleInput);
    expect(result.priority_action.eight_step_id).toBeGreaterThanOrEqual(1);
    expect(result.priority_action.eight_step_id).toBeLessThanOrEqual(8);
  });

  it("priority_action.flywheel_id 在 1-6", () => {
    const result = runAssessment(sampleInput);
    expect(result.priority_action.flywheel_id).toBeGreaterThanOrEqual(1);
    expect(result.priority_action.flywheel_id).toBeLessThanOrEqual(6);
  });
});
