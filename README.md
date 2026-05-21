# 知乎 CLI — Zhihu CLI

基于 Cookie 认证的知乎 API 命令行工具，支持搜索、热榜、内容查看、互动等操作。

> 本项目参考了 [crispyChicken999/zhihu-fisher-vscode](https://github.com/crispyChicken999/zhihu-fisher-vscode) 的知乎 API 研究，感谢原作者的贡献 🙏

## 功能一览

### 🔍 搜索
- 搜索知乎回答（answer）和专栏文章（article）
- 支持分页，最多一次返回 50 条
- 自动过滤广告、推广等无关内容

### 📖 查看内容
- 查看回答、专栏文章的完整内容
- 自动提取标题和作者信息

### 🔥 热榜
- 获取知乎实时热榜话题列表

### 👍 点赞 / 取消点赞
- 支持回答（`/question/xxx/answer/yyy`）
- 支持专栏文章（`/p/xxx`）
- 支持想法（`/pin/xxx`）

### 📁 收藏 / 取消收藏
- 收藏回答和文章到指定收藏夹
- 查看已有的收藏夹列表

### 💬 评论
- 在回答、文章、想法下发表评论
- 点赞 / 取消点赞评论

### 👤 关注 / 取消关注
- 关注或取关知乎用户

## 快速开始

### 1. 获取 Cookie

登录 [zhihu.com](https://www.zhihu.com)，打开浏览器开发者工具：

- **Chrome/Edge**: F12 → Application → Cookies → `https://www.zhihu.com`
- **Firefox**: F12 → Storage → Cookies

复制所有 cookie 值（通常以 `d_c0=` 开头的一段长字符串）。

> ⚠️ Cookie 有有效期（通常几周到几个月），过期后需要重新获取。

### 2. 设置 Cookie

```bash
python3 zhihu.py set-cookie "你的知乎cookie"
```

Cookie 会安全存储在本地的 `secrets/zhihu.env` 文件中，权限 600。

### 3. 开始使用

```bash
# 查看回答内容
python3 zhihu.py view https://www.zhihu.com/question/xxx/answer/xxx

# 搜索
python3 zhihu.py search "大模型" --type article --limit 5

# 热榜
python3 zhihu.py hot

# 点赞
python3 zhihu.py upvote https://www.zhihu.com/question/xxx/answer/xxx

# 评论
python3 zhihu.py comment https://www.zhihu.com/question/xxx/answer/xxx "写得好！"

# 收藏
python3 zhihu.py favorite https://zhuanlan.zhihu.com/p/xxx --collection-id 12345

# 关注用户
python3 zhihu.py follow https://www.zhihu.com/people/xxx
```

## 命令参考

| 命令 | 说明 | 选项 |
|------|------|------|
| `view` | 查看回答/文章内容 | — |
| `search` | 搜索内容 | `--type article\|answer`, `--limit N`, `--offset N` |
| `hot` | 查看热榜 | — |
| `upvote` | 点赞 | `--cancel` 取消点赞 |
| `favorite` | 收藏 | `--collection-id ID` |
| `unfavorite` | 取消收藏 | `--collection-id ID` |
| `comment` | 发表评论 | — |
| `like-comment` | 点赞评论 | `--cancel` 取消点赞 |
| `follow` | 关注用户 | `--cancel` 取消关注 |
| `collections` | 查看收藏夹 | `--limit N`, `--offset N` |
| `set-cookie` | 设置 Cookie | — |

## 支持的 URL 格式

- 回答：`https://www.zhihu.com/question/{id}/answer/{id}`
- 文章：`https://zhuanlan.zhihu.com/p/{id}`
- 想法：`https://www.zhihu.com/pin/{id}`
- 用户：`https://www.zhihu.com/people/{id}`

## 技术细节

- 使用知乎官方 API（`api.zhihu.com`）
- 请求头模拟浏览器环境，无需 Selenium 等浏览器自动化工具
- 支持回答、文章、想法三种内容类型的交互
- Cookie 存储在 `secrets/zhihu.env`，权限 0600，不输出到日志

## License

MIT
