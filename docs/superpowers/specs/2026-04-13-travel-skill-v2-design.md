# travel-skill v2 设计

日期：2026-04-13

## 1. 目标

`travel-skill v2` 的目标不是重写一个全新的旅行系统，而是在现有骨架上完成一次 `contract-first` 重构，让这条链路从“能产出一些页面”升级成“能稳定交付一套旅行攻略”。

本轮设计聚焦五件事：

- 把 intake 变成真正的门禁，而不是缺字段时崩溃或带病继续。
- 把主方案和备选方案都升级成独立的逐日规划。
- 把样本引用、搜索词、伪媒体文本彻底隔离在发布链路之外。
- 把默认发布行为固定为桌面端 5 套、移动端 5 套、单文件分享、ZIP 和来源说明。
- 把 verify 从静态字符串检查升级成真实交付门禁。

## 2. 非目标

本轮不做以下内容：

- 不重写整条 orchestrator。
- 不承诺稳定抓全所有社媒评论、转写和关键帧。
- 不在首轮把所有旧脚本一次性替换掉。
- 不做超出当前 `travel-skill` 边界的大规模产品化编排。

## 3. 当前问题

当前实现的核心问题不是“完全没有功能”，而是合同不稳、边界不清、默认行为和 skill contract 不一致：

- `normalize_request.py` 在缺核心字段时可能直接 `KeyError`，并不是温和 gate。
- `build_trip_planning.py` 产出的备选方案没有真正独立的逐日内容。
- `build_guide_model.py` 没有消费 `planning.route_options`，发布模型里的多方案仍偏卡片化。
- `render_trip_site.py` 默认只发 1 套模板，需要调用方手动传 `--style all` 才会变成 5 套。
- `sample_reference` 仍可能被带进发布页，而 `verify_trip.py` 又会把它当成错误。
- `verify_trip.py` 只做少量字符串检查，不能代表“这套攻略已可交付”。

## 4. 总体架构

`travel-skill v2` 沿用当前骨架，但明确拆成六段职责清晰的链路：

1. `intake-gate`
2. `research-contract`
3. `planning-engine`
4. `content-compose`
5. `publish-render`
6. `delivery-verify`

职责边界如下：

- `intake-gate` 只负责判断请求是否可继续，禁止兼做 research 或发布。
- `research-contract` 只负责生成研究任务和 `web-access` 运行合同。
- `planning-engine` 只负责把 trip 变成主方案和备选方案的逐日路线。
- `content-compose` 只负责把规划和事实装配为攻略内容模型。
- `publish-render` 只负责桌面端、移动端、单文件和 ZIP 产物。
- `delivery-verify` 只负责判断“是否达到可交付标准”。

## 5. 数据合同

### 5.1 请求归一化合同

`trip_request.normalized.json` 在保留现有字段基础上，新增以下字段：

- `intake_status`
- `blocking_fields`
- `warning_fields`
- `follow_up_questions`

规则：

- 缺 `departure_city`、`destinations`、`date_range`、`travelers`、`budget` 任一字段时，`intake_status=blocked`
- 被 blocked 的请求不能进入 `research-contract`
- `sample_reference` 只保留在 gate 与内部审校层，不透传到发布层 `meta`

### 5.2 Gate 合同

新增 `trip_request.gate.json`：

- `can_proceed`
- `blocking_fields`
- `warning_fields`
- `follow_up_questions`
- `traveler_constraints`

规则：

- `can_proceed=false` 时，后续 research、planning、publish 全部停止
- 有老人或小孩但年龄描述不清时，允许继续 research，但默认规划不能给强节奏方案

### 5.3 规划合同

`planning.route-main.json`

- `plan_id`
- `title`
- `fit_for`
- `tradeoffs`
- `days[]`

`planning.route-options.json`

- `plans[]`
- 每个 `plan` 都必须有完整的 `days[]`

每个 `day` 至少包含：

- `day`
- `base_city`
- `theme`
- `morning`
- `afternoon`
- `evening`
- `transport`
- `meals`
- `backup_spots`

硬规则：

- 主方案固定 1 条，必须逐日展开
- 备选方案 2 到 3 条
- `route_options[].days` 必须是独立内容，不允许引用或复用主方案 `days`
- 超过 `1000km` 时，`flight-hybrid` 必须出现
- 不超过 `1000km` 时，也必须至少有 2 条不同节奏或不同停留方式的备选

### 5.4 内容模型合同

`guide-content.json` 继续保留三层输出：

- `daily-overview`
- `recommended`
- `comprehensive`

但新增以下要求：

- `recommended.route_options` 必须来自 planning 结果，而不是仅靠 transport 卡片推导
- `daily-overview.days` 优先消费 `planning.route_main.days`
- 如果 planning 不完整，compose 可以降级，但必须显式标记 `is_placeholder`
- 发布前 verify 不允许 placeholder 残留在主方案和备选方案里

## 6. 门禁规则

### 6.1 阻断条件

以下情况必须阻断：

- 缺核心字段
- 请求中没有可识别目的地
- 需要时效性输出但没有任何可验证日期上下文
- research 事实中关键 section 全部为空

### 6.2 允许继续但要告警

以下情况允许继续，但必须进入 warning：

- 老人或小孩信息不够细
- 未来班次未开售，只能用最近可查日期代替
- 视频解析缺依赖，只能退回文字引用
- 公交或地铁细节不完整，只能输出接驳建议

## 7. Research 合同

`research-contract` 继续基于 `web-access`，不新增新的联网执行器。

要求如下：

- 所有在线收集仍通过 `web-access`
- 任务必须是“具体站点 + 具体 query”，不允许抽象标签
- 时效性事实必须带 `checked_at`
- 采集失败必须记录 `failed` 或失败原因

但 v2 明确把增强项和硬要求拆开：

- 硬要求：官方、交通、门票、预约、天气、来源链接
- 增强项：评论摘录、视频转写、时间轴、关键帧

规则：

- 增强项失败时可以降级，但必须明示
- 不允许把失败的增强项伪装成发布素材

## 8. Planning Engine 设计

`planning-engine` 是 v2 的核心修改点。

### 8.1 输入

- 通过 gate 的 trip request
- 结构化 facts
- `traveler_constraints`
- `distance_km`
- transport、weather、food、attractions、risks、lodging facts

### 8.2 输出

- `route-main.json`
- `route-options.json`
- `supporting-plans.json`

### 8.3 规划规则

- 按天而不是按卡片组织
- 跨城重交通日自动降密度
- 山岳和天气敏感景点优先给上午窗口
- 每天用餐和落脚城市必须一致
- 不为了“多方案”而复用同一份 `days`

### 8.4 备选方案策略

备选方案优先级：

- `rail-first`
- `flight-hybrid`
- `extended-nearby`

每个方案都要说明：

- 适用人群
- 代价
- 和主方案的区别

## 9. 中文化整理层

新增独立中文化整理层，位置在 compose 前。

职责：

- 统一中文术语
- 统一时间表达
- 统一票价与价格区间表达
- 统一风险提示语气
- 清理直接漏出的英文源文本

规则：

- 原始 source title 可以保留在来源层
- 主体阅读内容默认中文化
- verify 不能只以“没有英文字符”为准，而是要以“主要正文是否中文化完成”为准

## 10. 发布层合同

### 10.1 默认发布行为

默认行为直接固定为完整发布，不再依赖调用方传 `--style all`：

- 桌面端 5 套模板
- 移动端 5 套模板
- `portal.html`
- `recommended.html`
- `share.html`
- `package.zip`
- `notes/sources.md`
- `notes/sources.html`

### 10.2 模板规则

模板数量固定：

- `route-first`
- `decision-first`
- `destination-first`
- `transport-first`
- `lifestyle-first`

每套模板都必须在以下维度之一明显不同：

- 首屏结构
- section 顺序
- 信息强调策略
- 卡片形态

模板不能只是换颜色和换字体。

### 10.3 发布页禁入项

发布页严禁出现：

- `对标样本`
- `sample.html`
- 搜索词痕迹
- `B站搜索：`
- `抖音搜索：`
- `来源参考：`
- `text-citation-only` 伪媒体区块

## 11. 媒体与视频合同

本轮不要求视频链路完整自动化，但必须把媒体门禁做真。

### 11.1 媒体状态

只允许三种有效发布状态：

- `text-citation-only`
- `illustrative-media`
- `hero-ready`

### 11.2 发布规则

- `text-citation-only` 只能进入来源层或文字引用层
- 没有真实图片 URL 或关键帧时，不能进入正文媒体区
- 没有真实可点击链接时，不能进入正文媒体区

### 11.3 依赖策略

如果 `ffmpeg` 或 `whisper` 缺失：

- 必须在媒体结果里显式记录
- 允许降级
- 不允许伪装成“已完成媒体处理”

## 12. Verify 设计

`delivery-verify` 由三层组成：

### 12.1 静态结构检查

- 桌面端 5 套模板是否齐全
- 移动端 5 套模板是否齐全
- `portal.html`、`recommended.html`、`share.html`、`package.zip` 是否存在
- `sources.md`、`sources.html` 是否存在

### 12.2 内容合同检查

- 主方案是否逐日展开
- 多方案是否逐日展开
- 核心 section 是否齐全
- 时效性事实是否带 `checked_at`
- 发布页是否有样本泄漏
- 发布页是否有伪媒体块
- 是否残留 placeholder

### 12.3 浏览器级检查

至少用 Playwright 或同等检查器验证：

- 页面能打开
- 无明显脚本错误
- 单文件版本可独立打开
- 移动端页面存在且非空

硬规则：

- 任一端缺失都必须 fail
- 不允许出现“mobile 全丢但 verify pass”

## 13. 实施阶段

### 阶段 1：Gate 与 Contract

- 修 `normalize_request.py`
- 新增 request gate 输出
- 把 `sample_reference` 从发布层隔离出去
- 补缺字段和门禁测试

完成标准：

- 缺核心字段时不崩
- blocked request 不进入 research
- 发布模型 `meta` 不再暴露样本引用

### 阶段 2：Planning 与 Publish

- 重写 `build_trip_planning.py` 的备选方案输出
- 改 `build_guide_model.py` 消费 planning 结果
- 改 `render_trip_site.py` 默认发 5 套模板
- 把模板差异从“换皮”提升为“编排差异”

完成标准：

- 主方案和备选方案都逐日展开
- 默认发布即完整模板集
- 短途场景不再退化成只有 1 个 route option

### 阶段 3：Verify、中文化、媒体门禁

- 新增中文化整理层
- 强化 `verify_trip.py`
- 接入浏览器级校验
- 收紧媒体门禁

完成标准：

- 删除 `mobile/` 后 verify fail
- 正文主文案中文化完成
- 非可发布媒体不会进入正文媒体区

## 14. 风险与边界

已知风险：

- 社媒与视频解析仍依赖外部环境和工具链
- 现有测试通过不代表当前 contract 正确，需要补盲区测试
- 模板改造成真正的 5 套不同阅读体验，会牵涉渲染层结构调整

边界判断：

- 首轮以“修 contract 和交付门禁”为先
- 不在首轮追求平台抓取的极致自动化
- 不在首轮做统一总 orchestrator

## 15. 验收标准

`travel-skill v2` 达标需同时满足：

- 缺字段请求不会崩，且会被 gate 明确阻断
- 主方案和备选方案都是独立逐日路线
- 默认发布能直接产出完整交付集
- 发布页无样本、无搜索词、无伪媒体泄漏
- verify 能拦截多端缺失和内容 contract 违规
- 媒体降级行为真实、明确、可追踪

## 16. 决策摘要

本设计确认以下决策：

- 采用增量重构，不推倒重来
- 先修 contract，再补功能
- planning 是 v2 的核心，不再让 route options 停留在交通卡片层
- 默认发布行为必须等于完整交付行为
- verify 必须升级成真实门禁，而不是装饰性检查
