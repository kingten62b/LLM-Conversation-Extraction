# 客服对话结构化提取工具

基于 LangChain + FastAPI + Vue 的全栈客服对话提取系统。

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Vue 3 前端  │────▶│ FastAPI 后端  │────▶│ DeepSeek API │
│  localhost   │     │ localhost    │     │ (LangChain)  │
│  :5173       │◀────│ :8000        │◀────│              │
└─────────────┘     └──────────────┘     └──────────────┘
```

## 项目结构

```
0108/
├── backend/                          # FastAPI 后端
│   ├── main.py                       # API 入口（14 个端点）
│   ├── extractor.py                  # LangChain 提取链
│   ├── models.py                     # Pydantic 数据模型
│   ├── data.py                       # 数据加载/统计
│   └── .env                          # API 配置
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                   # 根组件
│   │   ├── main.js                   # 入口 + 路由
│   │   ├── api/index.js              # Axios API 客户端
│   │   ├── views/
│   │   │   ├── DashboardView.vue     # 仪表盘（统计图表）
│   │   │   ├── ConversationsView.vue # 对话列表 + 提取
│   │   │   ├── ResultsView.vue       # 提取结果展示
│   │   │   └── ValidationView.vue    # 人工验证界面
│   │   └── components/
│   │       └── NavBar.vue            # 导航栏
│   ├── vite.config.js                # Vite 配置（代理 /api）
│   ├── index.html
│   └── package.json
├── output/
│   └── extraction_results.json       # 提取结果
├── .env.example                      # API 配置模板
├── .gitignore
├── task.md
├── task2_conversations.json          # 25 条原始对话
└── task2_extract_example.md
```

## Schema 设计

| 字段 | 类型 | 说明 |
|------|------|------|
| `conversation_id` | str | 对话 ID |
| `channel` | str | 渠道：在线 / 电话 |
| `agent` | str | 客服姓名 |
| `turn_count` | int | 对话轮次 |
| `user_issue_summary` | str | 诉求摘要 |
| `issue_categories` | list[str] | 问题类别（支持多选） |
| `resolution_status` | str | 解决状态 |
| `resolution_action` | str | 处理措施 |
| `user_sentiment` | str | 用户情绪 |
| `urgency_level` | str | 紧急程度 |
| `requires_follow_up` | bool | 需跟进 |
| `escalation_required` | bool | 转人工 |

## 边界情况处理

| 场景 | 策略 |
|------|------|
| 多诉求（conv_06） | issue_categories 多标签 |
| 转人工（conv_09, conv_16） | escalation_required=true |
| 用户放弃（conv_12, conv_25） | resolution_status=unresolved |
| 部分解决（conv_20, conv_21） | resolution_status=partially_resolved |
| LLM 调用失败 | 规则兜底（keyword-based fallback） |

## 运行方式

```bash
# 1. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 2. 启动后端（Terminal 1）
conda activate 0108
cd backend && uvicorn main:app --reload --port 8000

# 3. 启动前端（Terminal 2）
cd frontend && npm install && npm run dev

# 浏览器打开 http://localhost:5173
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/conversations | 对话列表 |
| GET | /api/conversations/:id | 单条对话 |
| POST | /api/extract | 提取单条 |
| POST | /api/extract-all | 提取全部 |
| GET | /api/results | 提取结果 |
| GET | /api/results/:id | 单条结果 |
| GET | /api/stats | 统计概览 |
| POST | /api/validate | 人工验证 |
| GET | /api/validate/summary | 验证报告 |

## AI 工具使用

- **LangChain**（ChatOpenAI + JsonOutputParser）：结构化提取链
- **FastAPI**：REST API
- **Vue 3** + **Vite**：前端 SPA
- **DeepSeek API**：底层 LLM
