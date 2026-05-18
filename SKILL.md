---
name: assessment-toolkit-dispatcher
description: |
  星耀途学习力测评与诊断工具包 — 22 项测评 SOP 分发接口。
  根据当前测评需求(MECE/JUMEQ/CAMIQ/FIRE-UP + 七阶位)选择并执行对应诊断工具。
  Use when 系统或教练端触发学员学习力诊断、升学规划、职业匹配、生涯分析场景时。
version: "1.0.0"
repo: xingyaotu/learning-ability-assessment-and-diagnosis
portal: xyt-coach, xyt-hq
dao_compliance: v5.0
---

# 学习力测评与诊断工具包 — SOP 分发接口 (assessment-toolkit-dispatcher)

## 一、22 项测评工具分发表 (assessment dispatch)

### MECE 维度 — 4 项工具

| tool_id | 测评名 | 密码维度 | IRT 模型 |
|---|---|---|---|
| `assess_mece_motivation` | 学习动力测评 | M-动力(Motivation) | 2PL |
| `assess_mece_execution` | 学习执行力测评 | E-执行力(Execution) | 2PL |
| `assess_mece_capability` | 学习能力测评 | C-能力(Capability) | 3PL |
| `assess_mece_environment` | 学习环境测评 | E-环境(Environment) | 1PL |

> MECE = M-动力/E-执行力/C-能力/E-环境（4 字母，严格枚举）

### JUMEQ 维度 — 5 项工具

| tool_id | 测评名 | 密码维度 |
|---|---|---|
| `assess_jumeq_jobplacement` | 就业方向测评 | J-就业方向(Jobplacement) |
| `assess_jumeq_university` | 院校目标测评 | U-院校目标(University) |
| `assess_jumeq_major` | 专业匹配测评 | M-专业选择(Major) |
| `assess_jumeq_economy` | 经济区位测评 | E-经济区位(Economy) |
| `assess_jumeq_qualification` | 升学资质测评 | Q-资质综合(Qualification) |

### CAMIQ 维度 — 5 项工具

| tool_id | 测评名 | 密码维度 |
|---|---|---|
| `assess_camiq_character` | 性格类型测评 | C-性格(Character) |
| `assess_camiq_aptitude` | 职业适性测评 | A-适性(Aptitude) |
| `assess_camiq_monetary` | 薪酬期望测评 | M-薪资(Monetary) |
| `assess_camiq_interest` | 职业兴趣测评 | I-兴趣(Interest) |
| `assess_camiq_qualification` | 职业胜任力测评 | Q-职业资质(Qualification) |

### FIRE-UP 维度 — 6 项工具

| tool_id | 测评名 | 密码维度 | 权重 |
|---|---|---|---|
| `assess_fireup_family` | 家庭支持测评 | F-家庭(Family) | 0.15 |
| `assess_fireup_individual` | 个体差异测评 | I-个体(Individual) | 0.25 |
| `assess_fireup_resources` | 资源盘点测评 | R-资源(Resources) | 0.15 |
| `assess_fireup_ecosystem` | 生态环境测评 | E-生态(Ecosystem) | 0.10 |
| `assess_fireup_usability` | 可用性测评 | U-可用性(Usability) | 0.15 |
| `assess_fireup_pathways` | 路径灵活性测评 | P-路径(Pathways) | 0.20 |

> FIRE-UP = F/I/R/E/U/P 6 字母，权重总和 = 0.15+0.25+0.15+0.10+0.15+0.20 = 1.00

### 综合测评 — 2 项工具

| tool_id | 测评名 | 说明 |
|---|---|---|
| `assess_mastery_stages` | 七阶位综合测评 | 跨所有知识点的掌握层级快照 |
| `assess_flywheels_self_eval` | 六飞轮自评 | 计划/预习/复习/听课/作业/考试完成率自评 |

## 二、七阶位诊断映射 (stage × quadruple)

诊断结果输出的四元组 (knowledge_point_id, stage_id, eight_step_id, six_flywheel_id)：

| 七阶位 | stage | 推荐八步 | 推荐飞轮 |
|---|---|---|---|
| 不会 | 1 | 八步①穿透 | 飞轮①计划 |
| 模糊 | 2 | 八步①穿透 | 飞轮②预习 |
| 清晰 | 3 | 八步②提取 | 飞轮②预习 |
| 框架 | 4 | 八步③整理 | 飞轮③复习 |
| 运用 | 5 | 八步⑤流程 | 飞轮⑤作业 |
| 熟练 | 6 | 八步⑦分析 | 飞轮⑤作业 |
| 创新 | 7 | 八步⑧估分 | 飞轮⑥考试 |

> 八步⑤ = **流程**（step5 = 流程，固定映射）

## 三、诊断路由规则 (diagnostic routing)

```
输入: { user_id, goal: "升学"|"就业"|"生涯"|"学力", current_stage?, subject? }

路由逻辑:
  goal="升学" → JUMEQ 5项 + mastery_stages 综合
  goal="就业" → CAMIQ 5项 + FIRE-UP 6项
  goal="生涯" → FIRE-UP 6项 (加权合成得分)
  goal="学力" → MECE 4项 + mastery_stages
  goal="全量" → 22项全量诊断
  + 六飞轮自评作为所有目标的基线采集
```

## 四、分发到教练工具包 (→ coaching dispatch)

测评完成后，诊断结果传入教练工具包：

```
assessment-toolkit SKILL.md (本文件)
  ↓ (quadruple: stage_id, eight_step_id, six_flywheel_id)
learning-coaching-toolkit/SKILL.md
  → SOP_{01-08}.md (八步 SOP)
  → SOP_FW{1-6}.md (六飞轮 SOP)
```

## 五、道层合规检查 (compliance)

- [ ] MECE = 4 字母：M-动力/E-执行力/C-能力/E-环境（不是 Mutually Exclusive）
- [ ] JUMEQ = 5 字母（升学密码）
- [ ] CAMIQ = 5 字母（职业密码）
- [ ] FIRE-UP = 6 字母 F/I/R/E/U/P（不是5字母）
- [ ] 四密码字段合计：4+5+5+6 = 20 字段
- [ ] 八步第⑤步映射 = 流程（step5 = 流程，固定）
- [ ] 六飞轮 = 计划/预习/复习/听课/作业/考试（flywheel_id 1-6）
- [ ] 七阶位 = 不会/模糊/清晰/框架/运用/熟练/创新（stage 1-7）
