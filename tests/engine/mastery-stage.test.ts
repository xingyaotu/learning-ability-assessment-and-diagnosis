import { describe, it, expect } from "vitest";
import { scoreToStageId, calculateMasteryStage } from "../../src/engine/mastery-stage-calculator";

describe("道层守护 — 七阶 × 八步 × 六飞轮", () => {
  it("第5阶(运用)→第5步=流程 ★核心规则", () => {
    const result = calculateMasteryStage(60);
    expect(result.stage_id).toBe(5);
    expect(result.stage_name_zh).toBe("运用");
    expect(result.recommended_eight_step_id).toBe(5);
    expect(result.recommended_eight_step_name_zh).toBe("流程");
  });

  it("流程步骤名非演示/拆解/讲解/类比", () => {
    const result = calculateMasteryStage(60);
    expect(result.recommended_eight_step_name_zh).not.toBe("演示");
    expect(result.recommended_eight_step_name_zh).not.toBe("拆解");
    expect(result.recommended_eight_step_name_zh).not.toBe("讲解");
  });

  it("六飞轮无错题/笔记/阅读/实践", () => {
    const forbidden = ["错题", "笔记", "阅读", "实践"];
    for (let score = 0; score <= 100; score += 15) {
      const result = calculateMasteryStage(score);
      for (const word of forbidden) {
        expect(result.recommended_flywheel_name_zh).not.toContain(word);
      }
    }
  });

  it("七阶名称全覆盖: 不会/模糊/清晰/框架/运用/熟练/创新", () => {
    const scores = [0, 15, 30, 45, 60, 75, 90];
    const expectedNames = ["不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"];
    scores.forEach((score, idx) => {
      const result = calculateMasteryStage(score);
      expect(result.stage_name_zh).toBe(expectedNames[idx]);
    });
  });
});

describe("scoreToStageId — 阈值边界", () => {
  it("0 → stage 1 不会", () => expect(scoreToStageId(0)).toBe(1));
  it("14 → stage 1", () => expect(scoreToStageId(14)).toBe(1));
  it("15 → stage 2 模糊", () => expect(scoreToStageId(15)).toBe(2));
  it("29 → stage 2", () => expect(scoreToStageId(29)).toBe(2));
  it("30 → stage 3 清晰", () => expect(scoreToStageId(30)).toBe(3));
  it("45 → stage 4 框架", () => expect(scoreToStageId(45)).toBe(4));
  it("60 → stage 5 运用", () => expect(scoreToStageId(60)).toBe(5));
  it("75 → stage 6 熟练", () => expect(scoreToStageId(75)).toBe(6));
  it("90 → stage 7 创新", () => expect(scoreToStageId(90)).toBe(7));
  it("100 → stage 7", () => expect(scoreToStageId(100)).toBe(7));
});

describe("calculateMasteryStage — 完整映射", () => {
  it("stage 1: 穿透 + 计划飞轮", () => {
    const r = calculateMasteryStage(0);
    expect(r.recommended_eight_step_name_zh).toBe("穿透");
    expect(r.recommended_flywheel_name_zh).toBe("计划飞轮");
  });

  it("stage 2: 提取 + 预习飞轮", () => {
    const r = calculateMasteryStage(20);
    expect(r.recommended_eight_step_name_zh).toBe("提取");
    expect(r.recommended_flywheel_name_zh).toBe("预习飞轮");
  });

  it("stage 3: 整理 + 复习飞轮", () => {
    const r = calculateMasteryStage(35);
    expect(r.recommended_eight_step_name_zh).toBe("整理");
    expect(r.recommended_flywheel_name_zh).toBe("复习飞轮");
  });

  it("stage 4: 审题 + 听课飞轮", () => {
    const r = calculateMasteryStage(50);
    expect(r.recommended_eight_step_name_zh).toBe("审题");
    expect(r.recommended_flywheel_name_zh).toBe("听课飞轮");
  });

  it("stage 5: 流程★ + 作业飞轮", () => {
    const r = calculateMasteryStage(65);
    expect(r.recommended_eight_step_name_zh).toBe("流程");
    expect(r.recommended_flywheel_name_zh).toBe("作业飞轮");
  });

  it("stage 6: 分析 + 考试飞轮", () => {
    const r = calculateMasteryStage(80);
    expect(r.recommended_eight_step_name_zh).toBe("分析");
    expect(r.recommended_flywheel_name_zh).toBe("考试飞轮");
  });

  it("stage 7: 估分 + 计划飞轮(创新循环)", () => {
    const r = calculateMasteryStage(95);
    expect(r.stage_name_zh).toBe("创新");
    expect(r.recommended_eight_step_name_zh).toBe("估分");
    expect(r.recommended_flywheel_name_zh).toBe("计划飞轮");
  });

  it("溢出分数 150 → stage 7", () => {
    expect(calculateMasteryStage(150).stage_id).toBe(7);
  });

  it("负数分数 -5 → stage 1", () => {
    expect(calculateMasteryStage(-5).stage_id).toBe(1);
  });
});
