#!/usr/bin/env python3
"""
道层 IRT 标定种子验证脚本 v1.0
验证 pipeline-data/irt-calibration-seed.json 与 assessment-catalog.json 的一致性。

验证项:
  1. 种子文件存在且 JSON 有效
  2. 种子工具数量 == 22 (与 catalog 一致)
  3. 种子工具 ID 集合与 catalog 完全匹配
  4. 每个工具的 model 字段与 catalog.irt_config.model 一致
  5. 1PL 工具所有 item 的 a 参数 == 1.0 (Rasch 约束)
  6. 2PL 工具所有 item 的 a 参数 ∈ [0.5, 2.0]
  7. 3PL 工具所有 item 含 c 参数 ∈ [0, 0.35]
  8. 所有 item 的 b 参数 ∈ [-3.0, 3.5]
  9. 所有 item 的 stage_target ∈ {1, 2, 3, 4, 5, 6, 7}
 10. 六飞轮自评工具维度名称严格枚举合规
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATALOG_PATH = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
SEED_PATH = REPO_ROOT / "pipeline-data" / "irt-calibration-seed.json"

VALID_STAGES = {1, 2, 3, 4, 5, 6, 7}
B_MIN, B_MAX = -3.0, 3.5
A_MIN, A_MAX = 0.5, 2.0
C_MAX = 0.35
VALID_FLYWHEEL_DIM_NAMES = {"计划飞轮执行度", "预习飞轮执行度", "复习飞轮执行度",
                             "听课飞轮执行度", "作业飞轮执行度", "考试飞轮执行度"}

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


def validate_items(tool_id: str, model: str, dimensions: list) -> None:
    for dim in dimensions:
        dim_name = dim.get("dimension", "?")
        for item in dim.get("items", []):
            iid = item.get("item_id", "?")
            b = item.get("b")
            stage = item.get("stage_target")
            a = item.get("a")
            c = item.get("c")

            # b range
            if b is None or not (B_MIN <= b <= B_MAX):
                fail(f"{tool_id}/{dim_name}/{iid}: b={b} 超出 [{B_MIN},{B_MAX}]")

            # stage_target
            if stage not in VALID_STAGES:
                fail(f"{tool_id}/{dim_name}/{iid}: stage_target={stage} 不在 {VALID_STAGES}")

            # model-specific
            if model == "1PL":
                if a != 1.0:
                    fail(f"{tool_id}/{dim_name}/{iid}: 1PL a={a} 必须=1.0")
                if c is not None:
                    fail(f"{tool_id}/{dim_name}/{iid}: 1PL 不应含 c 参数")
            elif model == "2PL":
                if a is None or not (A_MIN <= a <= A_MAX):
                    fail(f"{tool_id}/{dim_name}/{iid}: 2PL a={a} 超出 [{A_MIN},{A_MAX}]")
                if c is not None:
                    fail(f"{tool_id}/{dim_name}/{iid}: 2PL 不应含 c 参数")
            elif model == "3PL":
                if a is None or not (A_MIN <= a <= A_MAX):
                    fail(f"{tool_id}/{dim_name}/{iid}: 3PL a={a} 超出 [{A_MIN},{A_MAX}]")
                if c is None or not (0 <= c <= C_MAX):
                    fail(f"{tool_id}/{dim_name}/{iid}: 3PL c={c} 超出 [0,{C_MAX}]")


def main() -> None:
    print("=" * 62)
    print("  IRT 标定种子验证 v1.0 — seed ↔ catalog 一致性检查")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not CATALOG_PATH.exists():
        fail(f"找不到 catalog: {CATALOG_PATH}")
        sys.exit(1)
    if not SEED_PATH.exists():
        fail(f"找不到 seed: {SEED_PATH}")
        sys.exit(1)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    ok("catalog + seed 文件加载成功")

    catalog_tools = {t["tool_id"]: t for t in catalog.get("assessment_tools", [])}
    seed_items = seed.get("calibration_items", [])
    seed_tools = {t["tool_id"]: t for t in seed_items}

    # [2] 工具数量
    print(f"\n[2] 工具数量校验")
    if len(seed_items) == 22:
        ok(f"种子工具数 = 22 ✓")
    else:
        fail(f"种子工具数 = {len(seed_items)}，期望 22")

    # [3] 工具 ID 集合匹配
    print(f"\n[3] 工具 ID 集合匹配")
    cat_ids = set(catalog_tools.keys())
    seed_ids = set(seed_tools.keys())
    missing_in_seed = cat_ids - seed_ids
    extra_in_seed = seed_ids - cat_ids
    if missing_in_seed:
        fail(f"Catalog 有但 Seed 缺少: {missing_in_seed}")
    else:
        ok("Seed 覆盖全部 22 个 catalog 工具 ✓")
    if extra_in_seed:
        fail(f"Seed 含 Catalog 没有的工具: {extra_in_seed}")
    else:
        ok("Seed 无多余工具 ✓")

    # [4] model 字段一致性
    print(f"\n[4] model 字段与 catalog.irt_config 一致性")
    for tid, st in seed_tools.items():
        seed_model = st.get("model")
        cat_cfg = catalog_tools.get(tid, {}).get("irt_config", {})
        cat_model = cat_cfg.get("model")
        if seed_model != cat_model:
            fail(f"{tid}: seed.model={seed_model} ≠ catalog.model={cat_model}")
        else:
            ok(f"{tid}: model={seed_model} 一致 ✓")

    # [5] item 参数合规 (per-model)
    print(f"\n[5] item 参数合规验证 (1PL/2PL/3PL 规则)")
    for st in seed_items:
        validate_items(st["tool_id"], st["model"], st.get("dimensions", []))
    if FAIL_COUNT == 0:
        ok(f"全部 item 参数合规 ✓")

    # [6] 六飞轮自评维度名称
    print(f"\n[6] 六飞轮自评维度名称守护")
    fw_tool = seed_tools.get("assess_flywheels_self_eval")
    if fw_tool:
        actual_dims = {d["dimension"] for d in fw_tool.get("dimensions", [])}
        missing_dims = VALID_FLYWHEEL_DIM_NAMES - actual_dims
        illegal_dims = actual_dims - VALID_FLYWHEEL_DIM_NAMES
        if missing_dims:
            fail(f"assess_flywheels_self_eval 缺少维度: {missing_dims}")
        elif illegal_dims:
            fail(f"assess_flywheels_self_eval 含非法维度: {illegal_dims}")
        else:
            ok(f"六飞轮自评 6维度名称全枚举合规 ✓")
    else:
        fail("assess_flywheels_self_eval 工具缺失")

    # [7] 统计汇总
    print(f"\n[7] 统计汇总")
    total_dims = sum(len(t["dimensions"]) for t in seed_items)
    total_it = sum(len(d["items"]) for t in seed_items for d in t["dimensions"])
    ok(f"22工具 {total_dims}维度 {total_it}题目 统计完成")

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
        print("  ✅ IRT 标定种子验证 PASS — 22 工具种子数据全部合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
