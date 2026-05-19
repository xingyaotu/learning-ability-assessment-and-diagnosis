import { describe, it, expect } from "vitest";
import { scoreMece } from "../../src/engine/mece-scorer";

describe("道层守护 — MECE 四维度", () => {
  it("MECE 4维度 M动机/E执行/C能力/E2环境 全部存在", () => {
    const result = scoreMece({ M: [4], E: [4], C: [4], E2: [4] });
    expect(result.M).toBeDefined();
    expect(result.E).toBeDefined();
    expect(result.C).toBeDefined();
    expect(result.E2).toBeDefined();
  });

  it("weakest_dimension 标签 M=动机", () => {
    const result = scoreMece({ M: [0], E: [4], C: [4], E2: [4] });
    expect(result.weakest_dimension).toBe("M");
    expect(result.weakest_label_zh).toBe("动机");
  });

  it("weakest_dimension 标签 E=执行", () => {
    const result = scoreMece({ M: [4], E: [0], C: [4], E2: [4] });
    expect(result.weakest_label_zh).toBe("执行");
  });

  it("weakest_dimension 标签 C=能力", () => {
    const result = scoreMece({ M: [4], E: [4], C: [0], E2: [4] });
    expect(result.weakest_label_zh).toBe("能力");
  });

  it("weakest_dimension 标签 E2=环境", () => {
    const result = scoreMece({ M: [4], E: [4], C: [4], E2: [0] });
    expect(result.weakest_label_zh).toBe("环境");
  });
});

describe("scoreMece — 基础计算", () => {
  it("全满分 → 所有维度 100 + overall 100", () => {
    const result = scoreMece({ M: [4, 4, 4], E: [4, 4, 4], C: [4, 4, 4], E2: [4, 4, 4] });
    expect(result.M).toBe(100);
    expect(result.E).toBe(100);
    expect(result.C).toBe(100);
    expect(result.E2).toBe(100);
    expect(result.overall).toBe(100);
  });

  it("全零分 → overall=0", () => {
    const result = scoreMece({ M: [0, 0], E: [0, 0], C: [0, 0], E2: [0, 0] });
    expect(result.overall).toBe(0);
  });

  it("单题满分 → 维度=100", () => {
    const result = scoreMece({ M: [4], E: [4], C: [4], E2: [4] });
    expect(result.M).toBe(100);
  });

  it("2分/4分量表 → 50分", () => {
    const result = scoreMece({ M: [2], E: [2], C: [2], E2: [2] });
    expect(result.M).toBe(50);
    expect(result.overall).toBe(50);
  });

  it("混合答案 [4,2,0] → M=50", () => {
    const result = scoreMece({ M: [4, 2, 0], E: [4], C: [4], E2: [4] });
    expect(result.M).toBe(50);
  });

  it("overall = 四维平均", () => {
    const result = scoreMece({ M: [4], E: [0], C: [2], E2: [2] });
    expect(result.overall).toBe(50);
  });

  it("多题数组正确平均", () => {
    const result = scoreMece({ M: [4, 4], E: [2, 2], C: [0, 0], E2: [4, 4] });
    expect(result.M).toBe(100);
    expect(result.E).toBe(50);
    expect(result.C).toBe(0);
    expect(result.overall).toBe(Math.round((100 + 50 + 0 + 100) / 4));
  });
});

describe("scoreMece — weakest_dimension", () => {
  it("四维相同 → weakest 稳定", () => {
    const result = scoreMece({ M: [2], E: [2], C: [2], E2: [2] });
    expect(["M", "E", "C", "E2"]).toContain(result.weakest_dimension);
  });

  it("E2 唯一最低", () => {
    const result = scoreMece({ M: [4], E: [3], C: [3], E2: [0] });
    expect(result.weakest_dimension).toBe("E2");
  });
});

describe("scoreMece — Zod 校验", () => {
  it("空数组应抛错", () => {
    expect(() => scoreMece({ M: [], E: [2], C: [2], E2: [2] })).toThrow();
  });

  it("答案超出范围 5 应抛错", () => {
    expect(() => scoreMece({ M: [5], E: [2], C: [2], E2: [2] })).toThrow();
  });

  it("负数答案应抛错", () => {
    expect(() => scoreMece({ M: [-1], E: [2], C: [2], E2: [2] })).toThrow();
  });
});
