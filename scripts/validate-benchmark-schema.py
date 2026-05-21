#!/usr/bin/env python3
"""
道层测评基准对比 schema 验证脚本 v1.0
验证 pipeline-data/assessment-benchmark-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. benchmark_groups: 3个基准组全覆盖
  3. 每个基准组: mece_benchmark_stats 含 M/E_exec/C/E_env 均值
  4. 每个基准组: flywheel_benchmark_stats 含六飞轮均值
  5. 每个基准组: stage_distribution 七阶全覆盖 + 分布和 = 1.0
  6. 每个基准组 _dao_guard 含'七阶'/'六飞轮' 守护
  7. benchmark_comparison_schema 核心字段 + mece_percentiles 4维度 + flywheel_percentiles 6飞轮
  8. stage_vs_benchmark: student_stage/benchmark_modal_stage enum 七阶
  9. benchmark_update_protocol: 6步流程
  10. validation_rules: 3组/MECE/六飞轮/七阶/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BENCHMARK_PATH = REPO_ROOT / "pipeline-data" / "assessment-benchmark-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
REQUIRED_BENCHMARK_IDS = {"bm-national-avg", "bm-gaokao-ready", "bm-junior-high"}

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
    print("  测评基准对比 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not BENCHMARK_PATH.exists():
        fail(f"找不到文件: {BENCHMARK_PATH}")
        sys.exit(1)
    data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    ok("assessment-benchmark-schema.json 加载成功")

    groups = data.get("benchmark_groups", [])

    # [2] 3个基准组全覆盖
    print("\n[2] benchmark_groups 3个基准组全覆盖")
    found_ids = {g.get("benchmark_id") for g in groups}
    missing_ids = REQUIRED_BENCHMARK_IDS - found_ids
    if missing_ids:
        fail(f"缺少基准组: {missing_ids}")
    else:
        ok(f"3个基准组全覆盖 ✓ {sorted(found_ids)}")

    for g in groups:
        bid = g.get("benchmark_id", "?")
        msn = g.get("min_sample_size", 0)
        if msn >= 500:
            ok(f"{bid}: min_sample_size={msn} ≥ 500 ✓")
        else:
            fail(f"{bid}: min_sample_size={msn} < 500")

    # [3] mece_benchmark_stats MECE 四维度均值
    print("\n[3] mece_benchmark_stats MECE 四维度均值")
    for g in groups:
        bid = g.get("benchmark_id", "?")
        mbs = g.get("mece_benchmark_stats", {})
        mbs_dims = {k.replace("_theta_mean", "").replace("_theta_sd", "")
                    for k in mbs.keys() if "_theta_mean" in k}
        if mbs_dims == MECE_DIMENSIONS:
            ok(f"{bid}: mece_benchmark_stats 四维度均值全覆盖 ✓")
        else:
            fail(f"{bid}: mece_benchmark_stats 维度 {mbs_dims} ≠ {MECE_DIMENSIONS}")

    # [4] flywheel_benchmark_stats 六飞轮均值
    print("\n[4] flywheel_benchmark_stats 六飞轮均值")
    for g in groups:
        bid = g.get("benchmark_id", "?")
        fbs = g.get("flywheel_benchmark_stats", {})
        fw_keys = {k.replace("_theta_mean", "") for k in fbs.keys() if "_theta_mean" in k}
        if fw_keys == VALID_FLYWHEEL_NAMES:
            ok(f"{bid}: flywheel_benchmark_stats 六飞轮均值全覆盖 ✓")
        else:
            fail(f"{bid}: flywheel_benchmark_stats 飞轮 {fw_keys} ≠ {VALID_FLYWHEEL_NAMES}")

    # [5] stage_distribution 七阶 + 分布和 = 1.0
    print("\n[5] stage_distribution 七阶全覆盖 + 分布和 = 1.0")
    for g in groups:
        bid = g.get("benchmark_id", "?")
        sd = g.get("stage_distribution", {})
        stage_keys = set(sd.keys())
        missing_stages = VALID_STAGE_NAMES - stage_keys
        if missing_stages:
            fail(f"{bid}: stage_distribution 缺少阶位: {missing_stages}")
        else:
            ok(f"{bid}: stage_distribution 七阶全覆盖 ✓")
        total = sum(sd.values())
        if abs(total - 1.0) < 1e-9:
            ok(f"{bid}: stage_distribution 和 = {total:.4f} = 1.0 ✓")
        else:
            fail(f"{bid}: stage_distribution 和 = {total:.4f} ≠ 1.0")

    # [6] _dao_guard 含守护关键词
    print("\n[6] 每个基准组 _dao_guard 道层守护")
    for g in groups:
        bid = g.get("benchmark_id", "?")
        guard = g.get("_dao_guard", "")
        if "七阶" in guard:
            ok(f"{bid}: _dao_guard 含'七阶' ✓")
        else:
            fail(f"{bid}: _dao_guard='{guard}' 未含'七阶'")

    # [7] benchmark_comparison_schema 核心字段
    print("\n[7] benchmark_comparison_schema 核心字段")
    bcs = data.get("benchmark_comparison_schema", {}).get("fields", {})
    required_bcs = {"comparison_id", "student_id", "session_id", "benchmark_id",
                    "comparison_date", "mece_percentiles", "flywheel_percentiles"}
    missing_bcs = required_bcs - set(bcs.keys())
    if missing_bcs:
        fail(f"benchmark_comparison_schema 缺少字段: {missing_bcs}")
    else:
        ok(f"benchmark_comparison_schema {len(bcs)}个字段 核心字段全覆盖 ✓")

    # mece_percentiles 4维度
    mece_pct_props = bcs.get("mece_percentiles", {}).get("properties", {})
    mece_pct_dims = {k.replace("_percentile", "") for k in mece_pct_props.keys() if k.endswith("_percentile")}
    if MECE_DIMENSIONS <= mece_pct_dims:
        ok("mece_percentiles 含 MECE 四维度 ✓")
    else:
        fail(f"mece_percentiles 维度 {mece_pct_dims} 未含全部 MECE")

    # flywheel_percentiles 六飞轮
    fw_pct_props = bcs.get("flywheel_percentiles", {}).get("properties", {})
    fw_pct_keys = {k.replace("_percentile", "") for k in fw_pct_props.keys() if k.endswith("_percentile")}
    if fw_pct_keys == VALID_FLYWHEEL_NAMES:
        ok("flywheel_percentiles 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_percentiles 飞轮 {fw_pct_keys} ≠ {VALID_FLYWHEEL_NAMES}")

    bench_enum = set(bcs.get("benchmark_id", {}).get("enum", []))
    if bench_enum == REQUIRED_BENCHMARK_IDS:
        ok("benchmark_comparison_schema.benchmark_id enum 3个基准组 ✓")
    else:
        fail(f"benchmark_id enum {bench_enum} ≠ {REQUIRED_BENCHMARK_IDS}")

    # [8] stage_vs_benchmark 七阶 enum
    print("\n[8] stage_vs_benchmark 七阶枚举")
    svb = bcs.get("stage_vs_benchmark", {}).get("properties", {})
    student_stage_enum = set(svb.get("student_stage", {}).get("enum", []))
    bench_modal_enum = set(svb.get("benchmark_modal_stage", {}).get("enum", []))
    if student_stage_enum == VALID_STAGE_NAMES:
        ok("stage_vs_benchmark.student_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"student_stage enum {student_stage_enum} ≠ {VALID_STAGE_NAMES}")
    if bench_modal_enum == VALID_STAGE_NAMES:
        ok("stage_vs_benchmark.benchmark_modal_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"benchmark_modal_stage enum {bench_modal_enum} ≠ {VALID_STAGE_NAMES}")

    # [9] benchmark_update_protocol
    print("\n[9] benchmark_update_protocol 更新流程")
    bup = data.get("benchmark_update_protocol", {})
    steps = bup.get("steps", [])
    if len(steps) >= 6:
        ok(f"benchmark_update_protocol.steps {len(steps)}步 ≥ 6 ✓")
    else:
        fail(f"benchmark_update_protocol.steps {len(steps)} < 6")
    if bup.get("version_control"):
        ok("benchmark_update_protocol.version_control 存在 ✓")
    else:
        fail("benchmark_update_protocol.version_control 缺失")

    # [10] validation_rules
    print("\n[10] validation_rules 合规")
    vr = data.get("validation_rules", {})
    bg_count = vr.get("benchmark_groups_count", 0)
    if bg_count == 3:
        ok("validation_rules.benchmark_groups_count=3 ✓")
    else:
        fail(f"validation_rules.benchmark_groups_count={bg_count} ≠ 3")

    stage_constraint = vr.get("stage_distribution_sum_constraint", "")
    if "1.0" in stage_constraint:
        ok("validation_rules.stage_distribution_sum_constraint 含 1.0 ✓")
    else:
        fail("validation_rules.stage_distribution_sum_constraint 缺失")

    mece_codes = set(vr.get("mece_dimension_codes", []))
    if mece_codes == MECE_DIMENSIONS:
        ok("validation_rules.mece_dimension_codes MECE 四维度 ✓")
    else:
        fail(f"mece_dimension_codes {mece_codes} ≠ {MECE_DIMENSIONS}")

    fw_names = set(vr.get("six_flywheel_valid_names", []))
    if fw_names == VALID_FLYWHEEL_NAMES:
        ok("validation_rules.six_flywheel_valid_names 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_valid_names {fw_names} ≠ {VALID_FLYWHEEL_NAMES}")

    stage_names = set(vr.get("seven_stage_valid_names", []))
    if stage_names == VALID_STAGE_NAMES:
        ok("validation_rules.seven_stage_valid_names 七阶全覆盖 ✓")
    else:
        fail(f"seven_stage_valid_names {stage_names} ≠ {VALID_STAGE_NAMES}")

    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "匿名" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")

    pipl_vr = vr.get("pipl_constraints", "")
    if "PIPL" in pipl_vr and "匿名" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失或不完整")

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
        print("  ✅ 测评基准对比 schema 验证 PASS — 3基准组/MECE/七阶/六飞轮/分布归一 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
