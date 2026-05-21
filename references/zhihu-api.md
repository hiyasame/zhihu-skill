# 知乎 API 端点参考

从 zhihu-fisher-vscode 项目整理的知乎 API 端点。所有请求需携带 Cookie。

## 基础信息

- **Base**: `api.zhihu.com` / `www.zhihu.com`
- **请求头**: 需携带 `Cookie`、`User-Agent`（模拟浏览器）、`Referer`、`X-Requested-With: XMLHttpRequest`
- **认证方式**: Cookie（含 `d_c0` 等字段）

## 搜索

### 全局搜索

```
GET https://api.zhihu.com/search_v3
```

参数：
| 参数 | 说明 |
|------|------|
| `t` | 搜索类型，固定 `general` |
| `q` | 搜索关键词 |
| `correction` | 纠错，`1` 开启 |
| `offset` | 分页偏移 |
| `limit` | 返回条数（最大 50） |
| `lc_idx` | 固定 `0` |
| `show_all_topics` | 固定 `0` |
| `search_source` | 固定 `Normal` |

返回中的 `data[].object.type` 区分内容类型：`answer`、`article`、`question`。

## 热榜

### 获取热榜

```
GET https://www.zhihu.com/api/v4/hot_list?business_type=normal&medium=hot_list
```

返回 `data[].target.title` 为话题标题，`target.id` 为对应 question_id。

## 用户

### 获取当前用户信息

```
GET https://www.zhihu.com/api/v4/me
```

返回 `id` / `url_token` 用于后续 API 调用。

## 点赞

### 回答点赞

```
POST https://www.zhihu.com/api/v4/answers/{answer_id}/voters
Body: {"type": "up"}         # 点赞
Body: {"type": "neutral"}    # 取消点赞
```

### 文章点赞

```
POST https://www.zhihu.com/api/v4/articles/{article_id}/voters
Body: {"voting": 1}   # 点赞
Body: {"voting": 0}   # 取消点赞
```

### 想法点赞

```
POST   https://www.zhihu.com/api/v4/pins/{pin_id}/voters/up
DELETE https://www.zhihu.com/api/v4/pins/{pin_id}/voters/up
```

## 收藏

### 收藏内容

```
POST https://www.zhihu.com/api/v4/collections/{collection_id}/contents?content_id={id}&content_type={type}
```

`content_type`: `answer` / `article`

### 取消收藏

```
DELETE https://www.zhihu.com/api/v4/collections/{collection_id}/contents/{content_id}?content_type={type}
```

### 查看收藏夹

```
GET https://www.zhihu.com/api/v4/people/{user_id}/collections?offset=0&limit=20
```

## 评论

### 发表评论

```
POST https://www.zhihu.com/api/v4/answers/{answer_id}/root_comments
POST https://www.zhihu.com/api/v4/articles/{article_id}/root_comments
POST https://www.zhihu.com/api/v4/pins/{pin_id}/root_comments

Body: {
  "content": [{
    "type": "paragraph",
    "paragraph": {
      "elements": [{
        "type": "text",
        "text": {"content": "评论内容"}
      }]
    }
  }]
}
```

返回中的 `id` 为评论 ID。

### 点赞评论

```
POST   https://www.zhihu.com/api/v4/comments/{comment_id}/like
DELETE https://www.zhihu.com/api/v4/comments/{comment_id}/like
```

## 关注

### 关注/取关用户

```
POST   https://www.zhihu.com/api/v4/members/{user_id}/followers
DELETE https://www.zhihu.com/api/v4/members/{user_id}/followers
```

## 注意事项

- Cookie 通常包含 `d_c0`、`z_c0`、`KL_*` 等多个字段，拼接为 `key1=value1; key2=value2` 格式
- Cookie 有效期通常为几周到几个月
- 请求频率过高可能会被限流
