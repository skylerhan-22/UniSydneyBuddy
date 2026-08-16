# UniSydneyBuddy Skill Hub — 完整测试与产品合理性报告

- 报告版本：v1.0
- 被测版本：Demo v0.12
- 测试日期：2026-08-16
- 测试环境：macOS、Python 3.12、Streamlit、本地浏览器 `http://127.0.0.1:8501/`
- 结论：**通过当前本地 Demo 发布门槛**

## 1. 测试目标

本轮测试不仅检查“按钮是否能点”，同时验证：

- 功能是否符合学生真实学习流程；
- 四门课程是否能力一致且数据不串联；
- 中文与英文是否完整一致；
- 已知事实、未知信息和系统建议是否区分；
- 多文件、多 Assignment 和个人 / 小组模式是否合理；
- 产品文档是否与当前实现一致；
- 当前 Demo 是否存在过度 AI 宣称。

## 2. 执行结果摘要

| 检查项 | 结果 |
|---|---|
| 自动测试 | 70 passed |
| QBUS Gold 数据质量校验 | Pass |
| JSON Schema 与数据文件语法 | Pass |
| Python 编译检查 | Pass |
| Python 依赖完整性 | Pass，无 broken requirements |
| 三门补充课程 Assessment 权重 | 全部 100% |
| 三门补充课程周次 | 全部 13 周 |
| 真实浏览器中文主流程 | Pass |
| 真实浏览器英文主流程 | Pass |
| 运行时 Traceback | 未发现 |

## 3. 测试方法

### 3.1 自动化 UI 测试

使用 Streamlit AppTest 驱动应用，覆盖控件状态、课程切换、语言切换、Canvas Assignment 分析入口、计划导出和异常路径。

### 3.2 单元测试

覆盖文档分类、分段、语言检测、日期格式、Assignment 匹配、计划生成、模板生成、隐私阻断和导出内容。

### 3.3 数据与 Schema 测试

覆盖 JSON Schema、引用关系、重复 ID、日期格式、Assessment 权重、未知值保存和 QBUS Gold Dataset。

### 3.4 真实浏览器测试

在运行中的本地页面验证真实 DOM 和交互，包括课程目录、三个标签、Weekly Brief、Canvas 作业匹配与独立 Assignment Analysis 页面。

### 3.5 产品合理性审查

按“学生是否会误解、事实是否被发明、不同课程是否适用、状态是否符合预期、AI 是否被过度声明”五个维度人工评审。

## 4. 自动测试覆盖

共收集并通过 68 项当前有效测试。

| 测试层 | 主要覆盖 |
|---|---|
| App smoke | 页面启动、课程目录、核心标签、课程内容、AI 门槛与小组校验。 |
| Demo helpers | 日期、多语言、任务 Part、内容框架与导出。 |
| Ingestion | TXT / MD 读取、截图 OCR 路由、分类、分段、稳定哈希、TBA 保留。 |
| Mapper | 中英文结构化请求、Provider 可替换、私有来源阻断。 |
| Quality / Schema | JSON Schema、跨对象引用、权重、未知值、AI 不预分配成员。 |
| Course data | 四课程目录、Week 1–13、Assessment 100%、Canvas 发布边界。 |
| UI acceptance | 课程 × 周次、双语、Canvas-first 分析入口、AI 门槛、明确文档要求和错误路径。 |

## 5. 功能验收矩阵

### 5.1 全局导航

| 用例 | 预期 | 结果 |
|---|---|---|
| 四门课程直接可见 | 不打开下拉菜单即可点击 | Pass |
| 当前课程高亮 | 高亮与主内容一致 | Pass |
| 中 / EN 切换 | 标签和核心动作同步切换 | Pass |
| 非学生功能隐藏 | 无 Deploy、Eval、工程模式入口 | Pass |

### 5.2 Semester Overview

| 用例 | 预期 | 结果 |
|---|---|---|
| 四课程 Course Overview | 使用各自真实课程内容 | Pass |
| 四课程 Class Structure | QBUS 缺失信息明确标记，不省略模块 | Pass |
| Assessment Map | 卡片展示类别、占比、日期、交付物 | Pass |
| 中文日期 | 年月日格式 | Pass |
| Week 1–13 | 四课程均连续展示 | Pass |
| Assessment 权重 | 每门课程总计 100% | Pass |

### 5.3 Weekly Brief

| 用例 | 预期 | 结果 |
|---|---|---|
| 四课程 × 13 周 | 每一周均可选择且不报错 | Pass |
| 已同步 Module | 展示完整 Module 来源预览、内容目录与 AI 总结入口 | Pass |
| 未发布详细内容 | 不生成虚假准备事项 | Pass |
| 中文内容 | 普通动作中文，课程术语可保留英文 | Pass |
| 内容范围 | 仅处理 Canvas Module；不混入 Recording、Ed Lesson 或 Workshop | Pass |
| 文本连续性 | Weekly 内容使用连续文本与轻量分隔，不再使用内容卡片 | Pass |
| AI 输出结构 | Module Summary、关键知识点、详细讲解 | Pass |

### 5.4 Project Planner — 作业列表

| 用例 | 预期 | 结果 |
|---|---|---|
| 可规划作业列表 | 仅个人和小组作业 | Pass |
| 排除考试类 | Exam、Test、Quiz、Participation 不进入 | Pass |
| 未选择作业 | 无解析、计划和下载内容 | Pass |
| Canvas 状态 | 匹配 description / rubric 后显示“打开作业分析” | Pass |

### 5.5 Assignment Analysis

| 用例 | 预期 | 结果 |
|---|---|---|
| 打开作业分析 | 作业列表切换为独立详情，并提供返回入口 | Pass |
| 无 API | 禁用 AI 按钮并说明连接或额度问题 | Pass |
| 主动分析 | 点击“AI 分析此作业”后才调用模型 | Pass |
| 无额外确认 | 不显示同意复选框 | Pass |
| 两种语言 | 中英文使用相同分析状态与功能 | Pass |

### 5.6 个人与小组计划

| 用例 | 预期 | 结果 |
|---|---|---|
| 个人 Assignment | 个人任务拆解，无小组确认按钮 | Pass |
| 小组 Assignment | 人数、Part、Owner、Reviewer | Pass |
| MKTG6104 | 保留 4–6 人范围 | Pass |
| 人数未知 | 显示 Brief 待确认 | Pass |
| Owner 未完成 | 导出禁用并给出提示 | Pass |
| 执行计划 | 不再展示按日期倒排的通用计划 | Pass |

### 5.7 AI 内容框架、显式文档要求与导出

| 用例 | 预期 | 结果 |
|---|---|---|
| 内容框架 | 中英文均显示六部分框架与检查点 | Pass |
| 文档清单 | 只显示来源明确要求 / 建议项，并标明资料位置 | Pass |
| 模板下载 | 页面不提供单文件或 ZIP 模板 | Pass |
| 跨学科合理性 | 不默认要求 Python、EDA 或固定视频时长 | Pass |
| 完整计划 | 导出包含任务、负责人、内容框架和显式文档要求 | Pass |

### 5.8 状态与隐私

| 用例 | 预期 | 结果 |
|---|---|---|
| QBUS → MKTG | QBUS 文件和计划不出现 | Pass |
| 返回 QBUS | 原会话状态保持，不显示“恢复”提示 | Pass |
| 不同 Assignment | 文件和 Part 状态独立 | Pass |
| 临时文件 | 解析后删除 | Pass |
| 私有来源 | 未授权 Provider 调用被阻断 | Pass |
| Canvas Connector | 仅允许悉大域名、只读内容脚本、快照 Schema 校验与本地往返 | Pass |
| Canvas Assignment 接入 | SIEN6006 三项正式作业与 Canvas description / rubric 正确匹配并可本地载入；Participation 被排除 | Pass |

## 6. 真实浏览器验收记录

### 中文模式

- 页面无 Traceback。
- 四门课程按钮存在。
- MKTG6104 可切换并显示对应内容。
- Weekly Brief 可打开并显示已发布内容或未知提示。
- Project Planner 显示可规划作业、Canvas 同步状态与“打开作业分析”。
- 未选择或未主动分析时不显示伪 AI 结果。
- 页面不再显示粘贴、上传与同意复选框。

### 英文模式

- 标签显示 `Semester Overview / Weekly Brief / Project Planner`。
- Project Planner 显示 `Plannable assignments`。
- 独立页面显示 `Assignment Analysis` 与 `Analyse this assignment with AI`。
- 页面无 Traceback。

说明：浏览器测试验证真实渲染和导航；文件注入、分组和下载 payload 使用 AppTest 自动化验证。

## 7. 数据质量结果

### QBUS6600

- Gold Dataset 跨对象规则通过。
- Assessment 权重合计 100%。
- 小组人数 3–4 保持来源值。
- TBA 中间节点没有被伪造日期。
- 建议任务没有预先指定真实成员。

### MKTG6018、MKTG6104、SIEN6006

- 课程目录完整。
- Assessment 权重均为 100%。
- 每门课程均为 13 周。
- MKTG6018 与 SIEN6006 未知小组人数保持未知。
- MKTG6104 保留 Canvas 中的 4–6 人信息。
- 只有已观察到的 Canvas Week 内容进入详细 Weekly Brief。

## 8. 产品合理性评估

| 评估项 | 结论 | 说明 |
|---|---|---|
| 信息架构 | 合理 | 三个模块对应学期、每周、作业三个真实决策层。 |
| 分析前后逻辑 | 合理 | 已知 Assessment 与 AI 结果分离，避免未主动分析即生成。 |
| Canvas 资料逻辑 | 合理 | 作业 description 与 rubric 自动进入对应的独立分析页。 |
| 个人 / 小组差异 | 合理 | 个人不显示团队分工，小组要求 Owner 确认。 |
| 四课程适配 | 基本合理 | 通用计划与模板不再假设所有课程需要数据建模。 |
| 双语 | 合理 | 核心能力一致，保留必要课程术语。 |
| 事实边界 | 合理 | 未发布和未知字段不推测。 |
| AI 表达 | 已修正 | 当前规则计划称为系统建议，不冒充 LLM 推理。 |
| 隐私 | 适合受控本地 Demo | Canvas 正文仅在本地快照与当前 Session 暂存；外部模型调用需 API 与明确的“AI 分析此作业”动作。 |
| 长期使用 | 尚不充分 | 当前状态只在浏览器会话中保持，无数据库。 |

## 9. 本轮发现并修复的问题

1. **过度 AI 表达**：未连接 API 时不再展示分工、框架或文档清单；只显示本地归类结果。
2. **跨课程模板偏置**：模板默认 Python、EDA、固定视频。已改为跨学科通用模板。
3. **通用执行计划干扰核心解析**：已从 Project Planner 移除。
4. **模糊文件强制归类**：原规则可能把低信息文件归入默认小组作业。已改为人工确认。
5. **中文导出字段混用英文**：Weight / Due 已改为占比 / 截止日期。

## 10. 剩余风险与限制

### P1 — 完整 Brief 内容尚未结构化驱动计划

当前 Project 标题、占比、截止日期和 Deliverables 主要来自课程数据；Canvas Assignment description 与可见 Rubric 直接作为 AI 输入。Canvas API 未返回的附件正文、LTI 页面、页数或特殊规则仍可能缺失。

建议：下一版继续强化结构化抽取与 Unknowns；学生界面不强制展示逐字段 Evidence，避免破坏阅读连贯性。

### 已修复 — Session State 不是长期存储

AI 结果与反馈已写入 SQLite；公开版按匿名用户命名空间隔离。

后续仍需补充用户主动删除策略与数据保留期限。

### P1 — Assignment Matcher 仍是规则方法

标题、编号、Group 和 Reflection 场景覆盖较好，但复杂命名依赖人工确认。

建议：在规则前后增加模型分类和置信度阈值，低置信度仍保留人工确认。

### P2 — 扫描型 PDF

没有文字层的 PDF 需要 OCR，目前会报无法读取。

### P2 — Streamlit 原生控件语言

表格工具栏和上传组件存在少量平台默认英文，不影响核心产品双语能力。

## 11. 发布判断

### 建议

**可以作为本地作品集 Demo 发布和演示。**

理由：

- 核心学生流程完整；
- 四门课程与双语均已覆盖；
- 多文件、状态隔离和个人 / 小组差异可演示；
- 数据边界和未知信息处理清晰；
- 自动化与真实浏览器验证均通过；
- 当前能力与未来 AI 能力已在产品文档中明确区分。

### 不建议当前声称

- 不应声称已经自动理解任意学校的所有 Brief。
- 不应声称已经上线真实 LLM Agent。
- 不应声称支持长期云端同步或多用户协作。
- 不应把当前规则生成结果描述为可直接提交的学术内容。

## 12. 回归测试命令

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/validate_gold.py
.venv/bin/python -m compileall -q app.py src tests scripts
.venv/bin/pip check
```

预期结果：

- `70 passed`
- `PASS qbus6600_gold.json`
- 编译无错误
- `No broken requirements found`
