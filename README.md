# UniSydneyBuddy Skill Hub

一个面向悉尼大学学生的中英双语 AI 课程工作台。MVP 将 Canvas 等来源中的课程资料转化为：

1. Semester Brief
2. Weekly Brief
3. Individual / Group Project Plan

开发与 Prompt 调试以中文为主；课程原文和证据保留英文，生成结果可切换中文或英文。

## 当前阶段

当前版本覆盖 QBUS6600、MKTG6018、MKTG6104 和 SIEN6006，并实现：

- 四课程 Course Overview、Class Structure、Assessment Map 与 Week 1–13
- 中英双语 Semester Overview、Weekly Brief 与 Project Planner
- Canvas Connector 真实只读同步，并将匹配的 Assignment 说明与 Rubric 载入 Project
- Canvas 作业列表直达独立 Assignment Analysis 页面
- 个人任务拆解与 3–6 人小组 Part / Owner / Reviewer 规划
- 可选 OpenAI Structured Outputs 实时解析：分工 / 任务、内容框架与明确文档要求
- 明确的 AI 分析动作、课程隔离和 SQLite 跨会话结果持久化
- Canvas 增量同步提示、资料变更失效提醒和结果反馈
- 四课程 Weekly AI Evaluation 数据集与可选真实 API Eval
- 73 项自动测试、数据校验和真实浏览器验收

## 数据边界

真实课程材料只能放在 `data/private/`，该目录不会被 Git 跟踪。公开 Demo 使用脱敏或虚构数据。

## 本地验证

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/validate_gold.py
```

## 启动当前原型

```bash
source .venv/bin/activate
streamlit run app.py
```

### 持久保存 OpenAI API Key

复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml`，并在本机文件中填写：

```toml
OPENAI_API_KEY = "你的 OpenAI API Key"
```

真实 `secrets.toml` 已被 `.gitignore` 排除，不会上传 GitHub。不要把真实 Key 写入示例文件、代码、聊天或截图。

未配置 `OPENAI_API_KEY` 时，页面只展示 Canvas 事实，不生成假 AI 结果。AI 结果、同步历史和用户反馈保存在被 Git 忽略的 SQLite 文件中；Canvas 原始资料仍保存在独立快照中。连接 Canvas 本身不会触发模型调用。

## Evaluation

四门课程的 Weekly Brief Eval 配置位于 `data/evals/weekly_ai_cases.json`：

```bash
python scripts/run_weekly_ai_evals.py
python scripts/run_weekly_ai_evals.py --live  # 会实际调用已配置的 OpenAI API
```

## 公开部署

`render.yaml` 定义唯一的线上产品路径：Streamlit Web + Canvas Sync API。线上网站生成私人 `sync_id` 地址，浏览器插件将只读快照发送到该地址。部署前在 Render 配置 `OPENAI_API_KEY`，并确认 Sync API 实际域名与插件权限一致。

详细步骤、成本边界和发布检查见 [公开部署说明](./docs/DEPLOYMENT.md)。

学生端产品只保留三个核心模块：Semester Overview、Weekly Brief 和 Project Planner。Semester Overview 使用 Unit Outline 和 Canvas 数据展示 Week 1–13；Weekly Brief 只总结已同步的 Canvas Module，按 Module Summary、关键知识点、详细讲解和内容目录组织；Project Planner 从 Canvas 作业列表进入独立 Assignment Analysis 页面，并支持个人任务和 3–6 人小组规划。

## Canvas Connector

`canvas_connector/` 提供一个只读 Chrome Manifest V3 扩展。它使用浏览器当前已登录的 `canvas.sydney.edu.au` 会话读取用户主动选择的 Courses、Modules、Pages、Assignments 和 Announcements，并把快照发送到本机 `127.0.0.1:8765`。不要求 Canvas 密码或个人 API token。

安装与权限说明见 [`canvas_connector/README.md`](canvas_connector/README.md)。同步数据保存在被 Git 忽略的 `data/local/`；Canvas 同步不等于允许发送资料给 OpenAI。

通知变更和 Eval 不占用学生主界面；Evidence 和自动化 Eval 继续作为内部质量控制。模型使用 Structured Outputs 返回稳定字段，且文档清单只允许出现来源中明确要求或建议的项目。

完整资料：

- [产品文档](./docs/PRODUCT_SPEC_v1.0.md)
- [测试与合理性报告](./docs/TEST_REPORT_v1.0.md)
- [课程数据导入报告](./docs/course-ingestion-report.md)
- [产品反馈记录](./docs/feedback-log.md)
- [历史 PRD v0.1](./UniSydneyBuddy_Skill_Hub_PRD_v0.1.md)
