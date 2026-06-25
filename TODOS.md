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

- [ ] **数据库：创建 license 表**
  - mr_licenses: code_hash, user_id, expiry, level, status
  - mr_user_feeds: user_id, feed_id（per-user RSS 源）
  - mr_user_rules: user_id, rule_id（per-user 评分规则）
  - Depends on: PostgreSQL 已部署

- [ ] **后端：授权码中间件**
  - 每个请求校验 X-License-Code header
  - 验证 JWT 签名 + 过期时间
  - 查询数据库检查 status（是否吊销）
  - 提取 user_id 注入请求上下文
  - 过期/无效返回 401 + 过期提示
  - Depends on: license 表创建

- [ ] **后端：授权码 API**
  - POST /api/license/validate — 验证授权码
  - POST /api/license/status — 查询授权码状态
  - POST /api/license/renew — 续订（管理员）
  - Depends on: 授权码中间件

- [ ] **后端：per-user 数据隔离**
  - 修改 feeds.fun 的 API，所有查询加 user_id 过滤
  - RSS 源：每个用户独立的订阅列表
  - 评分规则：每个用户独立的规则集
  - 新闻条目：全局共享（来自 RSSHub），但评分/标记 per-user
  - Depends on: 授权码中间件

- [ ] **前端：授权码输入页面**
  - 全屏页面，品牌 logo + 授权码输入框
  - 验证成功 → 存入 localStorage → 跳转主页
  - 验证失败 → 错误提示
  - Depends on: 授权码 API

- [ ] **前端：过期弹窗**
  - 每次 API 返回 401 → 弹窗提示过期
  - 引导续订（联系方式/购买链接）
  - 弹窗后锁定，不可操作
  - Depends on: 授权码中间件

- [ ] **前端：API 请求携带授权码**
  - 所有 fetch 请求 header 加 X-License-Code
  - 从 localStorage 读取
  - Depends on: 授权码输入页面

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
