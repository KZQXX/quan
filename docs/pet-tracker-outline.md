# 宠物行为分析 · 云端 SaaS · 开发大纲（MVP v1）

> 资深开发工程师（Senior Developer）主持 · 团队技术提升 + 方案落地
> 更新日期：2026-07-10

## 0. 产品定位（已与需求方确认）

| 维度 | 决策 |
|---|---|
| 形态 | 云端多用户 SaaS，浏览器访问 |
| 后端内核 | **Python + FastAPI**（异步 / 类型安全 / 易测试） |
| 前端 | **Vue 3 + Vite + TypeScript + Tailwind CSS**（独立前端，追求 premium 体验） |
| 宠物语音识别 | **本期不做**，预留接口，v2 迭代 |
| 行为分析 | **手动打卡 + 定时提醒**（v1）；CV 自动识别留 v2+ |
| 核心功能 | 进食次数记录、排便记录、行为记录、可视化、提醒 |

> 说明：内核 Python 决定了后端不走 Laravel；但前端仍可做出玻璃拟态、磁吸交互等高端质感（我的专长领域），做到"基础功能 + 奢华体验"。

---

## 1. 技术栈（落地版）

### 后端
- **FastAPI + Pydantic v2**：接口契约 + 数据校验
- **SQLAlchemy 2.0 (async) + PostgreSQL**（生产）/ SQLite（本地开发）
- **Alembic**：数据库迁移
- **定时任务**：APScheduler（轻量）或 Celery+Redis（规模化）
- **认证**：JWT（python-jose + passlib）或 authlib（OAuth）
- **存储**：对象存储（宠物头像/照片，可选）
- **测试**：pytest + httpx + pytest-asyncio
- **质量门禁**：ruff（lint）、black、mypy、pre-commit、GitHub Actions CI

### 前端（已确认选型：Vue 3）
- **Vue 3 + Vite + TypeScript + Tailwind CSS**
- 路由：Vue Router
- 状态管理：Pinia
- 图表：ECharts（喂食/排便趋势，与 Vue 生态契合度高）
- 主题：CSS 变量 + `@vueuse/core` 的 `useDark`，实现浅色 / 深色 / 跟随系统三态切换
- 组件：自建 premium 组件库（玻璃拟态 + 磁吸 hover + 平滑主题切换）

### AI/ML（v2 预留接口，本期仅留扩展点）
- 音频：librosa + 自训练分类器 / Whisper（主人指令）
- CV：OpenCV + YOLO（行为识别）
- 框架：PyTorch

### DevOps
- Docker + docker-compose（本地一键起）
- 可选：GitHub Actions → 云服务器 / 容器平台

---

## 2. 数据模型（核心实体）

- `User`：账号、订阅状态
- `Pet`：宠物档案（名字 / 物种 / 品种 / 生日 / 头像）
- `FeedingRecord`：喂食记录（时间 / 食量 / 食物类型 / 来源：自动或手动）
- `ExcretionRecord`：排便记录（时间 / 类型 / 性状 / 备注）
- `BehaviorRecord`：行为记录（类型 / 时长 / 情绪 / 备注）
- `Reminder`：定时提醒（喂食 / 梳洗 / 用药）
- `DailyStats`：每日聚合统计（预计算提速）
- （v2）`VoiceClip` / `BehaviorVideo`

---

## 3. 功能模块（MVP 范围）

1. **账号体系**：注册 / 登录 / 登出 / 改密
2. **宠物管理**：增删改查、多宠物切换
3. **记录中心**：进食次数、排便、行为（表单 + 快速打卡）
4. **定时提醒**：可配置提醒，到点通知（站内 / 邮件 / Webhook）
5. **仪表盘 / 可视化**：今日概览、趋势图、周报
6. **统计报表**：按宠物 / 时间段聚合
7. **设置**：主题切换（浅色 / 深色 / 跟随系统——**必做**）、单位、通知偏好

---

## 4. 逐日开发计划（M1–M5 共 33 天，约 6.5 周）

> 团队分工模式：Senior（我）负责关键模块 authoring + 全部 PR review，团队成员在带教下完成剩余模块。

---

### M1 · 脚手架（Day 1–5 | 第 1 周）

| 天 | 模块 | 内容 |
|---|---|---|
| **D1** | 后端骨架 | FastAPI 应用入口、pydantic-settings 配置管理、结构化日志(loguru)、全局异常处理中间件、Python 虚拟环境搭建 |
| **D2** | 数据库基座 | SQLAlchemy 2.0 async engine、Base 模型基类、Alembic 初始化 + 首条迁移、SQLite 本地开发 / PostgreSQL 生产双配置 |
| **D3** | 质量门禁 | ruff / black / mypy 配置、pre-commit hooks、pytest + pytest-asyncio 骨架、GitHub Actions CI 模板（lint + test） |
| **D4** | 前端骨架 | Vite + Vue 3 + TS + Tailwind CSS 初始化、Vue Router 基础路由、Pinia store 骨架、Axios 封装（baseURL + 拦截器） |
| **D5** | 全栈联通 | Docker + docker-compose 编排（backend + frontend + db）、前端代理→后端、`/api/health` 端点跑通、前后端联调验证 |

---

### M2 · 账号 + 宠物管理（Day 6–10 | 第 2 周）

| 天 | 模块 | 内容 |
|---|---|---|
| **D6** | 注册 | User 模型（密码 bcrypt 哈希）、`POST /api/auth/register`、Pydantic 请求/响应 schema、单元测试 |
| **D7** | 认证 | `POST /api/auth/login`（JWT 签发）、认证依赖注入中间件、登出、改密 API、认证流程集成测试 |
| **D8** | 宠物 CRUD | Pet 模型、增删改查 API、按用户隔离、多宠物列表、pytest 全覆盖 |
| **D9** | 前端登录 | 登录/注册页面 UI、Pinia auth store（token + user 持久化）、路由守卫（未登录→登录页）、Axios 拦截器自动携带 token |
| **D10** | 前端宠物 | 宠物列表页、添加/编辑表单、多宠物切换器、删除确认弹窗、前后端全链路联调 |

---

### M3 · 三大记录 + 快速打卡（Day 11–18 | 第 3 周 + 第 4 周前半）

| 天 | 模块 | 内容 |
|---|---|---|
| **D11** | 喂食后端 | FeedingRecord 模型（food_type 枚举、amount、time）、CRUD API、按宠物/日期范围筛选、测试 |
| **D12** | 排便后端 | ExcretionRecord 模型（type 枚举、consistency、notes）、CRUD API、筛选查询、测试 |
| **D13** | 行为后端 | BehaviorRecord 模型（behavior_type 枚举、duration、mood）、CRUD API、测试 |
| **D14** | 记录中心框架 | 记录中心主页面（Tab 切换：喂食/排便/行为）、通用记录列表组件、日期筛选器、宠物筛选器 |
| **D15** | 喂食打卡 | 喂食记录表单（食物类型下拉、食量输入）、「快速打卡」按钮（一键记录）、今日喂食列表 |
| **D16** | 排便+行为打卡 | 排便记录表单、行为记录表单（类型+时长+情绪）、快速打卡组件复用、三模块全联调 |
| **D17** | 打卡体验 | 卡片式记录展示、快捷操作（编辑/删除/复制）、表单验证与错误提示、空状态引导插画 |
| **D18** | 集成测试 | 记录中心端到端流程测试、边界条件测试、Swagger UI 接口文档、本周 code review |

---

### M4 · 提醒 + 仪表盘可视化（Day 19–26 | 第 4 周后半 + 第 5 周）

| 天 | 模块 | 内容 |
|---|---|---|
| **D19** | 提醒后端 | Reminder 模型（类型、时间、重复规则 cron）、CRUD API、APScheduler 定时任务引擎 |
| **D20** | 通知服务 | 站内通知模型 + API、邮件通知（SMTP）、Webhook 推送、通知偏好设置 |
| **D21** | 前端提醒 | 提醒列表页、创建/编辑表单、时间选择器、重复规则配置 UI（每天/每周/自定义） |
| **D22** | 每日统计 | DailyStats 聚合模型、定时聚合脚本（凌晨计算昨日数据）、统计查询 API（按宠物/时间段） |
| **D23** | 仪表盘 | 仪表盘主页布局、今日概览卡片（喂食次数/排便次数/行为条数/提醒数）、快速打卡入口 |
| **D24** | 趋势图表 | ECharts 折线图（7/30 天喂食&排便趋势）、排便类型饼图、行为统计柱状图 |
| **D25** | 统计报表 | 按宠物+时间段聚合报表页、数据导出 CSV、周报自动生成组件 |
| **D26** | 联调+评审 | 提醒触发→通知全链路验证、仪表盘数据准确性校验、响应式适配、本周 code review |

---

### M5 · 打磨（Day 27–32 | 第 6 周 + 第 7 周前半）

| 天 | 模块 | 内容 |
|---|---|---|
| **D27** | 主题系统 | CSS 变量完整体系（颜色/阴影/圆角/间距）、浅色/深色/跟随系统三态切换、`useDark` 集成、0.3s 过渡动画 |
| **D28** | 视觉组件库 | 玻璃拟态卡片、按钮、输入框、弹窗、磁吸 hover（`transform: scale(1.02)`）、统一动效规范文档 |
| **D29** | 前端性能 | 路由懒加载、组件异步加载、图片懒加载、虚拟列表（记录超 100 条时）、Lighthouse 评分 ≥90 |
| **D30** | 后端性能 | 数据库索引优化、N+1 查询治理、Redis 缓存热点数据、API 响应时间 P95 < 200ms |
| **D31** | 测试冲刺 | 补齐遗漏单元测试与集成测试、覆盖率报告生成、目标 ≥70%、修复测试中发现的 bug |
| **D32** | 收尾交付 | 移动端/平板/桌面三端响应式适配、docker-compose 一键启动验证、README + 部署文档 |

---

### D33 · 缓冲日

> 应对不可预见的技术问题、额外优化、最终走查验收。

---

### v2 预留（Day 34–35 | 第 7 周后半）

| 天 | 内容 |
|---|---|
| **D34** | VoiceClip 数据模型 + 文件上传 API + Whisper 集成占位 |
| **D35** | BehaviorVideo 模型 + 对象存储接口 + YOLO 分析任务队列骨架 |

---

## 5. 团队技能矩阵 & 提技路径

| 技能 | 团队现状（待填） | 目标 | 提技方式 |
|---|---|---|---|
| Python 异步 / FastAPI | 待评估 | 能独立写生产级接口 | 我带做 1 个模块 + PR 评审 |
| 类型注解 / mypy | 待评估 | 强制开启，PR 必过 | 配置门禁 + 范例 |
| 数据库建模 / 迁移 | 待评估 | 规范建模 + Alembic | 我出建模规范文档 |
| 测试文化（pytest） | 待评估 | 覆盖率 ≥70% | 我写测试模板，团队补用例 |
| 前端 premium 体验 | 待评估 | 玻璃拟态 / 动效规范 | 我提供组件库与动效指南 |
| CI/CD | 待评估 | 提交即跑质量门禁 | 我搭好，团队只需遵守 |
| 代码评审 | 待评估 | checklist 驱动 | 我定清单，逐 PR 带教 |

---

## 6. 代码质量把控机制（落地关键）

- **pre-commit 强制**：ruff / black / mypy
- **PR 模板 + 评审 checklist**：性能 / 安全 / 可测性 / 可读性
- **覆盖率门禁**：≥70% 才能合入 `main`
- **角色分工**：我（Senior）做「关键模块 author + 所有 PR reviewer」
- **每周 1 次 code review 直播/录屏**，沉淀团队规范文档

---

## 7. 下一步待确认 / 行动项

- [x] 确认前端技术选型：**Vue 3**（已定，详见第 1 节）
- [ ] 评估团队各技能现状（填第 5 节表格）
- [ ] 由我直接帮你在 `D:\github\P2` 起一套可运行的 MVP 脚手架
      （FastAPI + 前端雏形 + CI + 主题切换），边写边带团队
- [ ] 建立团队规范文档与评审 checklist
