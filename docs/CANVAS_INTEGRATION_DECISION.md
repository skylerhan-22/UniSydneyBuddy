# UniSydneyBuddy Canvas 接入调研与阶段决策

- 决策日期：2026-08-16
- 适用版本：公开部署候选版 v0.2
- 当前结论：**浏览器 Connector 是当前正式接入路径。现阶段不申请悉尼大学 Canvas Developer Key，也不把 OAuth 作为路线图前置项。公开网站通过私人同步地址接收每位用户的只读快照。**

## 1. 已确认的事实

### 悉尼大学侧

- 学生通过 UniKey 与密码登录学校 Canvas；课程通常在开学前一周出现在 Dashboard。悉尼大学公开帮助页没有提供面向学生或独立开发者的 API 注册、自助 Developer Key 或第三方 OAuth 申请入口。
- 因此，目前只能确认学校在使用 Canvas，**不能确认悉尼大学已允许本项目注册 OAuth 应用**。

来源：[University of Sydney — Accessing Canvas](https://www.sydney.edu.au/students/canvas/accessing-canvas.html)

### Canvas 平台侧

- Canvas 支持 OAuth 2.0，网页应用可把用户跳转至学校 Canvas 授权，取得 authorization code 后换取 access token；应用不需要、也不应该收集 Canvas 密码。
- 多用户应用必须使用 OAuth。Canvas 官方明确指出，让其他用户手工生成 token 并填入应用违反其 API Policy。
- OAuth 所需的 client ID 与 client secret 来自该机构 Canvas 管理员签发的 Developer Key；它不是学生个人可以假定获得的公共密钥。
- 获得授权后，官方只读 API 能覆盖本产品需要的核心来源：Courses、Modules / Module Items、Pages、Assignments 和 Announcements。返回结果仍受当前学生本人权限、发布时间与解锁条件约束。

来源：[Canvas OAuth2 Overview](https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth)、[Modules API](https://developerdocs.instructure.com/services/canvas/resources/modules)、[Assignments API](https://developerdocs.instructure.com/services/canvas/resources/assignments)、[Announcements API](https://developerdocs.instructure.com/services/canvas/resources/announcements)

## 2. 三种方案判断

| 方案 | 现在能否可靠落地 | 主要问题 | 决策 |
|---|---|---|---|
| Canvas OAuth + REST API | 取决于悉大管理员签发 Developer Key | 尚无学校批准或注册入口证据 | **当前不实施，也不影响发布** |
| 浏览器插件读取已登录 Canvas | 已实现本地与公开同步地址 | 需要安装扩展，正式分发仍需安全与隐私审核 | **当前产品主路径** |
| 模拟同步 + 手动粘贴/多文件上传 | 当前即可 | 不是自动实时同步 | **无 Canvas 环境下的备用演示** |

## 3. 下一阶段交付范围

### Phase 3 — 只读 Canvas Connector

- Chrome Connector 使用当前已登录 Canvas 会话调用同源只读 REST API。
- 用户选择课程后读取 Courses、Modules、Pages、Assignments 与 Announcements。
- Connector 不读取或保存 Canvas 密码、session cookie 值、成绩、提交或其他学生资料。
- 本地开发时快照发送到 localhost Bridge；公开版发送到网站生成的私人 `sync_id` 地址。
- 保留“粘贴 Canvas 文字 + 多文件 / 截图上传”和脱敏 Demo 数据作为备用。

### Phase 4 — 同步数据模型与增量更新

- 建立统一对象：Course、Module、Learning Item、Session、Assessment、Announcement、Source Snapshot。
- 每条内容保留 `source_id`、`source_url`、`available_at`、`updated_at`（若 API 提供）、内容哈希和 `last_seen_at`。
- 首次同步读取全部当前可见内容；后续按 API 更新时间与本地内容哈希比对，只更新新增或变化项。
- `Canvas 状态` 与 `Demo 导入状态` 分开显示，避免把“未导入”误写成“Canvas 未发布”。

### Phase 5 — 当前不进入范围

- 不申请 Developer Key，不实现 Canvas OAuth。
- 只有在学校未来提供明确渠道且插件方案无法满足产品需求时，才重新评估。

## 4. 推荐的只读范围

最小候选范围：

- 当前用户可见课程列表
- 指定课程 Modules 与 Module Items
- Module 中指向的 Pages / Files 元数据
- Assignments、due date、submission type、rubric（在学生权限允许时）
- Announcements

暂不接入：成绩、提交内容、同学名单、Discussion 发帖、消息、写入或提交接口。

## 5. 发布前仍需确认的问题

1. 课程材料在第三方工具中的缓存、摘要和模型处理有哪些版权或数据驻留要求？
2. 浏览器插件公开分发是否需要学校安全或品牌审批？
3. Lecture Recording 是否通过 Canvas API 直接可取，还是属于 Echo360 等独立系统？

产品文案必须明确：`Canvas Connector connected` 只表示学生主动安装的浏览器插件完成只读同步，不代表悉尼大学官方授权、背书或 OAuth 集成。
