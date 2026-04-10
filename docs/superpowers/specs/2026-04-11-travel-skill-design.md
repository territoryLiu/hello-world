---
title: Travel Skill Design
date: 2026-04-11
status: approved-in-chat
owner: Codex
---

# Travel Skill Design

## 背景与问题

当前 `docs/pipe/travel-planning-playbook.md` 和 `trips/<slug>/...` 已经能生成一套桌面端 / 移动端旅游攻略工程，但还存在三个明显问题：

1. 内容密度不够稳定。现有产物更像结构完整的初稿，缺少 `sample.html` 那种执行层信息，包括订票顺序、逐段交通、价格区间、预算分档、单页执行表、店铺级清单和风险提示。
2. 流程复用性不足。研究、核验、编排、渲染、导出、分享目前没有被封装成一个可复用的旅游工作流，每次换目的地都要重新拼装上下文。
3. 交付物不便分享。现有产物以多文件工程为主，便于维护，但不适合直接发给他人查看；缺少单文件分享版、压缩包和可选静态网址分享能力。

目标不是再补一份玩法文档，而是把“搜集信息 -> 研究确认 -> 生成攻略 -> 打包分享”做成一个可执行的 `travel skill`。

## 目标

这个 `travel skill` 需要满足以下目标：

1. 把旅游攻略生产流程标准化，覆盖需求输入、信息采集、研究核验、内容编排、页面生成、分享导出和渲染校验。
2. 明确编排已有 skill 的职责，尤其是 `web-access`、`frontend-design`、`playwright-skill`，并允许通过内置 Python / JS 脚本补齐特殊功能。
3. 强制生成一份研究包作为人工确认闸门，避免把未核实的高时效信息直接写进最终成品。
4. 默认同时产出：
   - 可维护的攻略工程版
   - 可直接双击打开的单文件 HTML 分享版
   - 可转发的 ZIP 压缩包
5. 对攻略内容做“执行层补齐”，确保生成结果不只是框架完整，而是能够直接指导出行。

## 非目标

以下内容不在第一阶段范围内：

1. 不承诺完全自动化公网发布。静态网址分享是可选增强，不是主流程硬依赖。
2. 不承诺完全替代人工判断。店铺、天气、票务、景区临时规则等高时效信息仍需要确认闸门。
3. 不把实时票价、未来天气预报、具体车次等信息默认硬编码进正文。
4. 不要求第一期就覆盖所有目的地的复杂玩法；第一阶段优先打通吉林延吉长白山这一类多段交通、多来源研究型行程。

## 用户价值

相较于现有流程，这个 skill 需要给出更明确的用户价值：

1. 对内部使用者：从一次性的“写一篇攻略”升级为“运行一套旅游生产流水线”。
2. 对最终读者：从“能看懂的路线草稿”升级为“能拿着就出发的执行稿”。
3. 对分享场景：从“打开一个目录看很多文件”升级为“发一个 HTML 或一个 ZIP 就能看”。

## 流程总览

`travel skill` 固定采用六阶段流水线：

1. `intake`
2. `research`
3. `review-gate`
4. `compose`
5. `render`
6. `package-share`
7. `verify`

其中 `review-gate` 是强制闸门，`package-share` 和 `verify` 属于默认交付路径，不允许跳过。

## 阶段设计

### 1. intake

目的：把自然语言需求整理成结构化输入。

最少输入字段：

- 出发地
- 日期范围
- 人数与人群特征
- 预算区间
- 住宿偏好
- 交通偏好
- 必去 / 可选 / 不去项
- 节奏偏好
- 分享目标

输出文件：

- `trip-request.json`

关键要求：

- 对日期、人数、预算做标准化。
- 允许记录“未明确”的字段，但必须显式标记。
- 允许把“单文件分享版 / 工程版 / 网址分享”作为输出偏好写入请求。

### 2. research

目的：从多源收集可用事实和高价值经验，不直接生成成品。

来源分层：

1. 官方源
   - 12306
   - 航司 / 机场
   - 景区官网 / 公告
   - 官方天气入口
2. 社媒源
   - 小红书
   - 抖音
   - B站
3. 本地生活源
   - 美团
   - 大众点评
   - Trip / 携程餐厅页等公开店铺页

研究主题至少拆成：

- 交通
- 天气 / 历史体感
- 穿衣
- 景点 / 路线
- 美食 / 店铺
- 落脚区域 / 住宿
- 排队 / 避坑 / 时效风险

输出文件：

- `research/raw/*`
- `research/normalized/*`
- `research/research-summary.json`

关键要求：

- 每条关键事实记录来源、核对时间、来源类型。
- 一手源优先于二手源；社媒用于补玩法和体感，不替代官方规则。
- 高时效信息要带“当前可查”属性，不得默认写死。

### 3. review-gate

目的：把研究结果压缩成一份可人工确认的研究包。

确认重点：

- 推荐路线是否合理
- 交通主方案与备选方案
- 订票顺序
- 价格区间是否仍可信
- 天气口径是否写法安全
- 店铺清单是否值得写进正文
- 是否存在高风险未确认项

输出文件：

- `review/research-packet.md`
- `review/research-packet.html`
- `review/approved-research.json`

关键要求：

- 必须区分“已核实”“待确认”“仅作近期经验参考”。
- 这一阶段结束前，不进入最终页面生成。

### 4. compose

目的：先生成中间内容模型，再生成页面。

中间内容模型必须覆盖以下模块：

- `overview`
- `recommended`
- `options`
- `attractions`
- `food`
- `season`
- `packing`
- `transport`
- `sources`

在此基础上，必须补齐 `sample.html` 对现有攻略暴露出的执行层缺口：

- 订票顺序
- 逐段交通与备选
- 城市内接驳
- 价格区间
- 历史天气体感
- 分层穿衣建议
- 店铺级清单
- 每日执行表
- 预算分档
- 风险与避坑提示

输出文件：

- `guide-content.json` 或 `guide-content.js`

关键要求：

- 页面生成只能消费内容模型，不直接消费原始研究数据。
- 若关键模块缺失，必须在这一阶段阻断。

### 5. render

目的：把内容模型渲染成可维护工程和单文件分享版。

默认输出：

1. 工程版
   - `trips/<slug>/desktop/*`
   - `trips/<slug>/mobile/*`
   - `trips/<slug>/assets/*`
   - `trips/<slug>/notes/*`
2. 单文件分享版
   - `dist/<slug>.html`
3. 可选 PDF
   - `dist/<slug>.pdf`

单文件分享版要求：

- CSS 内联
- JS 内联
- 数据内联
- 保留目录导航和锚点跳转
- 默认可离线打开

关键要求：

- 工程版用于维护，单文件版用于分享。
- 单文件版不是简化摘要页，而是完整阅读版。

### 6. package-share

目的：生成便于转发和归档的交付物。

默认产物：

1. `dist/<slug>.html`
2. `dist/<slug>.zip`

ZIP 默认包含：

- 单文件 HTML
- 可选 PDF
- `sources.md`
- `trip-summary.txt`

可选增强：

- `dist/site/<slug>/` 静态站目录
- 若存在部署配置，再生成实际分享 URL

关键要求：

- 没有部署凭证时，不承诺公网地址。
- 即便没有 URL，也必须保证单文件 HTML 可以独立使用。

### 7. verify

目的：在宣称“已完成”之前做事实、完整性、渲染三层校验。

校验层次：

1. 事实校验
   - 关键事实是否有来源
   - 是否写明核对时间
   - 是否区分来源类型
2. 内容完整性校验
   - 必备 section 是否齐全
   - 店铺、交通、来源、风险项是否为空
3. 渲染校验
   - 桌面端可读
   - 移动端可读
   - 单文件版可直接打开
   - 导航、锚点、链接和资源正常

输出文件：

- `verify/report.json`
- `verify/report.md`

## Skill 编排

`travel skill` 本身作为编排器，不自己承担所有专长，而是明确调用已有 skill。

### 硬依赖

1. `web-access`
   - 负责联网采集
   - 适用于官网、社媒、本地生活平台、多源网页内容获取
2. `frontend-design`
   - 负责最终 HTML 成品设计
   - 确保结果不是普通模板页
3. `playwright-skill`
   - 负责渲染与交互校验

### 可选依赖

1. `theme-factory`
   - 在明确需要统一主题或品牌风格时使用
   - 不作为首期硬依赖
2. `last30days`
   - 用于近 30 天趋势与热点增强
   - 不作为唯一事实源
3. `visual-explainer`
   - 用于生成研究包或流程可视化页面

## 脚本职责

为了让 skill 真正可执行，而不是只靠文字说明，skill 内必须携带脚本。

建议脚本集合：

- `scripts/normalize_request.py`
- `scripts/build_research_tasks.py`
- `scripts/merge_sources.py`
- `scripts/extract_structured_facts.py`
- `scripts/generate_review_packet.py`
- `scripts/build_guide_model.py`
- `scripts/fill_missing_sections.py`
- `scripts/render_trip_site.py`
- `scripts/export_single_html.py`
- `scripts/export_pdf.py`
- `scripts/package_trip.py`
- `scripts/verify_trip.py`

职责划分：

1. 请求标准化
2. 研究任务拆分
3. 多源合并与去重
4. 结构化事实抽取
5. 研究包生成
6. 内容模型生成
7. 缺项检查与补齐
8. 页面渲染
9. 单文件导出
10. PDF 导出
11. ZIP 打包
12. 最终校验

## Skill 目录结构

建议目录结构如下：

```text
travel-skill/
├─ SKILL.md
├─ agents/
│  └─ openai.yaml
├─ scripts/
│  ├─ normalize_request.py
│  ├─ build_research_tasks.py
│  ├─ merge_sources.py
│  ├─ extract_structured_facts.py
│  ├─ generate_review_packet.py
│  ├─ build_guide_model.py
│  ├─ fill_missing_sections.py
│  ├─ render_trip_site.py
│  ├─ export_single_html.py
│  ├─ export_pdf.py
│  ├─ package_trip.py
│  └─ verify_trip.py
├─ references/
│  ├─ source-priority.md
│  ├─ research-checklists.md
│  ├─ content-schema.md
│  ├─ sharing-modes.md
│  └─ sample-gap-checklist.md
└─ assets/
   ├─ templates/
   └─ themes/
```

## 数据与文件结构

建议把运行期数据结构固定下来，便于脚本和页面共享。

### 输入

- `trip-request.json`

### 研究产物

- `research/raw/*`
- `research/normalized/*`
- `research/research-summary.json`

### 审核产物

- `review/research-packet.md`
- `review/research-packet.html`
- `review/approved-research.json`

### 中间内容模型

- `guide-content.json` 或 `guide-content.js`

### 页面产物

- `trips/<slug>/...`
- `dist/<slug>.html`
- `dist/<slug>.pdf`
- `dist/<slug>.zip`

### 校验产物

- `verify/report.json`
- `verify/report.md`

## 分享策略

默认分享策略按照稳健性排序：

1. 单文件 HTML
2. ZIP
3. 静态网址分享

原因：

- 单文件最稳，不依赖部署环境。
- ZIP 便于转发、归档和附带研究来源。
- URL 最方便，但受部署能力约束，不应成为唯一交付方式。

单文件 HTML 的交互要求：

- 顶部导航
- section 锚点
- 可直接进入攻略界面
- 不需要本地服务

## 核验与时效规则

### 来源优先级

优先级从高到低：

1. 官方一手源
2. 正规平台公开页面
3. 本地生活平台页
4. 社媒经验内容

规则：

- 规则、票务、交通、营业、公告优先看一手源。
- 体感、避坑、拍照点、店铺热度可由社媒补充。

### 可以写死的内容

- 静态地理关系
- 经典路线结构
- 景点组合
- 穿衣分层原则
- 行程节奏逻辑

### 不能轻易写死的内容

- 具体车次和航班
- 实时票价
- 未来精确天气预报
- 店铺当日营业状态
- 景区临时开放规则
- 节假日限时活动

### 写法规则

对于高时效信息：

- 如需写具体数字，必须附带核对日期和来源
- 优先写“查询入口 + 订票顺序 + 决策建议”
- 不确定项用“当前可查”“建议临近出发复核”“近期常见反馈”表达，不伪装成确定事实

## 第一阶段实现范围

第一阶段优先打通吉林延吉长白山这类行程，原因是它具备代表性：

- 多段交通
- 山区天气与城市体感并存
- 官方规则和社媒经验都重要
- 美食与店铺信息密度高
- 现有仓库已有基础攻略工程可复用

第一阶段范围：

1. skill 骨架
2. 研究包生成
3. 内容模型生成
4. 工程版渲染
5. 单文件 HTML 导出
6. ZIP 打包
7. 基础校验

第二阶段再考虑：

1. 通用目的地模板强化
2. 主题切换
3. 静态网址发布
4. 多攻略集合入口页

## 决策总结

本设计的核心决策如下：

1. 采用“半自动 + 人工确认闸门”流程，而不是全自动黑盒。
2. `travel skill` 自身做编排，专长能力委托给已有 skill。
3. 把脚本能力内置到 skill 中，确保它能走完整流程。
4. 页面生成之前必须先有研究包和内容模型。
5. 默认交付同时包含工程版与单文件分享版。
6. 对高时效信息采用保守写法，避免过期内容被写死到正文。

## 风险与后续注意事项

1. 若没有稳定的部署凭证，网址分享只能作为增强能力，不应影响主流程。
2. 社媒和本地生活平台的采集可靠性会波动，因此研究层必须保留来源与核对时间。
3. 单文件 HTML 若内联大图过多，体积可能过大，需要提供轻量模式与增强模式。
4. 若未来扩展到更多目的地，需要维护一套可复用的研究检查表和内容 schema，避免 skill 演变成只服务单一路线的专用脚本包。
