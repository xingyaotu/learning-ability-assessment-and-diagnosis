#!/usr/bin/env python3
"""
道层测评常模表验证脚本 v1.0
验证 pipeline-data/assessment-norm-tables.json 的合规性。

验证项:
  1. JSON 文件加载
  2. norm_groups: 4个常模组存在
  3. 每组 theta_percentiles 11个键 (p10-p99)
  4. 百分位数单调递增
  5. stage_distribution 七阶全覆盖 且和 ≈ 1.0
  6. mece_norms 8个键全覆盖
  7. percentile_to_stage_guidance 映射覆盖全范围
  8. validation_rules 七阶枚举 + PIPL
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NORM_PATH = REPO_ROOT / "pipeline-data" / "assessment-norm-tables.json"

SEVEN_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
REQUIRED_PERCENTILE_KEYS = ["p10", "p20", "p30", "p40", "p50", "p60", "p70", "p80", "p90", "p95", "p99"]
REQUIRED_MECE_NORM_KEYS = {
    "M_mean", "M_sd", "E_exec_mean", "E_exec_sd",
    "C_theta_mean", "C_theta_sd", "E_env_mean", "E_env_sd"
}

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


def main() -> None:
    print("=" * 62)
    print("  测评常模表验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not NORM_PATH.exists():
        fail(f"找不到文件: {NORM_PATH}")
        sys.exit(1)
    data = json.loads(NORM_PATH.read_text(encoding="utf-8"))
    ok("assessment-norm-tables.json 加载成功")

    norm_groups = data.get("norm_groups", [])

    # [2] 4个常模组
    print("\n[2] 常模组数量")
    if len(norm_groups) >= 4:
        ok(f"{len(norm_groups)}个常模组 ≥ 4 ✓")
    else:
        fail(f"常模组数量 {len(norm_groups)} < 4")

    # [3-6] 逐组验证
    print("\n[3-6] 逐常模组验证")
    for ng in norm_groups:
        ngid = ng.get("norm_group_id", "?")
        ngname = ng.get("norm_group_name", "?")
        label = f"{ngid}({ngname})"

        # [3] theta_percentiles 11个键
        tp = ng.get("theta_percentiles", {})
        missing_keys = [k for k in REQUIRED_PERCENTILE_KEYS if k not in tp]
        if missing_keys:
            fail(f"{label}: theta_percentiles 缺少 {missing_keys}")
        else:
            ok(f"{label}: theta_percentiles 11个键全覆盖 ✓")

        # [4] 单调递增
        vals = [tp.get(k) for k in REQUIRED_PERCENTILE_KEYS if k in tp]
        if len(vals) >= 2:
            is_monotone = all(vals[i] < vals[i+1] for i in range(len(vals)-1))
            if is_monotone:
                ok(f"{label}: 百分位数单调递增 ✓ [{vals[0]:.1f} ~ {vals[-1]:.1f}]")
            else:
                fail(f"{label}: 百分位数非单调递增: {vals}")

        # [5] stage_distribution 七阶 + 和≈1.0
        sd = ng.get("stage_distribution", {})
        missing_stages = SEVEN_STAGE_NAMES - set(sd.keys())
        if missing_stages:
            fail(f"{label}: stage_distribution 缺少: {missing_stages}")
        else:
            ok(f"{label}: stage_distribution 七阶全覆盖 ✓")
            total = sum(sd.values())
            if abs(total - 1.0) < 0.01:
                ok(f"{label}: stage_distribution 之和 = {total:.3f} ≈ 1.0 ✓")
            else:
                fail(f"{label}: stage_distribution 之和 = {total:.3f} ≠ 1.0")

        # [6] mece_norms 8个键
        mn = ng.get("mece_norms", {})
        missing_mece = REQUIRED_MECE_NORM_KEYS - set(mn.keys())
        if missing_mece:
            fail(f"{label}: mece_norms 缺少: {missing_mece}")
        else:
            ok(f"{label}: mece_norms 8个键全覆盖 ✓")
        # SD should be positive
        for sd_key in ["M_sd", "E_exec_sd", "C_theta_sd", "E_env_sd"]:
            v = mn.get(sd_key, 0)
            if v > 0:
                ok(f"{label}: {sd_key}={v} > 0 ✓")
            else:
                fail(f"{label}: {sd_key}={v} ≤ 0 (SD 必须为正)")

    # [7] percentile_to_stage_guidance
    print("\n[7] percentile_to_stage_guidance 验证")
    ptsg = data.get("percentile_to_stage_guidance", {})
    mapping = ptsg.get("mapping", [])
    if len(mapping) >= 5:
        ok(f"percentile_to_stage_guidance {len(mapping)}条映射 ✓")
    else:
        fail(f"percentile_to_stage_guidance 仅 {len(mapping)} 条 < 5")

    # Check coverage [0, 100]
    all_ranges = [m.get("percentile_range", []) for m in mapping]
    flat_values = [v for r in all_ranges for v in r]
    if flat_values:
        if min(flat_values) <= 0:
            ok(f"映射覆盖起点 {min(flat_values)} ≤ 0 ✓")
        else:
            fail(f"映射起点 {min(flat_values)} > 0, 未覆盖低百分位")
        if max(flat_values) >= 100:
            ok(f"映射覆盖终点 {max(flat_values)} ≥ 100 ✓")
        else:
            fail(f"映射终点 {max(flat_values)} < 100, 未覆盖高百分位")

    for m in mapping:
        stage_ref = m.get("stage_reference", "")
        interp = m.get("interpretation", "")
        if stage_ref and interp:
            ok(f"映射 {m.get('percentile_range')}: stage_reference + interpretation 存在 ✓")
        else:
            fail(f"映射 {m.get('percentile_range')}: 缺少 stage_reference 或 interpretation")

    # [8] validation_rules
    print("\n[8] validation_rules 合规")
    vr = data.get("validation_rules", {})
    stage_enum = set(vr.get("stage_names_enum", []))
    if stage_enum == SEVEN_STAGE_NAMES:
        ok("validation_rules.stage_names_enum 七阶完整 ✓")
    else:
        fail(f"validation_rules.stage_names_enum 不完整: {stage_enum}")

    pct_monotonicity = vr.get("percentile_monotonicity", "")
    if pct_monotonicity:
        ok(f"percentile_monotonicity 规则存在 ✓")
    else:
        fail("percentile_monotonicity 规则缺失")

    pipl = vr.get("pipl_constraints", "")
    if "群体统计" in pipl or "匿名" in pipl or "PIPL" in pipl:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失")

    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "个体" not in pipl_meta.replace("不含个体", ""):
        ok("_meta.pipl_note PIPL 合规声明存在 ✓")
    elif "PIPL" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明存在 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")

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
        print("  ✅ 测评常模表验证 PASS — 全部常模配置合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
