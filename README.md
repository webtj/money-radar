# Money Radar — 通用信息资讯雷达

AI 自动打标签、评分、过滤的新闻阅读器。基于 [feeds.fun](https://github.com/Tiendil/feeds.fun) + [RSSHub](https://github.com/DIYgod/RSSHub)。

## 快速部署

### 1. 服务器准备

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Git
sudo apt install -y git
```

### 2. 克隆项目

```bash
git clone <your-fork-url> money-radar
cd money-radar
```

### 3. 一键安装

```bash
chmod +x setup.sh
./setup.sh
```

### 4. 配置环境变量

```bash
vim feeds.fun/.env
```

必须配置：
- `FFUN_POSTGRESQL__PASSWORD` — 数据库密码
- `FFUN_USER_SETTINGS_SECRET_KEY` — 随机密钥
- `FFUN_OPENAI_API_KEY` — DeepSeek API Key

获取 DeepSeek API Key: https://platform.deepseek.com

### 5. 启动服务

```bash
cd feeds.fun
docker compose --profile single-user up -d
```

### 6. 导入 RSS 源

```bash
# 先查看有哪些分类
python3 ../scripts/import_rsshub.py --list-categories

# 试运行（不实际导入）
python3 ../scripts/import_rsshub.py --dry-run

# 导入财经、科技、政策
python3 ../scripts/import_rsshub.py --categories finance,tech,policy
```

### 7. 访问

打开浏览器访问 `http://你的服务器IP`

## 项目结构

```
money-radar/
├── setup.sh                    # 一键安装脚本
├── .env.example                # 环境变量模板
├── docker-compose.override.yml # 添加 RSSHub
├── config/
│   └── tag_processors.toml     # 中文 LLM 标签配置
├── scripts/
│   └── import_rsshub.py        # RSSHub 批量导入脚本
├── DESIGN.md                   # 设计系统文档
├── CLAUDE.md                   # AI 辅助配置
└── TODOS.md                    # 任务清单
```

## 3 种主题

在设置中切换：
- **权威**（默认）— 白色背景，衬线标题，专业新闻风格
- **墨水屏** — 纯黑白，像报纸
- **养眼** — 暖色调，长时间阅读不累

## 技术栈

- **后端:** Python 3.13, FastAPI, PostgreSQL
- **前端:** Vue.js, Vite
- **AI:** DeepSeek API (OpenAI 兼容)
- **数据源:** RSSHub (5000+ 站点)
- **部署:** Docker Compose
