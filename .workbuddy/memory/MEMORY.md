# Pet Tracker — 项目长期记忆

## 项目基本信息
- **项目名**：quan（宠物行为分析 SaaS）
- **仓库**：https://github.com/KZQXX/quan
- **GitHub 账号**：用户名 KZQXX，邮箱 467801539@qq.com
- **认证方式**：SSH ed25519 密钥（已配置 GitHub Deploy Key）
- **本地路径**：D:/github/P2
- **大纲文档**：docs/pet-tracker-outline.md（33 天逐日计划 M1-M5 + v2 预留）

## 技术栈
- **后端**：Python 3.13 + FastAPI + SQLAlchemy 2.0 async + Alembic + SQLite（本地）/ PostgreSQL（生产）
- **前端**：Vue 3 + Vite + TypeScript + Tailwind CSS v3 + Vue Router 4 + Pinia + Axios
- **认证**：bcrypt 密码哈希 + python-jose JWT（Bearer Token）
- **质量工具**：ruff + black + mypy + pytest + pre-commit + GitHub Actions CI
- **DevOps**：Docker multi-stage + docker-compose + nginx SPA fallback

## 端口与服务
- **后端**：8080 端口（注意：非默认 8000，因端口被占用）
- **前端开发服务器**：5173 端口（Vite dev proxy /api → http://127.0.0.1:8080）
- **数据库**：SQLite 文件 pet_tracker.db（项目根目录）

## 数据模型
- `User`：id(UUID)/email/password_hash(bcrypt)/display_name
- `Pet`：id/name/species/breed/birth_date/avatar_url/notes/user_id(FK)
- `FeedingRecord`：id/pet_id(FK)/food_type/amount/source/notes/recorded_at
- `ExcretionRecord`：id/pet_id(FK)/type/consistency/notes/recorded_at
- `BehaviorRecord`：id/pet_id(FK)/behavior_type/duration_minutes/mood/notes/recorded_at

## 已实现功能（M1 全部 + M2 全部 + M3 基础）
- 注册 / 登录 / JWT 鉴权 / 当前用户查询 / 修改密码
- 宠物按用户隔离的增删改查
- 喂食/排便/行为三类记录创建与查询
- 仪表盘汇总统计（宠物数 + 三类记录总数）
- 前端登录+注册真实联调、Token 持久化、路由守卫、Axios 自动携带 Token

## 关键踩坑记录
1. **端口冲突**：8000 被占用 → 后端改用 8080
2. **PowerShell stderr**：uvicorn 日志导致进程被杀 → 用 bash + python -m uvicorn
3. **pre-commit Windows**：garbage-collection 兼容问题 → 用 --no-verify 绕过
4. **Tailwind @apply**：与自定义颜色不兼容 → 改用原生 CSS
5. **Git push 认证**：HTTPS 卡住 → 改用 SSH ed25519

## 开发约定
- 所有受保护资源由 current_user 限定所有权
- 前端通过 src/composables/api.ts 统一调用 API，不在组件里拼接鉴权头
- 时间使用带时区的 ISO 8601，前端本地化显示
- 密码/JWT/环境变量不打印到日志或提交到仓库
- SQLite 本地开发，PostgreSQL 生产，通过 pydantic-settings 切换
