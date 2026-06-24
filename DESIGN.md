# Design System — Money Radar

## Product Context
- **What this is:** 通用信息资讯雷达，AI 自动打标签、评分、过滤
- **Who it's for:** 个人投资者 / 信息敏感型用户
- **Space/industry:** 信息过滤 + AI 标签 + RSS 聚合
- **Project type:** Web App（新闻阅读器 + AI 过滤）

## Aesthetic Direction
- **Direction:** Editorial/News — 报纸编辑部风格
- **Decoration level:** minimal — 排版承载所有信息，不靠装饰
- **Mood:** 严肃、可信、安静、不打扰。像一份精心编辑的每日简报。
- **Reference:** Reuters, Financial Times, Wall Street Journal, 新华社

## Memorable Thing
用户第一次看到产品时记住：**信息有价值、密度高、一目了然、干净、不废话、不打扰。**

## Typography
- **Display/Hero:** Noto Serif SC（思源宋体）— 衬线字体传达严肃、可信
- **Body:** Noto Sans SC（思源黑体）— 无衬线正文，清晰可读
- **UI/Labels:** Noto Sans SC（同 body）
- **Data/Tables:** Geist Mono — 等宽数字，评分/统计数据
- **Code:** Geist Mono
- **Loading:** Google Fonts CDN
- **Scale:** 12px / 13px / 14px / 16px / 20px / 24px / 32px

## Color — 3 Themes

### 权威主题（默认）
```css
--bg-primary: #ffffff;
--bg-secondary: #fafafa;
--bg-tertiary: #f5f5f5;
--text-primary: #1a1a1a;
--text-secondary: #4a4a4a;
--text-tertiary: #8a8a8a;
--accent: #c41e3a;        /* 红色点缀，极克制使用 */
--border: #e0e0e0;
--border-heavy: #1a1a1a;
```

### 墨水屏主题
```css
--bg-primary: #ffffff;
--bg-secondary: #ffffff;
--bg-tertiary: #f5f5f5;
--text-primary: #000000;
--text-secondary: #000000;
--text-tertiary: #555555;
--accent: #000000;
--border: #000000;
--border-heavy: #000000;
```

### 养眼主题
```css
--bg-primary: #f8f6f1;
--bg-secondary: #f3f0e8;
--bg-tertiary: #ebe8df;
--text-primary: #3d3529;
--text-secondary: #5a5044;
--text-tertiary: #8a8070;
--accent: #8b6914;        /* 暖金色 */
--border: #d9d3c7;
--border-heavy: #3d3529;
```

## Spacing
- **Base unit:** 4px
- **Density:** compact — 信息密度高
- **Scale:** 4px / 8px / 12px / 16px / 24px / 32px / 48px

## Layout
- **Approach:** grid-disciplined — 严格对齐，可预测
- **Grid:** 2栏（侧边栏 200px + 主内容区）
- **Max content width:** 1200px
- **Border radius:** 0 — 无圆角，用线条分隔

## Motion
- **Approach:** minimal-functional — 只有理解状态变化需要的动画
- **Easing:** ease-out
- **Duration:** micro(50ms) / short(100ms)

## Design Rules

### 标题
- 用衬线字体（Noto Serif SC）
- 传达严肃、可信
- 首条新闻标题 22px，其他 16px

### 标签
- 用 `#标签名` 格式，灰色文字
- 不用彩色色块
- 不用边框

### 评分
- 等宽数字（Geist Mono）
- 左侧对齐
- 首条 24px，其他 16px

### 分隔
- 用线条分隔，不用圆角卡片
- 首条新闻用 2px 粗线分隔（头条感）
- 其他用 1px 细线

### 品牌色
- 仅用于：Logo 的 "Radar" 部分、过期提醒、链接 hover
- 不用于：按钮、标签、背景
- 极克制使用

### 授权码页面
- 全屏居中
- 衬线 Logo
- 等宽输入框
- 下粗边框聚焦态

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-24 | 初始设计系统 | 基于权威新闻平台设计语言 |
| 2026-06-24 | 3种主题 | 墨水屏/养眼/权威，CSS 变量切换 |
| 2026-06-24 | 衬线标题 | 参考 FT/WSJ/新华社，传达严肃可信 |
| 2026-06-24 | 无圆角卡片 | 用线条分隔，信息密度更高 |
| 2026-06-24 | 标签用文字不用色块 | 参考知乎/HN，扫描更快 |
