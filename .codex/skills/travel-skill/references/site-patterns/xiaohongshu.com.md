---
domain: xiaohongshu.com
aliases: [小红书, RED, Xiaohongshu]
updated: 2026-04-08
---
## 平台特征
- PC Web 端公开内容可直接访问，但搜索结果和评论抓取需要真实浏览器环境，静态抓取价值很低。
- 已登录 Chrome 下，`search_result` 页面会直接渲染 `.note-item` 卡片，详情页会直接渲染 `.note-content` 和 `.comment-item`。
- 搜索与详情链接常带 `xsec_token` 等参数；使用站内生成的完整 URL 更稳。

## 有效模式
- 搜索页可直接访问 `https://www.xiaohongshu.com/search_result?keyword=关键词`。
- 搜索结果卡片可从 `.note-item` 中提取标题、作者、点赞和 `a[href*="/search_result/"]` 详情链接。
- 详情页正文可从 `.note-content .title`、`.note-content .desc`、`.note-content .date` 抽取。
- 详情页互动数可从 `.interact-container .count, .interaction-container .count` 的最后三个值获取，通常对应点赞、收藏、评论。
- 评论列表可从 `.comment-item` 抽取，`innerText` 里通常按“作者 / 内容 / 时间地点 / 赞 / 数字 / 回复”顺序排列。

## 已知陷阱
- 未登录状态下搜索页只显示“登录后查看搜索结果”，这时不要继续硬爬。
- PowerShell 中 `curl` 是 `Invoke-WebRequest` 别名，调本地 CDP proxy 时不要直接用 `curl` 语法。
- 评论区 DOM 中会同时混入主评论、子回复和交互按钮文字，不能简单把所有 `.count` 当作笔记统计。
