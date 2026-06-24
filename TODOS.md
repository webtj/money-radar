# TODOS

## High Priority (Sprint 1)

- [ ] **Fork feeds.fun + 部署**
  - Fork https://github.com/Tiendil/feeds.fun
  - Docker Compose 一键部署：PostgreSQL + Backend + Frontend + RSSHub
  - 验证基本功能可用
  - Depends on: 无

- [ ] **修改 LLM prompt 支持中文标签**
  - 修改 `tag_processors.toml` 里的 system prompt
  - 要求用中文输出标签（替代默认的英文标签规则）
  - 测试中文标签质量
  - Depends on: feeds.fun fork 完成

- [ ] **RSSHub 自动导入脚本**
  - 脚本从 RSSHub API 获取路由列表
  - 过滤用户关注的领域（金融、科技、政策等）
  - 批量调用 feeds.fun API 添加 feed
  - Depends on: feeds.fun + RSSHub 部署完成

## High Priority (Sprint 2) — 授权码系统

- [ ] **授权码生成工具**
  - 生成 JWT 格式的授权码
  - Payload 包含: user_id, expiry_date, permission_level
  - 用 HMAC-SHA256 签名
  - 提供 CLI 工具生成授权码
  - Depends on: feeds.fun fork 完成

- [ ] **后端授权码校验 API**
  - 新增 `/api/license/validate` 端点
  - 新增授权码校验中间件（拦截所有请求）
  - 检查签名、过期时间、黑名单
  - 存储授权码到 PostgreSQL（支持吊销）
  - Depends on: feeds.fun fork 完成

- [ ] **前端授权码页面**
  - 首次访问弹出授权码输入页面
  - 授权码存入 localStorage
  - 过期前提醒续订
  - 过期后锁定，无法使用
  - Depends on: 后端校验 API 完成

## Medium Priority (Sprint 3)

- [ ] **运行 /design-consultation 建立设计系统**
  - 定义主色调、字体家族、间距系统、圆角系统、阴影系统
  - 生成 DESIGN.md
  - Depends on: 无

- [ ] **中文 UI 适配**
  - 修改 Vue 前端的文案为中文
  - 日期格式、数字格式本地化
  - Depends on: feeds.fun fork 完成

- [ ] **LLM workers 优化**
  - 把 tag_processors.toml 的 workers 从 1 改到 3-5
  - 验证并发处理效果
  - Depends on: 部署完成

- [ ] **Spike 周评估**
  - 接入 3-5 个信息源（财经、科技、政策）
  - 体验一周 AI 打标签效果
  - 记录：哪些标签准确？哪些不准确？每天推荐质量如何？
  - 用 100 条新闻做测试集，人工标注后对比 precision
  - Depends on: 部署 + 中文 prompt 修改完成

## Low Priority (Backlog)

- [ ] **多用户认证系统** (v2)
  - 接入 OAuth 或邮箱注册
  - Depends on: v1 自用验证通过

- [ ] **监控告警**
  - RSSHub 健康检查
  - feeds.fun Worker 心跳
  - Telegram/微信通知
  - Depends on: spike 周后按需

- [ ] **自定义前端** (如需要)
  - 如果 feeds.fun 原版 UI 不满足需求
  - Depends on: spike 周体验结果
