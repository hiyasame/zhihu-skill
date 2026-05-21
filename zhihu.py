#!/usr/bin/env python3
"""
知乎 Fisher CLI - 通过 Cookie 调用知乎 API 进行搜索、点赞、收藏、评论等操作
基于 https://github.com/crispyChicken999/zhihu-fisher-vscode 项目
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

COOKIE_FILE = Path(__file__).resolve().parent / "secrets" / "zhihu.env"

# ─────────────────────────────── Cookie 管理 ────────────────────────────────

def load_cookie() -> str:
    """从文件加载 Cookie"""
    if COOKIE_FILE.exists():
        content = COOKIE_FILE.read_text().strip()
        for line in content.splitlines():
            if line.startswith("ZHIHU_COOKIE="):
                return line[len("ZHIHU_COOKIE="):].strip().strip('"')
    return ""


def save_cookie(cookie: str):
    """保存 Cookie 到文件"""
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(f'ZHIHU_COOKIE="{cookie}"\n')
    os.chmod(COOKIE_FILE, 0o600)
    print(f"✅ Cookie 已保存到 {COOKIE_FILE}")


def require_cookie() -> str:
    """获取 Cookie，没有则报错"""
    cookie = load_cookie()
    if not cookie:
        print("❌ 未设置知乎 Cookie，请先运行：zhihu set-cookie <cookie>", file=sys.stderr)
        sys.exit(1)
    return cookie


# ─────────────────────────────── HTTP 请求 ────────────────────────────────

def get_headers(cookie: str, content_type: str = None) -> dict:
    """返回知乎 API 标准请求头"""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",  # 不压缩，方便直接读取
        "Cache-Control": "no-cache",
        "Cookie": cookie,
        "DNT": "1",
        "Origin": "https://www.zhihu.com",
        "Pragma": "no-cache",
        "Referer": "https://www.zhihu.com/search",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def api_request(method: str, url: str, cookie: str,
                 body=None, content_type: str = None) -> dict:
    """通用 API 请求"""
    headers = get_headers(cookie, content_type)

    if isinstance(body, str):
        data = body.encode("utf-8")
    elif isinstance(body, dict):
        data = json.dumps(body).encode("utf-8")
    elif isinstance(body, bytes):
        data = body
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            # 尝试解压
            try:
                import gzip
                raw = gzip.decompress(raw)
            except Exception:
                pass
            if not raw:
                return {"success": True}
            return json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body_raw = e.read()
        try:
            import gzip
            body_raw = gzip.decompress(body_raw)
        except Exception:
            pass
        try:
            err_json = json.loads(body_raw)
            print(f"❌ HTTP {e.code}: {err_json}", file=sys.stderr)
        except Exception:
            print(f"❌ HTTP {e.code}: {body_raw[:200]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────── URL 解析 ────────────────────────────────

def parse_content_info(url: str):
    """
    解析 URL，返回 (content_type, content_id)
    - answer: zhihu.com/question/xxx/answer/yyy
    - article: zhuanlan.zhihu.com/p/xxx
    - pin: zhihu.com/pin/xxx
    """
    import re
    # 回答
    m = re.search(r"/question/\d+/answer/(\d+)", url)
    if m:
        return "answer", m.group(1)
    # 文章
    m = re.search(r"/p/(\d+)", url)
    if m:
        return "article", m.group(1)
    # 想法
    m = re.search(r"/pin/(\d+)", url)
    if m:
        return "pin", m.group(1)
    # 用户
    m = re.search(r"zhihu\.com/people/([^/?#]+)", url)
    if m:
        return "user", m.group(1)
    return None, None


# ─────────────────────────────── 搜索 ────────────────────────────────

def cmd_search(args):
    """搜索文章/回答"""
    cookie = require_cookie()
    query = " ".join(args.query)
    limit = min(args.limit, 50)
    offset = args.offset

    params = {
        "t": "general",
        "q": query,
        "correction": "1",
        "offset": str(offset),
        "limit": str(limit),
        "lc_idx": "0",
        "show_all_topics": "0",
        "search_source": "Normal",
    }

    url = "https://api.zhihu.com/search_v3?" + urllib.parse.urlencode(params)
    result = api_request("GET", url, cookie)

    items = result.get("data", [])

    # 过滤广告/教育类型
    SKIP_TYPES = {"education", "knowledge_ad", "promotion", "ad", "relevant_query"}
    real_items = [it for it in items if it.get("type") not in SKIP_TYPES]

    # 如果指定了类型，进一步过滤
    if args.type:
        real_items = [it for it in real_items
                      if it.get("object", {}).get("type") == args.type]

    total = len(real_items)
    print(f"🔍 搜索「{query}」 — 共 {total} 条结果\n{'─' * 60}\n")

    for i, item in enumerate(real_items, 1):
        obj = item.get("object", {})
        obj_type = obj.get("type", "")
        # search_result 包装
        if item.get("type") == "search_result" and not obj_type:
            obj = item
            obj_type = obj.get("type", "")

        # highlight 中的 title 去除 HTML
        import re as _re
        def clean_html(s): return _re.sub(r'<[^>]+>', '', s or "")

        if obj_type == "answer":
            # question title 可能在 obj["question"] 或 obj["description"] 或 item["highlight"]["title"]
            question = obj.get("question", {})
            q_title = (question.get("title") or question.get("name")
                       or clean_html(item.get("highlight", {}).get("title", ""))
                       or obj.get("description", "")[:60]
                       or "（无标题）")
            q_title = clean_html(q_title)
            author = obj.get("author", {}).get("name", "匿名")
            voteup = obj.get("voteup_count", 0)
            ans_id = obj.get("id", "")
            q_id = question.get("id", "") or obj.get("question_id", "")
            if q_id and ans_id:
                link = f"https://www.zhihu.com/question/{q_id}/answer/{ans_id}"
            else:
                link = obj.get("url", "").replace("api.zhihu.com", "www.zhihu.com")
            excerpt = clean_html(obj.get("excerpt", ""))[:120]
            print(f"{i}. [回答] {q_title}")
            print(f"   👤 {author}  👍 {voteup}")
            if excerpt:
                print(f"   {excerpt}")
            print(f"   🔗 {link}\n")

        elif obj_type == "article":
            title = clean_html(obj.get("title") or item.get("highlight", {}).get("title", "") or "（无标题）")
            author = obj.get("author", {}).get("name", "匿名")
            voteup = obj.get("voteup_count", 0)
            art_id = obj.get("id", "")
            link = f"https://zhuanlan.zhihu.com/p/{art_id}"
            excerpt = clean_html(obj.get("excerpt", ""))[:120]
            print(f"{i}. [文章] {title}")
            print(f"   👤 {author}  👍 {voteup}")
            if excerpt:
                print(f"   {excerpt}")
            print(f"   🔗 {link}\n")

        elif obj_type == "question":
            title = clean_html(obj.get("title") or obj.get("name") or "（无标题）")
            q_id = obj.get("id", "")
            link = f"https://www.zhihu.com/question/{q_id}"
            answer_count = obj.get("answer_count", 0)
            print(f"{i}. [问题] {title}")
            print(f"   💬 {answer_count} 个回答")
            print(f"   🔗 {link}\n")

        else:
            title = clean_html(obj.get("title") or obj.get("name") or "")
            if not title:
                title = f"（类型: {obj_type}）"
            print(f"{i}. [{obj_type}] {title}\n")


# ─────────────────────────────── 热榜 ────────────────────────────────

def cmd_hot(args):
    """获取知乎热榜"""
    cookie = require_cookie()
        # 知乎热榜从页面数据获取（API 端点已废弃）
    url = "https://www.zhihu.com/hot"
    headers = get_headers(cookie)
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"❌ 获取热榜失败: {e}", file=sys.stderr)
        sys.exit(1)

    import re
    m = re.search(r'<script[^>]*id="js-initialData"[^>]*>([^<]+)</script>', html)
    if not m:
        print("❌ 无法解析热榜数据", file=sys.stderr)
        sys.exit(1)

    raw = m.group(1)
    raw = raw.replace("\\\\u002F", "/").replace("\\u002F", "/").replace("\\\\n", "").replace("\\n", "")
    data = json.loads(raw)
    hotlist = data.get("initialState", {}).get("topstory", {}).get("hotList", [])

    print(f"🔥 知乎热榜 — 共 {len(hotlist)} 条\n{'─' * 70}")
    for i, item in enumerate(hotlist, 1):
        target = item.get("target", {})
        title = (target.get("titleArea", {}) or {}).get("text", "") or "(无标题)"
        metrics = (target.get("metricsArea", {}) or {}).get("text", "")
        excerpt = (target.get("excerptArea", {}) or {}).get("text", "")[:80]
        link = (target.get("link", {}) or {}).get("url", "")
        print(f"{i:2}. {title}")
        if metrics:
            print(f"    📊 {metrics}")
        if excerpt:
            print(f"    📝 {excerpt}")
        if link:
            print(f"    🔗 {link}")
        print()


# ─────────────────────────────── 点赞 ────────────────────────────────

def cmd_upvote(args):
    """点赞或取消点赞"""
    cookie = require_cookie()
    url = args.url
    cancel = args.cancel

    content_type, content_id = parse_content_info(url)
    if not content_type or not content_id:
        print("❌ 无法识别 URL 类型（支持回答、文章、想法）", file=sys.stderr)
        sys.exit(1)

    if content_type == "answer":
        api_url = f"https://www.zhihu.com/api/v4/answers/{content_id}/voters"
        vote_type = "neutral" if cancel else "up"
        result = api_request("POST", api_url, cookie,
                              body={"type": vote_type}, content_type="application/json")
        action = "取消点赞" if cancel else "点赞"
        print(f"✅ 已{action}回答 {content_id}")

    elif content_type == "article":
        api_url = f"https://www.zhihu.com/api/v4/articles/{content_id}/voters"
        voting = 0 if cancel else 1
        result = api_request("POST", api_url, cookie,
                              body={"voting": voting}, content_type="application/json")
        action = "取消点赞" if cancel else "点赞"
        print(f"✅ 已{action}文章 {content_id}")

    elif content_type == "pin":
        method = "DELETE" if cancel else "POST"
        api_url = f"https://www.zhihu.com/api/v4/pins/{content_id}/voters/up"
        result = api_request(method, api_url, cookie,
                              body={"not_sync_moments": True}, content_type="application/json")
        action = "取消点赞" if cancel else "点赞"
        print(f"✅ 已{action}想法 {content_id}")

    else:
        print(f"❌ 不支持对 {content_type} 类型点赞", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────── 收藏 ────────────────────────────────

def cmd_collections(args):
    """查看收藏夹列表"""
    cookie = require_cookie()
    # 先获取当前用户信息
    me = api_request("GET", "https://www.zhihu.com/api/v4/me", cookie)
    user_id = me.get("id") or me.get("url_token")
    if not user_id:
        print("❌ 无法获取用户信息，请检查 Cookie 是否有效", file=sys.stderr)
        sys.exit(1)

    params = urllib.parse.urlencode({
        "offset": args.offset,
        "limit": args.limit,
    })
    url = f"https://www.zhihu.com/api/v4/people/{user_id}/collections?{params}"
    result = api_request("GET", url, cookie)
    items = result.get("data", [])
    print(f"📚 我的收藏夹（共 {len(items)} 个）\n{'─' * 60}")
    for i, col in enumerate(items, 1):
        col_id = col.get("id", "")
        title = col.get("title", "（无标题）")
        count = col.get("item_count", 0)
        is_public = "公开" if col.get("is_public") else "私密"
        print(f"{i}. [{col_id}] {title}  ({count} 项, {is_public})")


def cmd_favorite(args):
    """收藏内容"""
    cookie = require_cookie()
    url = args.url
    collection_id = args.collection_id

    content_type, content_id = parse_content_info(url)
    if not content_type or not content_id:
        print("❌ 无法识别 URL 类型（支持回答、文章）", file=sys.stderr)
        sys.exit(1)

    if content_type not in ("answer", "article"):
        print(f"❌ 收藏仅支持回答和文章类型", file=sys.stderr)
        sys.exit(1)

    if not collection_id:
        # 如果没指定收藏夹 ID，先列出收藏夹让用户选择
        me = api_request("GET", "https://www.zhihu.com/api/v4/me", cookie)
        user_id = me.get("id") or me.get("url_token")
        col_url = f"https://www.zhihu.com/api/v4/people/{user_id}/collections?offset=0&limit=20"
        result = api_request("GET", col_url, cookie)
        items = result.get("data", [])
        if not items:
            print("❌ 您还没有收藏夹，请先在知乎创建收藏夹", file=sys.stderr)
            sys.exit(1)
        print("📚 请选择收藏夹（复制 ID 后重新运行带 --collection-id 参数）：")
        for col in items:
            print(f"  ID: {col['id']}  标题: {col['title']}")
        return

    api_url = f"https://www.zhihu.com/api/v4/collections/{collection_id}/contents?content_id={content_id}&content_type={content_type}"
    result = api_request("POST", api_url, cookie,
                          content_type="application/x-www-form-urlencoded; charset=UTF-8")
    print(f"✅ 已收藏 {content_type} {content_id} 到收藏夹 {collection_id}")


def cmd_unfavorite(args):
    """取消收藏"""
    cookie = require_cookie()
    url = args.url
    collection_id = args.collection_id

    content_type, content_id = parse_content_info(url)
    if not content_type or not content_id:
        print("❌ 无法识别 URL 类型", file=sys.stderr)
        sys.exit(1)

    if not collection_id:
        print("❌ 取消收藏需要指定 --collection-id", file=sys.stderr)
        sys.exit(1)

    api_url = f"https://www.zhihu.com/api/v4/collections/{collection_id}/contents/{content_id}?content_type={content_type}"
    result = api_request("DELETE", api_url, cookie)
    print(f"✅ 已从收藏夹 {collection_id} 取消收藏 {content_type} {content_id}")


# ─────────────────────────────── 评论 ────────────────────────────────

def cmd_comment(args):
    """发表评论"""
    cookie = require_cookie()
    url = args.url
    content_text = " ".join(args.content)

    content_type, content_id = parse_content_info(url)
    if not content_type or not content_id:
        print("❌ 无法识别 URL 类型（支持回答、文章）", file=sys.stderr)
        sys.exit(1)

    if content_type == "answer":
        api_url = f"https://www.zhihu.com/api/v4/answers/{content_id}/root_comments"
    elif content_type == "article":
        api_url = f"https://www.zhihu.com/api/v4/articles/{content_id}/root_comments"
    elif content_type == "pin":
        api_url = f"https://www.zhihu.com/api/v4/pins/{content_id}/root_comments"
    else:
        print(f"❌ 不支持对 {content_type} 类型评论", file=sys.stderr)
        sys.exit(1)

    body = {
        "content": [{"type": "paragraph", "paragraph": {"elements": [{"type": "text", "text": {"content": content_text}}]}}]
    }
    result = api_request("POST", api_url, cookie, body=body, content_type="application/json")
    comment_id = result.get("id", "（未知）")
    print(f"✅ 评论成功！评论 ID: {comment_id}")
    print(f"   内容: {content_text}")


def cmd_like_comment(args):
    """点赞/取消点赞评论"""
    cookie = require_cookie()
    comment_id = args.comment_id
    cancel = args.cancel

    method = "DELETE" if cancel else "POST"
    api_url = f"https://www.zhihu.com/api/v4/comments/{comment_id}/like"
    result = api_request(method, api_url, cookie, content_type="application/json")
    action = "取消点赞" if cancel else "点赞"
    print(f"✅ 已{action}评论 {comment_id}")


# ─────────────────────────────── 关注 ────────────────────────────────

def cmd_follow(args):
    """关注/取消关注用户"""
    cookie = require_cookie()
    url = args.url
    cancel = args.cancel

    content_type, user_id = parse_content_info(url)
    if content_type != "user" or not user_id:
        # 可能是直接传了 url_token
        import re
        m = re.search(r"people/([^/?#]+)", url)
        if m:
            user_id = m.group(1)
        else:
            user_id = url.strip("/").split("/")[-1]

    if not user_id:
        print("❌ 无法解析用户 URL，请传入 https://www.zhihu.com/people/xxx 格式", file=sys.stderr)
        sys.exit(1)

    api_url = f"https://www.zhihu.com/api/v4/members/{user_id}/followers"
    method = "DELETE" if cancel else "POST"
    result = api_request(method, api_url, cookie, content_type="application/json")
    action = "取消关注" if cancel else "关注"
    print(f"✅ 已{action}用户 {user_id}")


# ─────────────────────────────── 主入口 ────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="zhihu",
        description="知乎 Fisher CLI — 通过 Cookie 调用知乎 API"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # set-cookie
    p = subparsers.add_parser("set-cookie", help="设置知乎 Cookie")
    p.add_argument("cookie", nargs="+", help="知乎 Cookie 字符串")
    p.set_defaults(func=lambda a: save_cookie(" ".join(a.cookie)))

    # search
    p = subparsers.add_parser("search", help="搜索文章/回答")
    p.add_argument("query", nargs="+", help="搜索关键词")
    p.add_argument("--type", choices=["article", "answer"], help="内容类型")
    p.add_argument("--limit", type=int, default=10, help="返回数量（默认10，最大50）")
    p.add_argument("--offset", type=int, default=0, help="分页偏移")
    p.set_defaults(func=cmd_search)

    # hot
    p = subparsers.add_parser("hot", help="查看知乎热榜")
    p.set_defaults(func=cmd_hot)

    # upvote
    p = subparsers.add_parser("upvote", help="点赞回答/文章/想法")
    p.add_argument("url", help="内容 URL")
    p.add_argument("--cancel", action="store_true", help="取消点赞")
    p.set_defaults(func=cmd_upvote)

    # collections
    p = subparsers.add_parser("collections", help="查看收藏夹列表")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_collections)

    # favorite
    p = subparsers.add_parser("favorite", help="收藏内容")
    p.add_argument("url", help="内容 URL")
    p.add_argument("--collection-id", dest="collection_id", help="收藏夹 ID（不指定则列出可用收藏夹）")
    p.set_defaults(func=cmd_favorite)

    # unfavorite
    p = subparsers.add_parser("unfavorite", help="取消收藏")
    p.add_argument("url", help="内容 URL")
    p.add_argument("--collection-id", dest="collection_id", required=True, help="收藏夹 ID")
    p.set_defaults(func=cmd_unfavorite)

    # comment
    p = subparsers.add_parser("comment", help="发表评论")
    p.add_argument("url", help="内容 URL（回答或文章）")
    p.add_argument("content", nargs="+", help="评论内容")
    p.set_defaults(func=cmd_comment)

    # like-comment
    p = subparsers.add_parser("like-comment", help="点赞评论")
    p.add_argument("comment_id", help="评论 ID")
    p.add_argument("--cancel", action="store_true", help="取消点赞")
    p.set_defaults(func=cmd_like_comment)

    # follow
    p = subparsers.add_parser("follow", help="关注用户")
    p.add_argument("url", help="用户主页 URL")
    p.add_argument("--cancel", action="store_true", help="取消关注")
    p.set_defaults(func=cmd_follow)

    # unfollow (alias)
    p = subparsers.add_parser("unfollow", help="取消关注用户")
    p.add_argument("url", help="用户主页 URL")
    p.set_defaults(func=lambda a: cmd_follow(type('args', (), {'url': a.url, 'cancel': True})()))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
