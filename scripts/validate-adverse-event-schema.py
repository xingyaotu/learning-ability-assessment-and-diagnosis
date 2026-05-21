#!/usr/bin/env python3
"""
道层测评异常事件 schema 验证脚本 v1.0
验证 pipeline-data/assessment-adverse-event-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. event_categories: 4个分类全覆盖 + 各分类 event_types 非空
  3. aec-data 含 MECE 维度缺失事件 + _dao_guard 含'MECE'
  4. aec-data 含飞轮 θ 越界事件 + _dao_guard 含'六飞轮'
  5. aec-quality 含七阶异常事件 + _dao_guard 含'七阶'
  6. aec-quality 含道层漂移检测事件 + _dao_guard 含'道层'
  7. aec-pipl 含 PIPL-02 (未成年/HALT) + action 含 'HALT-CSO'
  8. adverse_event_record_schema 核心字段 + severity enum 4级 + category_id enum 4个
  9. severity_response_times: 4级 + critical=1h
  10. validation_rules: 4类事件/飞轮/七阶/MECE/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ADVERSE_EVENT_PATH = REPO_ROOT / "pipeline-data" / "assessment-adverse-event-schema.json"

REQUIRED_CATEGORY_IDS = {"aec-data", "aec-technical", "aec-quality", "aec-pipl"}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
SEVERITY_LEVELS = {"low", "medium", "high", "critical"}

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
    print("  测评异常事件 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not ADVERSE_EVENT_PATH.exists():
        fail(f"找不到文件: {ADVERSE_EVENT_PATH}")
        sys.exit(1)
    data = json.loads(ADVERSE_EVENT_PATH.read_text(encoding="utf-8"))
    ok("assessment-adverse-event-schema.json 加载成功")

    categories = data.get("event_categories", [])

    # [2] 4个分类全覆盖
    print("\n[2] event_categories 4个分类全覆盖")
    found_cats = {c.get("category_id") for c in categories}
    missing_cats = REQUIRED_CATEGORY_IDS - found_cats
    if missing_cats:
        fail(f"缺少事件分类: {missing_cats}")
    else:
        ok(f"4个事件分类全覆盖 ✓ {sorted(found_cats)}")
    for c in categories:
        cid = c.get("category_id", "?")
        et = c.get("event_types", [])
        if et:
            ok(f"{cid}: event_types {len(et)}个 ✓")
        else:
            fail(f"{cid}: event_types 为空")

    # [3] aec-data MECE 维度缺失 + _dao_guard 含'MECE'
    print("\n[3] aec-data MECE 维度缺失事件 + _dao_guard")
    aec_data = next((c for c in categories if c.get("category_id") == "aec-data"), None)
    if aec_data is None:
        fail("aec-data 分类缺失")
    else:
        data_events_str = str(aec_data.get("event_types", []))
        if "MECE" in data_events_str:
            ok("aec-data event_types 提及 MECE ✓")
        else:
            fail("aec-data event_types 未提及 MECE")
        # Check specific MECE event _dao_guard
        mece_event = next((e for e in aec_data.get("event_types", []) if "MECE" in str(e)), None)
        if mece_event and "MECE" in mece_event.get("_dao_guard", ""):
            ok("aec-data MECE 事件 _dao_guard 含'MECE' ✓")
        else:
            fail("aec-data MECE 事件 _dao_guard 缺失或未含'MECE'")

    # [4] aec-data 飞轮 θ 越界事件 + _dao_guard 含'六飞轮'
    print("\n[4] aec-data 飞轮 θ 越界 + _dao_guard 含'六飞轮'")
    if aec_data:
        fw_event = next((e for e in aec_data.get("event_types", [])
                         if "飞轮" in e.get("event_name", "") or "飞轮" in str(e.get("trigger", ""))), None)
        if fw_event:
            ok(f"aec-data 含飞轮事件 '{fw_event.get('event_name')}' ✓")
            if "六飞轮" in fw_event.get("_dao_guard", ""):
                ok("飞轮事件 _dao_guard 含'六飞轮' ✓")
            else:
                fail(f"飞轮事件 _dao_guard='{fw_event.get('_dao_guard','')}' 未含'六飞轮'")
        else:
            fail("aec-data 未含飞轮 θ 越界事件")

    # [5] aec-quality 七阶异常事件 + _dao_guard 含'七阶'
    print("\n[5] aec-quality 七阶异常事件 + _dao_guard 含'七阶'")
    aec_quality = next((c for c in categories if c.get("category_id") == "aec-quality"), None)
    if aec_quality is None:
        fail("aec-quality 分类缺失")
    else:
        stage_event = next((e for e in aec_quality.get("event_types", [])
                            if "七阶" in str(e) or "stage" in str(e).lower()), None)
        if stage_event:
            ok(f"aec-quality 含七阶事件 '{stage_event.get('event_name')}' ✓")
            if "七阶" in stage_event.get("_dao_guard", ""):
                ok("七阶事件 _dao_guard 含'七阶' ✓")
            else:
                fail(f"七阶事件 _dao_guard='{stage_event.get('_dao_guard','')}' 未含'七阶'")
        else:
            fail("aec-quality 未含七阶异常事件")

    # [6] aec-quality 道层漂移检测 + _dao_guard 含'道层'
    print("\n[6] aec-quality 道层漂移检测 + _dao_guard 含'道层'")
    if aec_quality:
        drift_event = next((e for e in aec_quality.get("event_types", [])
                            if "漂移" in str(e.get("event_name", "")) or "道层" in str(e.get("_dao_guard", ""))), None)
        if drift_event:
            ok(f"aec-quality 含道层漂移事件 '{drift_event.get('event_name')}' ✓")
            if "道层" in drift_event.get("_dao_guard", ""):
                ok("道层漂移事件 _dao_guard 含'道层' ✓")
            else:
                fail(f"道层漂移事件 _dao_guard='{drift_event.get('_dao_guard','')}' 未含'道层'")
            if drift_event.get("severity") == "critical":
                ok("道层漂移事件 severity=critical ✓")
            else:
                fail(f"道层漂移事件 severity={drift_event.get('severity')} ≠ critical")
        else:
            fail("aec-quality 未含道层漂移检测事件")

    # [7] aec-pipl PIPL-02 含 HALT-CSO
    print("\n[7] aec-pipl HALT-CSO 守护")
    aec_pipl = next((c for c in categories if c.get("category_id") == "aec-pipl"), None)
    if aec_pipl is None:
        fail("aec-pipl 分类缺失")
    else:
        pipl_events = aec_pipl.get("event_types", [])
        halt_event = next((e for e in pipl_events if "HALT" in str(e.get("action", ""))), None)
        if halt_event:
            ok(f"aec-pipl 含 HALT-CSO 事件 '{halt_event.get('event_name')}' ✓")
            if halt_event.get("severity") == "critical":
                ok("HALT 事件 severity=critical ✓")
            else:
                fail(f"HALT 事件 severity={halt_event.get('severity')} ≠ critical")
        else:
            fail("aec-pipl 未含 HALT-CSO 处置事件")
        for pe in pipl_events:
            pid = pe.get("event_type_id", "?")
            if pe.get("severity") in ["high", "critical"]:
                ok(f"{pid}: severity={pe['severity']} 高危等级 ✓")
            else:
                fail(f"{pid}: severity={pe.get('severity')} 低于 high")

    # [8] adverse_event_record_schema
    print("\n[8] adverse_event_record_schema 核心字段")
    rec_fields = data.get("adverse_event_record_schema", {}).get("fields", {})
    required_rec = {"event_id", "session_id", "student_id", "event_type_id",
                    "category_id", "severity", "detected_at", "status"}
    missing_rec = required_rec - set(rec_fields.keys())
    if missing_rec:
        fail(f"adverse_event_record_schema 缺少字段: {missing_rec}")
    else:
        ok(f"adverse_event_record_schema {len(rec_fields)}个字段 核心字段全覆盖 ✓")

    sev_enum = set(rec_fields.get("severity", {}).get("enum", []))
    if sev_enum == SEVERITY_LEVELS:
        ok("severity enum 4级全覆盖 ✓")
    else:
        fail(f"severity enum {sev_enum} ≠ {SEVERITY_LEVELS}")

    cat_enum = set(rec_fields.get("category_id", {}).get("enum", []))
    if cat_enum == REQUIRED_CATEGORY_IDS:
        ok("category_id enum 4分类全覆盖 ✓")
    else:
        fail(f"category_id enum {cat_enum} ≠ {REQUIRED_CATEGORY_IDS}")

    status_enum = set(rec_fields.get("status", {}).get("enum", []))
    if "cso_halt" in status_enum:
        ok(f"status enum 含 cso_halt ✓")
    else:
        fail("status enum 未含 cso_halt")

    # [9] severity_response_times
    print("\n[9] severity_response_times 4级响应时效")
    srt = data.get("severity_response_times", {})
    for sev in ["low", "medium", "high", "critical"]:
        if sev in srt:
            ok(f"severity_response_times.{sev} 存在 ✓")
        else:
            fail(f"severity_response_times.{sev} 缺失")
    critical_srt = srt.get("critical", {})
    if critical_srt.get("max_response_hours") == 1:
        ok("critical max_response_hours=1h ✓")
    else:
        fail(f"critical max_response_hours={critical_srt.get('max_response_hours')} ≠ 1")

    # [10] validation_rules
    print("\n[10] validation_rules 合规")
    vr = data.get("validation_rules", {})
    ec_count = vr.get("event_categories_count", 0)
    if ec_count == 4:
        ok("validation_rules.event_categories_count=4 ✓")
    else:
        fail(f"validation_rules.event_categories_count={ec_count} ≠ 4")

    mece_codes = set(vr.get("mece_dimension_codes", []))
    if mece_codes == MECE_DIMENSIONS:
        ok("validation_rules.mece_dimension_codes MECE 四维度 ✓")
    else:
        fail(f"validation_rules.mece_dimension_codes {mece_codes} ≠ {MECE_DIMENSIONS}")

    fw_names = set(vr.get("six_flywheel_valid_names", []))
    missing_fw = VALID_FLYWHEEL_NAMES - fw_names
    if missing_fw:
        fail(f"six_flywheel_valid_names 缺少: {missing_fw}")
    elif len(fw_names) == 6:
        ok("validation_rules.six_flywheel_valid_names 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_valid_names 数量 {len(fw_names)} ≠ 6")

    stage_names = set(vr.get("seven_stage_valid_names", []))
    missing_st = VALID_STAGE_NAMES - stage_names
    if missing_st:
        fail(f"seven_stage_valid_names 缺少: {missing_st}")
    elif len(stage_names) == 7:
        ok("validation_rules.seven_stage_valid_names 七阶全覆盖 ✓")
    else:
        fail(f"seven_stage_valid_names 数量 {len(stage_names)} ≠ 7")

    pipl_halt = vr.get("pipl_halt_event", "")
    if "aet-pipl" in pipl_halt:
        ok(f"validation_rules.pipl_halt_event='{pipl_halt}' ✓")
    else:
        fail(f"validation_rules.pipl_halt_event='{pipl_halt}' 未指向 aet-pipl")

    pipl_vr = vr.get("pipl_constraints", "")
    if "PIPL" in pipl_vr and "匿名" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失")

    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "匿名" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
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
        print("  ✅ 测评异常事件 schema 验证 PASS — 4类事件/道层守护/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
