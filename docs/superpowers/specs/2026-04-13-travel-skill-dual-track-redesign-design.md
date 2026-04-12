# travel-skill 双轨重构设计

日期：2026-04-13

## 1. 背景与问题

当前 `travel-skill` 已经能从请求生成研究包、攻略模型、HTML 和打包产物，但核心链路存在结构性问题：

- 研究数据、行程规划、发布产物混放在同一 trip 目录里，职责不清。
- 生成内容大量沿用英文键值和英文语义，不适合直接阅读。
- 城市知识、景点知识、交通段知识没有长期沉淀，难以复用。
- 当前“最推荐路线”和“多方案”并不是真正逐日规划，而是从景点和餐饮列表机械拼接。
- 5 套模板实际上共用同一骨架，只换配色和字体，导致结果高度相似。
- 发布页会把 `对标样本`、搜索词、伪来源文案直接写进正文。
- 视频来源没有经过真实媒体解析，却被伪装成“参考画面”。
- 最终攻略产物与研究数据混放，目录边界混乱。

本次重构目标不是只修当前案例，而是重建 `travel-skill` 的通用链路，并用 `2026-mayday-nanjing-yanji-changbaishan` 作为首个验收样本。

## 2. 目标

本次重构采用双轨系统：

- 一条轨道负责长期沉淀“目的地知识”与“城市间交通段知识”。
- 一条轨道负责“单次旅行规划”与“最终攻略出版”。

目标如下：

- 默认产出中文可读内容。
- 按城市沉淀知识，按“城市到城市”或“枢纽到景区”沉淀交通段。
- 攻略产物单独输出到 `guides/`，不再与研究数据混放。
- 主方案与备选方案都必须逐日展开。
- 5 个模板必须是 5 种不同的信息编排，不是换皮。
- 视频解析成为 `travel-skill` 必选能力，但没有真实关键帧和真实原链接时，视频不能进入正文画面区。
- 建立明确的验证门禁，阻断伪内容进入最终发布物。

## 3. 非目标

以下内容不在本轮设计目标内：

- 直接在本轮设计中实现所有平台抓取细节。
- 直接统一替换仓库内所有旧脚本。
- 在没有完成新合同前继续堆补丁增强旧 `guide-content.json` 链路。

## 4. 总体架构

系统拆为四层：

1. `destination knowledge`
2. `trip planning`
3. `publishing`
4. `media pipeline`

职责边界如下：

- `destination knowledge` 回答“这个地方本身有什么”。
- `trip planning` 回答“这次具体怎么走”。
- `publishing` 回答“怎么把这次旅行讲给客户看”。
- `media pipeline` 回答“哪些图和视频真的能用于正文发布”。

## 5. 新目录结构

建议目录结构如下：

```text
travel-data/
  places/
    yanji/
      place.json
      climate.json
      seasonality.json
      city-transport.json
      food.json
      attractions/
      media/
      sources/
    changbaishan/
    tumen/
  corridors/
    nanjing-to-changchun/
      transport.json
      sources.json
    changchun-to-yanji/
      transport.json
      sources.json
    yanji-to-erdaobaihe/
      transport.json
      sources.json
  trips/
    2026-mayday-nanjing-yanji-changbaishan/
      request/
        raw.json
        normalized.json
      planning/
        trip-brief.json
        route-main.json
        route-options.json
        day-plans.json
        supporting-plans.json
      snapshots/
        linked-knowledge.json
        linked-corridors.json
  guides/
    2026-mayday-nanjing-yanji-changbaishan/
      desktop/
      mobile/
      share/
      package/
      verify/
```

目录规则：

- `places/` 只存可复用目的地知识。
- `corridors/` 只存可复用交通段知识。
- `trips/` 只存某次出行实例与规划结果。
- `guides/` 只存最终发布成品。
- 研究结果进入知识库前需要结构化，不再直接作为最终发布输入。

## 6. 目的地知识合同

### 6.1 城市目录

每个城市至少包含：

- `place.json`
- `climate.json`
- `seasonality.json`
- `city-transport.json`
- `food.json`
- `attractions/*.json`
- `media/`
- `sources/`

### 6.2 字段最小集

`place.json`

- `name_zh`
- `slug`
- `aliases`
- `city_type`
- `summary_zh`

`climate.json`

- `monthly_avg_temp`
- `monthly_avg_high`
- `monthly_avg_low`
- `wind_notes`
- `packing_advice`

`seasonality.json`

- `best_windows`
- `current_window_assessment`
- `why_go_now`
- `why_not_now`
- `reference_links`

`food.json`

- `dish_name`
- `shop_name`
- `shop_area`
- `must_order`
- `queue_tip`
- `source_platforms`

`attractions/*.json`

- `name_zh`
- `visit_duration`
- `ticketing`
- `reservation`
- `best_time_of_day`
- `source_links`

不同类型景点需要追加专属字段：

- 山岳景点：`route_recommendations`、`viewpoints`、`photo_spots`
- 博物馆或展馆：`must_see_items`
- 园林古建：`history_notes`、`famous_halls`

## 7. 交通走廊合同

`corridors/<from>-to-<to>/transport.json` 用于沉淀稳定交通段，必须按交通模式拆分：

- `rail`
- `flight`
- `bus`
- `taxi`
- `self_drive`

高铁与航班记录至少包含：

- `checked_at`
- `search_date_used`
- `used_latest_searchable_schedule`
- `from`
- `to`
- `train_or_flight_no`
- `depart_time`
- `arrive_time`
- `duration`
- `price_range`

规则：

- 如果未来日期尚未开票，可用“最近可查询班次”代替，但必须显式记录检索基准。
- 不允许伪造公交线路号或不可验证的班次细节。

## 8. 规划层合同

规划层是本次重构核心。其职责是把一次旅行变成真正可执行的逐日方案，而不是从素材拼卡片。

### 8.1 规划文件

- `trip-brief.json`
- `route-main.json`
- `route-options.json`
- `day-plans.json`
- `supporting-plans.json`

### 8.2 `trip-brief.json`

最少字段：

- `departure_city`
- `date_range`
- `travelers`
- `pace`
- `budget_level`
- `must_go`
- `optional_go`
- `allow_nearby_extensions`

### 8.3 `route-main.json`

唯一主方案，必须逐日展开。每一天必须包含：

- `day`
- `base_city`
- `theme`
- `morning`
- `afternoon`
- `evening`
- `transport`
- `meals`
- `backup_spots`

规则：

- 每天只能有一个主轴。
- 跨城重交通日自动降密度。
- 山岳景区优先抢上午窗口，不能与城市景点随机混排。
- 每日餐饮必须跟当天落脚城市和路线走。

### 8.4 `route-options.json`

每个备选方案也必须逐日展开，不允许只给“高铁优先/空铁联运”卡片。

建议至少支持：

- `rail-first`
- `flight-hybrid`
- `extended-nearby`

每个方案至少包含：

- `plan_id`
- `title`
- `fit_for`
- `tradeoffs`
- `days`

### 8.5 `supporting-plans.json`

集中承载：

- `food-plan`
- `clothing-plan`
- `transport-plan`
- `risk-plan`

其中：

- `food-plan` 既要有城市维度概览，也要有逐日绑定餐饮建议和备选店。
- `clothing-plan` 需要包含历史均温、场景体感和打包清单。
- `transport-plan` 必须拆成 `intercity`、`last-mile`、`urban` 三层。
- `risk-plan` 必须按票务、天气、排队、复核、体力、跨城疲劳等场景拆分。

## 9. 发布层与模板合同

发布层只消费已验证的知识、规划和媒体，不再临时补全事实或推断路线。

### 9.1 模板原则

5 套模板必须是 5 套独立的出版编排，而不是共用一个 DOM 骨架再换样式。

### 9.2 模板 manifest

每个模板必须拥有独立 `template_manifest.json`，至少包含：

- `template_id`
- `template_name_zh`
- `layout_strategy`
- `hero_mode`
- `section_order`
- `section_components`
- `allowed_media_slots`

### 9.3 推荐的 5 套模板

- `route-first`
- `decision-first`
- `destination-first`
- `transport-first`
- `lifestyle-first`

每套模板必须至少在以下维度存在明显差异：

- 首屏结构
- 章节顺序
- 组件形态
- 强调模块

### 9.4 发布目录

```text
guides/<trip-slug>/
  desktop/
    route-first/
    decision-first/
    destination-first/
    transport-first/
    lifestyle-first/
  mobile/
    route-first/
    decision-first/
    destination-first/
    transport-first/
    lifestyle-first/
  share/
    route-first.html
    decision-first.html
    destination-first.html
    transport-first.html
    lifestyle-first.html
  package/
    travel-guide.zip
  verify/
    verify-report.json
```

规则：

- 每次发布只能输出 5 套模板，不再生成 legacy 默认版。
- 攻略成品只能落到 `guides/`，不能继续放在 trip 研究目录内。

## 10. 媒体与视频解析合同

媒体层是独立管线，不再由渲染器自行判断“能不能上图”。

### 10.1 媒体子链路

- `link validation`
- `image/article extraction`
- `video extraction`

### 10.2 视频解析流程

```text
原始视频链接
  -> 平台识别
  -> 链接校验
  -> 元数据抓取
  -> 音频抽取(ffmpeg)
  -> 转写(whisper)
  -> 时间轴切片
  -> 关键帧提取(ffmpeg)
  -> 关键帧打标
  -> 发布可用性判断
```

### 10.3 视频记录最小合同

- `platform`
- `url`
- `title`
- `checked_at`
- `author`
- `duration_sec`
- `availability`
- `transcript_status`
- `keyframe_status`
- `transcript`
- `timeline_segments`
- `keyframes`
- `publishable_assets`

### 10.4 正文准入门禁

视频只允许以下三种状态：

- `text citation only`
- `illustrative media`
- `hero-ready media`

硬规则：

- 没有真实可点击原链接时，不能进入正文媒体区。
- 没有真实关键帧时，不能进入正文媒体区。
- 只有文字摘要的视频可以保留为来源或正文引用，但不能伪装成“参考画面”。

### 10.5 环境要求

`travel-skill` 的媒体链路将显式依赖：

- `ffmpeg`
- `whisper`
- 必要的 Python 包或 CLI

如果依赖缺失，必须在结果中明确标记媒体链路未完成，不允许默默降级成伪内容。

## 11. 验证与失败策略

发布成功的标准不再是“文件写出来了”，而是“合同正确、内容可信、媒体状态明确、产物结构符合要求”。

### 11.1 验证层

- `schema validation`
- `content validation`
- `publish validation`
- `evidence validation`

### 11.2 必须阻断发布的错误

- 主方案没有逐日展开。
- 多方案没有逐日展开。
- 交通段缺少 `from/to/schedule/checked_at`。
- 正文出现伪画面模块。
- 正文出现伪链接、搜索词或 `对标样本`。
- 模板数量不是 5 套。
- 仍生成 legacy 冗余结果。
- 中文化未完成。
- 视频未通过媒体门禁却进入正文画面区。
- 核心章节缺失。

### 11.3 允许降级但必须明示

- 未来日期未开票，允许使用最近可查班次代替。
- 视频解析失败，允许保留文字来源但移出媒体区。
- 公交细节不完整，允许退化为通用接驳建议。
- 个别餐饮链接失效，允许保留菜系与区域建议，但需标明待复核。

### 11.4 验证报告

建议统一输出 `verify-report.json`，至少包含：

- `schema_checks`
- `content_checks`
- `publish_checks`
- `media_checks`
- `blocking_errors`
- `warnings`
- `status`

关键检查项包括：

- `all_primary_text_in_zh`
- `all_route_plans_day_expanded`
- `no_sample_reference_in_publish`
- `no_fake_media_blocks`
- `exactly_five_templates`
- `no_legacy_outputs`
- `all_transport_segments_checked`
- `video_assets_gate_respected`

## 12. 迁移策略

本次重构不建议一次推倒重来，而是分阶段迁移。

### 12.1 迁移原则

- 先建立新合同，再迁移旧数据。
- 先让新规划层跑通，再替换旧渲染层。
- 先并行输出，再删除旧产物。
- 不再允许新增对旧“大一统 `guide-content.json`”链路的依赖。

### 12.2 推荐阶段

阶段 1：建立新目录和 schema

- 创建 `places/`、`corridors/`、`trips/`、`guides/`
- 新增基础 loader 与 schema 校验

阶段 2：拆 research 输出

- 把现有 research 结果拆入 `places`、`corridors`、`media` 和 trip 快照

阶段 3：重做 planning 层

- 新增真正的 `route-main`、`route-options`、`day-plans`、`supporting-plans`

阶段 4：重做 publishing 层

- 先做桌面端 5 套模板
- 再补移动端

阶段 5：接入媒体与视频链路

- 接入 `ffmpeg`
- 接入 `whisper`
- 建立媒体准入门禁

阶段 6：分享页、打包与验证收尾

- 从 `guides/` 导出分享页、ZIP 和 `verify-report.json`

## 13. 测试策略

推荐测试分层如下：

- schema 测试
- planning 测试
- media gate 测试
- 5 模板发布测试
- verify-report 测试

人工复核点保留三项：

- 主方案是否真的顺路
- 多方案是否真的有差异
- 5 套模板是否真的像 5 套作品，而不是换皮

## 14. 风险与开放问题

已确认风险：

- 视频平台的真实抓取与解析稳定性存在环境依赖。
- 当前旧脚本之间耦合较深，迁移时需要严格阻止新旧链路互相污染。

开放问题：

- 视频平台抓取具体实现方式，需在实现阶段结合环境能力进一步细化。
- 5 套模板的具体视觉语言和首屏组件，需要在发布实现阶段进一步设计。

## 15. 决策摘要

本设计已确认以下关键决策：

- 采用双轨系统而非单轨补丁修复。
- 采用“目的地知识库 + 交通走廊 + 单次旅行规划 + 独立发布物”的分层模型。
- 所有方案都必须逐日展开。
- 5 套模板必须是 5 种不同的信息编排。
- 视频解析为必选能力，但媒体门禁必须严格执行。
- 攻略成品必须从 `guides/` 单独输出。
