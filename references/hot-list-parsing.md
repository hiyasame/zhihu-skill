# 知乎热榜 HTML 解析参考

## 背景

`https://www.zhihu.com/api/v4/hot_list` 旧 API 端点已废弃（返回 404），改为从 `https://www.zhihu.com/hot` 页面直接解析 HTML。

## 解析方式

参考 [zhihu-fisher-vscode](https://github.com/crispyChicken999/zhihu-fisher-vscode) 的实现，使用 Cheerio/正则解析 HTML。

### HTML 结构（当前有效）

```html
<section class="HotItem" tabindex="0">
  <div class="HotItem-index">
    <div class="HotItem-rank HotItem-hot">1</div>
  </div>
  <div class="HotItem-content">
    <a href="https://www.zhihu.com/question/{id}"
       title="标题" target="_blank">
      <h2 class="HotItem-title">标题文字</h2>
      <p class="HotItem-excerpt">摘要文字</p>
    </a>
    <div class="HotItem-metrics HotItem-metrics--bottom">
      <style>...</style>
      {热度值} 万热度
    </div>
  </div>
</section>
```

部分条目无图片时，`<a>` 标签包裹标题和摘要，链接出现在 metrics 之前。
部分条目有图片时，另有 `<a class="HotItem-img">` 标签，链接出现在 metrics 之后。

### CSS Selectors（对应原版插件）

| 数据 | 选择器 |
|------|--------|
| 容器 | `.HotList-list` |
| 条目 | `.HotItem` |
| 标题 | `.HotItem-title` |
| 摘要 | `.HotItem-excerpt` |
| 热度 | `.HotItem-metrics` |
| 图片 | `.HotItem-img img` |

## 清洗注意事项

- metrics 内部可能包含 `<style>` 标签（如 `.css-15ro776{margin-right:4px;}`），需要正则移除
- metrics 末尾可能有零宽空格（`\u200b`）和"分享"文字
- 部分条目没有摘要（excerpt），需处理为可选字段
- 链接位置不固定（可能在 metrics 前或后），需在整个 section 内搜第一个有效 href

## 失效时的应对

如果热榜再次失效，排查步骤：

1. 检查 `https://www.zhihu.com/hot` 页面是否返回 200
2. 检查页面中 `HotItem` 类名是否还存在
3. 尝试用浏览器打开页面，查看新的 CSS 类名
4. 参考 zhihu-fisher-vscode 插件的最新代码
