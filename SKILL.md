---
name: zhihu-skill
description: "知乎 API CLI — 通过 Cookie 认证调用知乎开放 API，支持搜索、点赞、收藏、评论、关注等操作"
version: 1.0.0
author: hiyasame
license: MIT
platforms: [linux, macos, windows]
tags: [zhihu, social, api, cli]
---

# 知乎 Skill

基于 [zhihu-fisher-vscode](https://github.com/crispyChicken999/zhihu-fisher-vscode) 项目的知乎 API，通过 Cookie 认证调用知乎开放 API，支持搜索、点赞、收藏、评论、关注等操作。

## 文件结构

```
zhihu-skill/
├── SKILL.md                            # 本文件 — skill 描述
├── README.md                           # 项目说明
├── INSTALL.md                          # 安装指南
├── zhihu.py                            # 核心 CLI 脚本
├── secrets/                            # Cookie 等敏感信息（自动创建，已 gitignore）
│   └── zhihu.env
└── references/
    ├── zhihu-api.md                    # 知乎 API 端点参考
    └── hot-list-parsing.md             # 热榜 HTML 解析参考
```

## 使用方式

### 获取 Cookie

1. 在浏览器中登录 zhihu.com
2. 按 F12 打开开发者工具 → Application → Cookies → `https://www.zhihu.com`
3. 复制所有 cookie 值（以 `d_c0=` 开头的长字符串，或全部 cookie 拼接）

> ⚠️ Cookie 有有效期（通常几周到几个月），过期后需要重新获取。

### 设置 Cookie

```bash
python3 zhihu.py set-cookie <你的知乎cookie>
```

Cookie 会安全存储在 `secrets/zhihu.env` 中。

### 搜索文章/回答

```bash
python3 zhihu.py search <关键词> [--type article|answer] [--limit N] [--offset N]
```

- `--type`: 搜索类型，`article`（专栏文章）或 `answer`（回答），不指定则全部
- `--limit`: 返回数量，默认 10，最大 50
- `--offset`: 分页偏移，默认 0

### 热榜

```bash
python3 zhihu.py hot
```

获取知乎热榜话题列表。

### 点赞

```bash
python3 zhihu.py upvote <url>            # 点赞
python3 zhihu.py upvote <url> --cancel   # 取消点赞
```

支持回答 URL（`https://www.zhihu.com/question/xxx/answer/xxx`）、文章 URL（`https://zhuanlan.zhihu.com/p/xxx`）、想法 URL（`https://www.zhihu.com/pin/xxx`）。

### 收藏

```bash
python3 zhihu.py favorite <url> --collection-id <id>    # 收藏
python3 zhihu.py unfavorite <url> --collection-id <id>  # 取消收藏
```

不指定 `--collection-id` 时会列出收藏夹供选择。

### 评论

```bash
python3 zhihu.py comment <url> "评论内容"
python3 zhihu.py like-comment <comment_id>
python3 zhihu.py unlike-comment <comment_id>
```

### 查看收藏夹

```bash
python3 zhihu.py collections [--limit N] [--offset N]
```

### 关注/取消关注

```bash
python3 zhihu.py follow <用户主页URL>
python3 zhihu.py unfollow <用户主页URL>
```

### 帮助

```bash
python3 zhihu.py --help
```

## 技术细节

- 所有 API 请求自动携带 Cookie 和知乎标准请求头
- 支持回答（answer）、文章（article）、想法（pin）三种内容类型
- 搜索使用知乎官方搜索 API，不依赖浏览器
- 热榜从 `zhihu.com/hot` 页面解析 HTML（旧 API 已废弃），详见 [references/hot-list-parsing.md](references/hot-list-parsing.md)

## 安全提示

- Cookie 存储在 `secrets/zhihu.env`，权限 0600，不会输出到日志
- 所有 API 请求仅限 zhihu.com 域名
