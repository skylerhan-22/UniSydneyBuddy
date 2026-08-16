# UniSydneyBuddy Canvas Connector

Chrome Manifest V3 只读浏览器插件。它使用当前已登录的 `canvas.sydney.edu.au` 浏览器会话读取学生主动选择的课程，并发送到用户在插件中配置的 UniSydneyBuddy 私人同步地址。

## 安装

1. 启动 UniSydneyBuddy：`streamlit run app.py`。
2. Chrome 打开 `chrome://extensions`。
3. 开启右上角 **Developer mode**。
4. 点击 **Load unpacked**，选择本目录 `canvas_connector/`。
5. 打开并正常登录 `https://canvas.sydney.edu.au/`。
6. 从 UniSydneyBuddy 的“连接 Canvas Connector”区域复制私人同步地址，填入插件。
7. 点击扩展图标，选择课程并同步。
8. 回到网站点击“检查最新同步”。

## 当前只读范围

- Courses 与 syllabus body
- Modules 与 Module Items
- Module 中的 Canvas Pages
- Assignments、due dates、submission types 与可见 Rubric
- Announcements

不读取成绩、提交记录、讨论回复、同学名单或教师管理数据。不调用任何 Canvas 写入接口。

本地开发时同步地址为 `http://127.0.0.1:8765/canvas-sync`，快照保存在被 Git 忽略的 `data/local/`。公开部署时使用网站生成的带随机 `sync_id` 的私人同步地址。Canvas 同步不会自动调用 OpenAI；只有学生主动生成 Weekly Brief 或 Assignment Analysis 时才调用模型。

## 当前限制

- 仅支持 `canvas.sydney.edu.au`。
- Echo360、Ed、Turnitin、Canvas Studio 等第三方 LTI 内容不在 Canvas REST API 的直接覆盖范围内。
- 尚未经过 Chrome Web Store 或悉尼大学安全审核；正式发布前需完成权限说明与隐私审查。
