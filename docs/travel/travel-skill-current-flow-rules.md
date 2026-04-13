# travel-skill 处理流程和规则

日期：2026-04-13

## 1. 文档目的

这份文档整理的是当前仓库里 `.codex/skills/travel-skill` 的实际处理流程、已写入代码的规则、当前边界，以及已确认的缺口。

它描述的是“现在这套 skill 实际能做什么、怎么做、哪些地方会降级”，不是理想目标稿。

## 2. 适用范围

当前 `travel-skill` 设计用于把一次旅行请求加工成以下几类产物：

- 研究任务矩阵
- `web-access` 研究运行说明
- 结构化研究数据
- 攻略内容模型
- 桌面端和移动端 HTML
- 单文件分享页
- ZIP 打包结果
- 简单验证报告

默认规则写在以下位置：

- `.codex/skills/travel-skill/SKILL.md`
- `.codex/skills/travel-skill/agents/openai.yaml`
- `.codex/skills/travel-skill/references/*.md`
- `.codex/skills/travel-skill/scripts/*.py`

## 3. 当前总流程

当前 skill 约定的执行顺序如下：

1. intake
2. research-plan
3. research-run
4. review-gate
5. compose
6. render
7. package-share
8. verify

这条链路在 `SKILL.md` 里已经写明，但“写在规则里”和“每一步都被自动强制执行”不是一回事。当前代码里，研究、组合、渲染、打包这几段最明确；intake 追问和 review-gate 仍偏弱。

## 4. 当前目录和数据布局

当前代码已经把数据和成品拆成四层：

- `travel-data/places/`
- `travel-data/corridors/`
- `travel-data/trips/<trip-slug>/`
- `travel-data/guides/<trip-slug>/`

目录职责如下：

- `places/`：存按地点沉淀的可复用知识。
- `corridors/`：存城市到城市的交通走廊知识。
- `trips/`：存单次行程的请求、规划和快照。
- `guides/`：存最终 HTML 成品、分享页、打包物和验证结果。

对应脚本：

- `scripts/travel_paths.py`
- `scripts/persist_research_knowledge.py`
- `scripts/build_trip_snapshots.py`

## 5. intake 阶段

### 5.1 当前设计目标

规则里要求 intake 至少确认这些信息：

- 出发城市
- 目的地
- 日期范围
- 出行人数
- 是否有小孩
- 大致年龄段
- 预算
- 交通偏好
- 住宿偏好
- 行程节奏
- 是否接受中转停留
- 是否需要桌面端、手机端、单文件、ZIP、来源说明

对应参考：

- `references/research-checklists.md`
- `agents/openai.yaml`

### 5.2 当前实际实现

`scripts/normalize_request.py` 负责把输入请求标准化，产出：

- `trip_slug`
- `traveler_profile`
- `traveler_constraints`
- `sample_reference`
- `required_topics`
- `share_mode`
- `review_mode`
- `data_layout`

### 5.3 当前规则

- 默认分享模式：`single-html`
- 默认 review 模式：`manual-gate`
- 默认样本引用：`sample.html`
- 旅客约束会从 `children` 和 `age_notes` 推导
- 会记录缺失字段，但不会自动中止流程

### 5.4 当前边界

这是 intake 阶段最大的现实问题：

- 代码会记录 `missing_core_fields`
- 但不会强制“缺字段先追问”
- 所以它更像“标准化器”，还不是“强门禁 intake”

## 6. research-plan 阶段

### 6.1 当前职责

`scripts/build_research_tasks.py` 会按“地点 x 主题 x 站点”展开任务矩阵。

默认主题包括：

- `weather`
- `clothing`
- `packing`
- `long_distance_transport`
- `city_transport`
- `attractions`
- `tickets_and_booking`
- `food`
- `lodging_area`
- `seasonality`
- `risks`
- `sources`

### 6.2 当前站点规则

当前代码已经把多源采集要求写成矩阵，核心站点包括：

- `official`
- `history`
- `map`
- `xiaohongshu`
- `douyin`
- `bilibili`
- `meituan`
- `dianping`

### 6.3 当前必须采集字段

不同主题有不同字段要求。例如：

- 天气：`summary`、`checked_at`
- 长途交通：`schedule`、`price_range`、`latest_searchable_schedule`
- 景点：`price_range`、`reservation_rules`
- 美食：`shop_name`、`address`、`recommended_dishes`
- 社媒：`comment_highlights`
- 视频：`transcript`、`timeline`、`shot_candidates`

### 6.4 当前规则

- 社媒任务要求带评论区摘要
- 抖音和 B 站要求带视频转写、时间轴、截图候选
- 长途交通要求支持“未来未开售时使用最近可查班次”

### 6.5 当前边界

- 这里只是“任务合同”，不等于每个平台都能稳定抓到
- 失败字段允许标记失败，不允许假装采集成功

## 7. research-run 阶段

### 7.1 当前职责

`scripts/build_web_research_runs.py` 会把研究任务转换成面向 `web-access` 的具体 prompt。

### 7.2 当前硬规则

- 所有联网采集必须通过 `web-access`
- 不能只写“social platform summary”
- 必须带具体站点和站内查询词
- 必须记录原始链接
- 必须记录 `checked_at`
- 必须记录失败原因

### 7.3 当前 prompt 形态

每条 run 至少包含：

- `skill: web-access`
- `task`
- `prompt`

prompt 中会明确要求：

- 打开具体页面而不是平台总结页
- 提取正文摘要
- 抽结构化事实
- 读评论
- 视频页抓转写和时间轴

### 7.4 当前边界

当前 skill 只负责生成研究运行合同，不包含真正的“浏览器级执行器”。这意味着：

- 规则是明确的
- 编排是明确的
- 但真正执行是否成功仍取决于 `web-access` 和具体站点状态

## 8. review-gate 阶段

### 8.1 当前职责

当前 review-gate 主要靠这些文件支撑：

- `scripts/validate_site_coverage.py`
- `scripts/generate_review_packet.py`

### 8.2 当前规则

会检查这些主题的站点覆盖：

- `food`
- `attractions`
- `risks`

例如：

- 美食要求覆盖 `meituan`、`dianping`、`xiaohongshu`
- 景点要求覆盖 `official`、`xiaohongshu`、`douyin`、`bilibili`

### 8.3 当前边界

- 当前 review-gate 主要是“站点覆盖检查”
- 还不是“内容质量审校门禁”
- 也不会自动阻断所有弱内容进入发布阶段

## 9. 研究数据沉淀阶段

### 9.1 当前职责

`scripts/persist_research_knowledge.py` 负责把研究结果沉淀到长期复用目录。

### 9.2 当前输出

每个地点目录会写出：

- `raw-web-research.json`
- `structured-facts.json`
- `media-raw.json`
- `site-coverage.json`

每条交通走廊会写出：

- `transport.json`

### 9.3 当前规则

- 有 `place` 的事实进入 `places/`
- 有 `from/to` 的事实进入 `corridors/`
- trip 级关联快照由 `build_trip_snapshots.py` 生成

### 9.4 当前边界

- 目录分层已经实现
- 但目录名目前默认用 slug
- 不是中文目录名

## 10. planning 阶段

### 10.1 当前职责

当前规划相关脚本主要是：

- `scripts/build_trip_planning.py`
- `scripts/build_guide_model.py`

### 10.2 当前已落地部分

`build_guide_model.py` 已经实现了以下规则：

- 提取旅客约束
- 根据距离启用 `600km` 规则
- 生成高铁优先和空铁联运路线卡
- 生成穿衣、景点、美食、交通、提示、来源等 section
- 对部分负向文案做温和化替换

### 10.3 当前规划规则

- 可输出 `daily-overview`
- 可输出 `recommended`
- 可输出 `comprehensive`
- 默认把“高铁优先”作为首选
- 距离大于 `600km` 时补充空铁联运和纯高铁备选
- 未来车票未开售时，可引用最近可售日并标注核对语境

### 10.4 当前最大缺口

`build_trip_planning.py` 目前还是样例级实现，不是通用规划器：

- 主方案只写了 1 天
- 文案里写死了延吉、长白山等场景
- 多方案并没有真正生成独立逐日内容
- 更像一个 demo，而不是可靠规划引擎

### 10.5 当前每日安排生成逻辑

如果 payload 里带了 `planning.route_main.days`，`build_guide_model.py` 会优先用它渲染每日安排。

如果没有，就会退回到“从景点和餐饮事实拼接出 1 到 3 天的占位式日程”。

这意味着：

- 当前已经支持“planning 优先”
- 但如果 planning 不完整，仍会退回弱日程

## 11. clothing、景点、美食、提示阶段

### 11.1 已实现规则

#### 穿衣与装备

- 会合并 `weather`、`seasonality`、`clothing`、`packing`
- 会输出旅客节奏提醒
- 会输出“出行时机”卡

#### 景点

- 支持费用、预约、建议时长
- 支持评论摘录
- 支持来源元数据

#### 美食

- 支持店名、地址、风味、推荐菜、排队提示、备选店
- 当店铺较多时会先生成“城市 + 风味概览卡”

#### 提示

- 支持风险事实卡
- 支持天气提醒
- 支持旅客节奏提醒

### 11.2 当前边界

- 美食虽然有分组，但还不是严格的“按城市 -> 按菜系 -> 按店铺”三级结构
- 景点详情还没有按“山岳/博物馆/园林”做专属深挖模板
- 历史均温字段目前只在研究合同里出现，组合层没有形成特别稳的结构化展示

## 12. 媒体和视频阶段

### 12.1 当前职责

相关脚本包括：

- `scripts/collect_media_candidates.py`
- `scripts/validate_media_assets.py`
- `scripts/extract_video_assets.py`
- `scripts/build_image_plan.py`

### 12.2 当前已实现规则

- 如果媒体只有文字来源，没有关键帧，则标记为 `text-citation-only`
- 只有可发布媒体才允许进入图像计划
- 渲染层会跳过 `text-citation-only` 的封面和 section 媒体

### 12.3 当前发布状态

当前媒体状态分为：

- `hero-ready`
- `illustrative-media`
- `text-citation-only`
- `blocked`

### 12.4 当前环境探测

`extract_video_assets.py` 只会检测：

- `ffmpeg` 是否存在
- `whisper` 是否存在

并写出：

- `ffmpeg_ready`
- `whisper_ready`
- `transcript_status`
- `keyframe_status`

### 12.5 当前边界

这里要特别明确：

- 当前只是“状态门禁”和“依赖探测”
- 还不是真正的视频下载、抽帧、转写流水线
- 所以“可读取评论区、转写语音、抽关键帧做插图”现在只算部分实现

## 13. render 阶段

### 13.1 当前职责

`scripts/render_trip_site.py` 负责把内容模型渲染成桌面端和移动端页面。

### 13.2 当前模板规则

当前固定发布五套模板：

- `route-first`
- `decision-first`
- `destination-first`
- `transport-first`
- `lifestyle-first`

### 13.3 当前已实现规则

- 桌面端和移动端共用同一事实集
- 页面语言是中文
- 支持五套模板批量输出
- 支持来源页 `sources.html`
- 支持来源 Markdown `sources.md`
- 支持封面媒体和 section 媒体的安全渲染

### 13.4 当前模板现实

虽然数量已经固定为 5 套，但现在模板差异主要体现在：

- section 排序
- 字体主题
- 配色和局部布局

它们还不算“5 套完全不同的作品级阅读体验”，更像“5 种编排风格”。

## 14. share 和 package 阶段

### 14.1 当前已实现产物

当前代码会产出：

- `portal.html`
- `recommended.html`
- `share.html`
- `package.zip`
- `trip-summary.txt`

### 14.2 当前规则

- `share.html`：优先转发的完整单文件
- `recommended.html`：较轻量的路线优先单文件
- `portal.html`：总入口
- `package.zip`：整包归档和分享

### 14.3 当前实现方式

- `scripts/export_single_html.py` 会把 CSS 和 JS 内联到单文件
- `scripts/build_portal.py` 会生成统一入口
- `scripts/package_trip.py` 会把关键文件打进 ZIP

### 14.4 当前边界

- 当前有“单文件分享”能力
- 但还没有“自动发布到静态 URL”的通用交付能力
- `static-url` 仍停留在规则层，不是现成脚本能力

## 15. verify 阶段

### 15.1 当前职责

`scripts/verify_trip.py` 负责做静态检查。

### 15.2 当前已实现检查项

- `all_primary_text_in_zh`
- `no_sample_reference_in_publish`
- `no_fake_media_blocks`
- `exactly_five_templates`

### 15.3 当前会拦截的问题

- 页面中出现 `对标样本`
- 页面中出现 `sample.html`
- 页面中出现 `B站搜索：`
- 页面中出现 `抖音搜索：`
- 页面中出现 `来源参考：`
- 桌面端模板数量不是固定 5 套

### 15.4 当前边界

- 这是静态文本检查
- 不是浏览器渲染检查
- 也不是完整 schema 校验
- skill 文档里要求的 Playwright 级验证，目前还没有在这条脚本链里真正落地

## 16. 当前 Python 和环境规则

`SKILL.md` 里已经写入以下环境偏好：

- 优先使用现有 conda 环境
- 当前偏好环境：`py313`
- Playwright 场景偏好环境：`paper2any`
- 依赖缺失时建议走清华镜像安装

### 当前边界

这些规则目前主要是说明文字，没有形成统一的环境探测和自动激活脚本。

## 17. 当前硬规则汇总

当前代码和 skill 说明里，可以视作硬规则的内容有：

- 所有联网采集通过 `web-access`
- 时间敏感事实保留 `checked_at`
- 高铁优先
- 超过 `600km` 补空铁联运和纯高铁备选
- 未来未开售时使用最近可查班次并标注上下文
- 桌面端和移动端使用同一事实集
- 固定只发布五套模板
- 默认输出单文件分享和 ZIP
- 视频没有真实可发布媒体时降级为文字引用
- 发布页不应出现 `对标样本` 和伪媒体文本

## 18. 当前软规则汇总

当前组合层里已经存在一些软规则：

- 文案尽量用温和表达
- 有老人或小孩时，节奏更松、少走长段
- 多人同行时，打车短接驳更省心
- 城市公交和地铁适合作为接驳补位

这些规则更像内容生成偏好，不属于强校验门禁。

## 19. 已确认缺口

到 2026-04-13 这次审查为止，仍明确存在以下缺口：

- intake 缺少强门禁追问
- 通用逐日规划器未完成
- 多方案仍不够独立
- 历史均温和最佳观赏期展示不够结构化
- 美食城市分层还不够彻底
- 视频解析只完成了门禁和依赖探测
- `frontend-design`、`theme-factory` 等 skill 的协同主要停留在规则层
- verify 仍偏静态，未形成完整浏览器验证链

## 20. 使用这份 skill 时应有的预期

当前更合理的使用预期是：

- 它已经具备“多源研究合同 + 数据沉淀 + 中文攻略渲染 + 分享打包”的骨架
- 适合继续迭代成稳定的旅行攻略生产链
- 但还不能把“所有目标需求都已实现”当成事实

如果后续要继续完善，应优先补这四段：

1. 强门禁 intake
2. 通用逐日规划器
3. 真实视频解析流水线
4. 更强的发布验证链

