# UniSydneyBuddy 公开部署说明

## 上线形态

产品只有一个学生可见的网站，不区分 Demo 模式和真实模式。`render.yaml` 会创建两个技术服务：

1. `unisydneybuddy`：学生访问的 Streamlit 网站。
2. `unisydneybuddy-sync`：浏览器插件上传只读 Canvas 快照的同步接口。

第二项是后台接口，不是第二个产品页面。学生仍只使用 UniSydneyBuddy 网站和 Canvas Connector 插件。

## 数据流

1. 网站为每个浏览器生成一段不可猜测的私人 `sync_id`，并显示专属同步地址。
2. 学生把该地址粘贴到 Chrome 插件。
3. 插件使用当前已登录的 `canvas.sydney.edu.au` 会话，只读获取所选课程资料并上传快照。
4. 网站读取对应 `sync_id` 的快照，计算新增、修改和删除数量。
5. 学生主动点击生成后，才会把当前 Module 或 Assignment 的必要文本发送给 OpenAI。

`sync_id` 具有类似密码的作用。不得截图、公开分享或提交到 Git。网站的 SQLite 缓存按 `sync_id` 的匿名哈希隔离，不保存明文 token。

## Render 部署步骤

1. 将代码放入用户自己的私有 GitHub 仓库。
2. 登录 Render，选择 **New → Blueprint**，连接仓库根目录的 `render.yaml`。
3. Blueprint 首次创建时填写 `OPENAI_API_KEY`；不要把 Key 写进仓库。
4. 等两个服务健康检查通过。
5. 确认 Sync 服务最终域名。如果不是 `https://unisydneybuddy-sync.onrender.com`：
   - 把 Web 服务的 `CANVAS_SYNC_API_URL` 改成真实域名；
   - 在 `canvas_connector/manifest.json` 的 `host_permissions` 中加入该域名；
   - 重新加载插件。
6. 打开网站，复制私人同步地址，在插件中同步一门课程，回网站点击“检查最新同步”。
7. 用四门测试课程检查 Semester Overview、Weekly Brief、Assignment Analysis、中英切换和反馈提交。

## 成本与存储

当前 Blueprint 使用两个 `starter` Web Service，并各挂载 1 GB persistent disk，因为课程快照、AI 结果和反馈必须在重启或重新部署后保留。Render 的 persistent disk 只适用于付费服务；若希望零成本试用，需要把 SQLite 和快照存储改为外部数据库/对象存储，不能简单删除磁盘而仍宣称数据可持久保存。

## 发布前检查

- 插件权限仅覆盖 `canvas.sydney.edu.au` 和实际 Sync API 域名。
- `OPENAI_API_KEY` 只存在于 Render Secret 环境变量。
- 不读取 Canvas 密码、成绩、同学名单、提交内容或教师管理数据。
- 无正文的 Module 必须显示“资料未同步”，AI 不得补写。
- 所有缓存和同步基线按匿名用户命名空间隔离。
- 运行 `.venv/bin/pytest -q` 与 `python scripts/run_weekly_ai_evals.py`。
- 真实模型评测使用 `python scripts/run_weekly_ai_evals.py --live`，会产生 API 用量。

## 当前仍需用户授权的操作

公开部署会创建云服务、连接 GitHub 仓库并可能产生 Render 费用，因此必须由用户登录自己的 Render/GitHub 账号确认。代码与 Blueprint 已准备好，不会在未授权时替用户创建付费资源。
