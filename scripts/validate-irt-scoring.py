#!/usr/bin/env python3
"""
道层 IRT 评分阈值验证脚本 v1.0
验证 pipeline-data/irt-scoring-thresholds.json 的合规性。

验证项:
  1. JSON 文件加载
  2. global_thresholds: 七阶全量覆盖 + 边界无缺口 + 无重叠
  3. tool_specific_thresholds: 工具ID存在于 catalog + 七阶覆盖 + 边界连续
  4. aggregation_rules 权重归一化
  5. MECE 复合公式系数之和 == 1.0
  6. scoring_pipeline 步骤连续 (1→N)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATALOG_PATH = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
THRESH_PATH = REPO_ROOT / "pipeline-data" / "irt-scoring-thresholds.json"

VALID_STAGE_IDS = list(range(1, 8))
VALID_STAGE_NAMES = {
    1: "不会", 2: "模糊", 3: "清晰", 4: "框架",
    5: "运用", 6: "熟练", 7: "创新"
}
WEIGHT_TOLERANCE = 1e-9

PASS_COUNT = 0
FAIL_COUNT = 0
ERRORS: list[str] = []


def ok(msg: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    global FAIL_COUNT
    FAIL_COUNT += 1
    ERRORS.append(f"❌ {msg}")
    print(f"  ❌ {msg}")


def validate_stage_boundaries(boundaries: list, ctx: str) -> None:
    """Validate 7-stage boundary coverage, ordering, and continuity."""
    stage_ids = [b["stage_id"] for b in boundaries]
    if sorted(stage_ids) != VALID_STAGE_IDS:
        fail(f"{ctx}: stage_id 集合 {sorted(stage_ids)} 不等于 {VALID_STAGE_IDS}")
        return
    ok(f"{ctx}: 七阶 1-7 全量覆盖 ✓")

    # names
    for b in boundaries:
        sid = b["stage_id"]
        sname = b.get("stage_name", "")
        if sname != VALID_STAGE_NAMES[sid]:
            fail(f"{ctx}/stage{sid}: name='{sname}' 期望 '{VALID_STAGE_NAMES[sid]}'")
        else:
            ok(f"{ctx}/stage{sid}: name='{sname}' ✓")

    # boundary continuity: stage N theta_max == stage N+1 theta_min
    sorted_b = sorted(boundaries, key=lambda x: x["stage_id"])
    for i in range(len(sorted_b) - 1):
        curr = sorted_b[i]
        nxt = sorted_b[i + 1]
        curr_max = curr.get("theta_max")
        nxt_min = nxt.get("theta_min")
        if curr_max is None or nxt_min is None:
            fail(f"{ctx}/stage{curr['stage_id']}→{nxt['stage_id']}: 边界含 null 但非首/末段")
        elif abs(curr_max - nxt_min) > 1e-9:
            fail(f"{ctx}/stage{curr['stage_id']} theta_max={curr_max} ≠ "
                 f"stage{nxt['stage_id']} theta_min={nxt_min} (边界不连续)")
        else:
            ok(f"{ctx}/stage{curr['stage_id']}→{nxt['stage_id']}: 边界连续 "
               f"θ={curr_max} ✓")

    # first stage has null min, last has null max
    first = sorted_b[0]
    last = sorted_b[-1]
    if first.get("theta_min") is not None:
        fail(f"{ctx}/stage1: theta_min 应为 null (−∞)")
    else:
        ok(f"{ctx}/stage1: theta_min=null (−∞) ✓")
    if last.get("theta_max") is not None:
        fail(f"{ctx}/stage7: theta_max 应为 null (+∞)")
    else:
        ok(f"{ctx}/stage7: theta_max=null (+∞) ✓")


def validate_weights(weights: dict, ctx: str) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        fail(f"{ctx}: 权重之和 = {total:.6f} ≠ 1.0")
    else:
        ok(f"{ctx}: 权重之和 = {total:.4f} ≈ 1.0 ✓")


def main() -> None:
    print("=" * 62)
    print("  IRT 评分阈值验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not THRESH_PATH.exists():
        fail(f"找不到阈值文件: {THRESH_PATH}")
        sys.exit(1)
    if not CATALOG_PATH.exists():
        fail(f"找不到 catalog: {CATALOG_PATH}")
        sys.exit(1)
    thresh = json.loads(THRESH_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    ok("irt-scoring-thresholds.json + catalog 加载成功")
    catalog_ids = {t["tool_id"] for t in catalog.get("assessment_tools", [])}

    # [2] global_thresholds
    print("\n[2] global_thresholds 七阶覆盖 + 边界连续性")
    global_b = thresh.get("global_thresholds", {}).get("stage_boundaries", [])
    validate_stage_boundaries(global_b, "global")

    # [3] tool_specific_thresholds
    print("\n[3] tool_specific_thresholds 工具ID + 边界连续性")
    for ts in thresh.get("tool_specific_thresholds", []):
        tid = ts.get("tool_id", "?")
        if tid not in catalog_ids:
            fail(f"tool_specific tool_id='{tid}' 不在 catalog")
        else:
            ok(f"tool_specific '{tid}' 存在于 catalog ✓")
        validate_stage_boundaries(ts.get("stage_boundaries", []), f"tool:{tid}")

    # [4] aggregation_rules 权重归一化
    print("\n[4] aggregation_rules 维度权重归一化")
    overrides = (thresh.get("aggregation_rules", {})
                 .get("multi_dimension_scoring", {})
                 .get("dimension_weight_overrides", {}))
    for tool_id, weights in overrides.items():
        validate_weights(weights, f"weights:{tool_id}")

    # [5] MECE composite 系数之和
    print("\n[5] MECE 复合公式系数之和")
    mece_formula = thresh.get("aggregation_rules", {}).get("mece_composite", {}).get("formula", "")
    import re
    coeffs = [float(x) for x in re.findall(r'(\d+\.\d+)\*', mece_formula)]
    if coeffs:
        total = sum(coeffs)
        if abs(total - 1.0) > 1e-9:
            fail(f"MECE 复合公式系数之和 = {total:.4f} ≠ 1.0")
        else:
            ok(f"MECE 公式系数之和 = {total:.2f} ✓ ({coeffs})")
    else:
        fail("MECE 复合公式解析失败")

    # [6] scoring_pipeline 步骤连续
    print("\n[6] scoring_pipeline 步骤连续性")
    steps = thresh.get("scoring_pipeline", {}).get("steps", [])
    step_nums = [s["step"] for s in steps]
    expected = list(range(1, len(steps) + 1))
    if step_nums == expected:
        ok(f"scoring_pipeline 步骤 {step_nums} 连续 ✓")
    else:
        fail(f"scoring_pipeline 步骤 {step_nums} 不连续，期望 {expected}")

    # ── 结果 ──────────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    total = PASS_COUNT + FAIL_COUNT
    print(f"  结果: {PASS_COUNT}/{total} 通过 | {FAIL_COUNT} 失败")
    print("=" * 62)
    if FAIL_COUNT > 0:
        print("\n失败详情:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  ✅ IRT 评分阈值验证 PASS — θ→七阶配置全部合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
