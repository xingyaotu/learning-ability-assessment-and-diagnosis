---
name: assessment-toolkit
description: |
  星耀途学习力测评套件 — 22 个测评工具，覆盖 MECE/JUMEQ/CAMIQ/FIRE-UP 四大诊断维度。
  每工具含七阶四元组(七阶 × 八步 × 六飞轮) + IRT 参数配置。
  Use when: 学员首次入学诊断、学期中期测评、升学规划诊断、飞轮激活评估。
  Triggers: 测评 / 诊断 / 学员能力评估 / MECE / JUMEQ / CAMIQ / FIRE-UP / IRT
version: "1.0.0"
portal: xyt-student
source: xingyaotu/learning-ability-assessment-and-diagnosis
assessment_catalog: pipeline-data/assessment-catalog.json
allowed-tools:
  - Read
---

# 学习力测评套件 (assessment-toolkit)

## 22 工具分组概览

| 分组 | 数量 | 工具名称 |
|---|---|---|
| MECE | 4 | 学习动力 / 学习执行力 / 学习能力 / 学习环境 |
| JUMEQ | 5 | 职业规划 / 大学意向 / 专业志愿 / 经济能力 / 资格认证 |
| CAMIQ | 5 | 性格特质 / 学科天赋 / 财务资源 / 学习兴趣 / 资质条件 |
| FIRE-UP | 6 | F家庭 / I个体 / R资源 / E生态 / U工具 / P路径 |
| 综合 | 2 | 掌握度阶段测评 / 六飞轮自评诊断 |

★ FIRE-UP 6字母: F=Family / I=Individual / R=Resources / E=Ecosystem / U=Usability / P=Pathways
★ FIRE-UP 权重总和: 0.20+0.25+0.15+0.15+0.10+0.15 = 1.00

## 诊断场景 → 工具选择

| 场景 | 推荐工具组合 |
|---|---|
| 新生入学全测 | MECE(4) + FIRE-UP(6) + mastery_stages |
| 升学规划诊断 | JUMEQ(5) + CAMIQ(5) |
| 学习瓶颈诊断 | MECE(4) + mastery_stages |
| 六飞轮激活评估 | flywheels_self_eval |
| 单科攻坚 | mastery_stages + CAMIQ(aptitude) |

## IRT 参数规格

| 模型 | 适用工具 | 参数 |
|---|---|---|
| 1PL | assess_jumeq_economy, assess_camiq_monetary | 仅难度参数 |
| 2PL | 大多数工具(16个) | 难度 + 区分度 |
| 3PL | assess_mastery_stages | 难度 + 区分度 + 猜测参数(0.25) |

difficulty_range: 大多数 [-3,3] 或 [-2,3] 或 [-2,2]

## 调用接口

```
invoke assessment-toolkit:
  scenario: "入学全测" | "升学规划" | "飞轮评估" | "瓶颈诊断" | "单科攻坚"
  tool_id:    string?  # 直接指定任意 22 工具 tool_id
  student_id: string
  subject:    string?  # 可选,科目
```

读取工具目录:
```
Read pipeline-data/assessment-catalog.json
```

## 七阶 → 教练操作分发

测评完成后，按 stage_quadruples 分发至教练操作手册:
```
stage_id → eight_step_id → coaching-sops/eight-step-sops/SOP_{n}
         → six_flywheel_id → coaching-sops/flywheel-sops/SOP_FW{n}
```
参见: xingyaotu/learning-coaching-toolkit `SKILL.md`

## 道层约束

- ⑤ = 流程(八步第5步唯一合法名称,绝无例外)
- 六飞轮 = 计划 / 预习 / 复习 / 听课 / 作业 / 考试(不得替换)
- FIRE-UP 6字母: F=Family / I=Individual / R=Resources / E=Ecosystem / U=Usability / P=Pathways
- cso-required: 否(纯测评规格,无 API key 引用)
- PIPL 提示: 学员年龄 < 14 岁 → 需触发 cso-required 审查
