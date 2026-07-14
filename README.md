# Pet Tracker (quan)

宠物行为分析 SaaS — 记录宠物日常进食、排便、行为，提供可视化统计分析和定时提醒。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.13 + FastAPI + SQLAlchemy 2.0 async + Alembic + SQLite/PostgreSQL |
| 前端 | Vue 3 + Vite + TypeScript + Tailwind CSS + ECharts + Pinia |
| 认证 | bcrypt + python-jose JWT (Bearer Token) |
| 调度 | APScheduler (AsyncIOScheduler) |
| 质量 | ruff + mypy + pytest (70% coverage) |
| DevOps | Docker multi-stage + docker-compose + nginx |

## 功能

- **账号体系**：注册/登录/改密/JWT 鉴权
- **宠物管理**：多宠物 CRUD，按用户隔离
- **记录中心**：喂食/排便/行为三类记录 + 快速打卡 + 日期筛选 + 编辑/删除/复制
- **定时提醒**：可配置提醒（每天/每周/自定义 cron），站内通知
- **仪表盘**：全量统计卡片 + 今日数据概览
- **可视化**：ECharts 7/30 天趋势折线图 + 排便饼图 + 行为柱状图
- **统计报表**：按宠物+时间段聚合 + CSV 导出
- **三态主题**：浅色/深色/跟随系统，localStorage 持久化

## 快速开始

### 本地开发

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8080

# 前端
cd frontend
npm install
npm run dev                    # http://localhost:5173 (proxy /api -> 8080)
```

### Docker

```bash
docker-compose up --build
# 前端: http://localhost:80
# 后端: http://localhost:8080
```

## 质量验证

```bash
# 后端
cd backend
ruff check app/
mypy app/
pytest -v --cov=app --cov-report=term   # 目标 ≥ 70%

# 前端
cd frontend
npm run build                            # vue-tsc + vite build
```

## 环境变量

参考 `backend/.env.example`：

```env
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./pet_tracker.db
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET  | `/api/auth/me` | 当前用户 |
| PATCH| `/api/auth/password` | 改密 |
| PATCH| `/api/auth/preferences` | 通知偏好 |
| CRUD | `/api/pets` | 宠物管理 |
| CRUD | `/api/pets/{id}/feedings` | 喂食记录 |
| CRUD | `/api/pets/{id}/excretions` | 排便记录 |
| CRUD | `/api/pets/{id}/behaviors` | 行为记录 |
| CRUD | `/api/reminders` | 提醒管理 |
| GET  | `/api/notifications` | 通知列表 |
| GET  | `/api/dashboard` | 仪表盘数据 |
| GET  | `/api/stats/daily` | 每日统计 |
| GET  | `/api/stats/report` | 聚合报表 |
| GET  | `/api/stats/export` | CSV 导出 |
| GET  | `/api/health` | 健康检查 |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api.py              # 所有 REST 端点
│   │   ├── main.py             # FastAPI 入口
│   │   ├── schemas.py          # Pydantic 模型
│   │   ├── core/               # 配置/安全/日志/调度器
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── services/           # 业务服务层
│   │   └── shared/             # 数据库/基础模型
│   ├── migrations/             # Alembic 迁移
│   └── tests/                  # pytest 集成测试
├── frontend/
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── components/         # 通用组件
│   │   ├── composables/        # API 封装
│   │   ├── stores/             # Pinia 状态
│   │   └── assets/css/         # 主题样式
│   └── ...
└── docker-compose.yml
```
