# Travel Skill 内建联网与视频结构化设计

日期：2026-04-13

范围：`[.codex/skills/travel-skill](/d:/vscode/hello-world/.codex/skills/travel-skill)`、`[.codex/skills/web-access](/d:/vscode/hello-world/.codex/skills/web-access)`

状态：已完成设计讨论，待 Captain 审核

## 背景

当前 `travel-skill` 把联网研究能力外包给独立的 `web-access` skill。这个拆分在概念上清晰，但在实际执行上已经出现稳定性问题：

- `travel-skill` 的研究链路依赖 `web-access` 正常触发，否则在线采集直接断裂。
- 即使 `web-access` 成功拿到视频页面或媒体链接，也没有把视频稳定转成可复用的结构化研究数据。
- 现有 `travel-skill` 已经有媒体与视频相关脚本，但职责不完整，缺少统一的回退策略和标准产物定义。
- 站点模式、CDP 流程、媒体失败记录、页面与视频信息合并策略分散在两个 skill 之间，维护边界不稳。

用户要求把 `web-access` 融入 `travel-skill`，并把视频研究补到“可结构化入库”的程度，最终删除独立的 `web-access` 目录。

## 目标

1. 让 `travel-skill` 自带联网研究能力，不再把在线采集声明为外部 skill 依赖。
2. 把网页研究、站点模式、CDP 访问、失败降级和视频回退链整合到一个 skill 里。
3. 对视频来源建立稳定的结构化 JSON 主产物，而不是停在“抓到视频页面”或“下载到文件”。
4. 明确页面直采、视频回退、失败降级三种路径的判定规则和产物合同。
5. 在确认无活跃引用后删除 `web-access` 目录。

## 非目标

1. 不在本轮重做 `travel-skill` 的整条渲染与发布链路。
2. 不在本轮扩展成通用互联网采集平台；能力边界仍以旅行研究为中心。
3. 不承诺所有视频平台都能无条件下载；失败必须被记录和暴露。
4. 不重写现有所有媒体脚本；优先复用并补齐职责边界。

## 总体设计

### 设计原则

- 单一入口：`travel-skill` 既负责旅行研究编排，也负责研究数据获取。
- 结构化优先：页面或视频都要尽量落成标准 JSON，再交给后续事实抽取与内容组合。
- 失败显式化：任何站点覆盖失败、视频下载失败、转录失败都必须有状态和原因，不能伪装成“已覆盖”。
- 页面优先：先利用网页可直接拿到的结构化信息，只有证据不足时才进入视频回退链。
- 复用现有资产：优先吸收 `web-access` 的脚本和 references，优先复用 `travel-skill` 里已存在的媒体处理脚本。

### 合并后的职责边界

`travel-skill` 新增并内建以下职责：

- 搜索与网页访问策略
- CDP 浏览器接入与页面操作
- 站点模式识别与经验沉淀
- 页面证据抽取
- 视频回退下载、抽帧、转录、结构化
- 研究覆盖状态判定与失败记录

以下能力仍保持外部协同，不并入：

- `frontend-design`
- `ui-ux-pro-max`
- `theme-factory`
- `verification-before-completion`
- `playwright-skill` 或仓库内浏览器验证脚本

## 目录设计

### Travel Skill 内新增或吸收的资产

`travel-skill` 应吸收 `web-access` 的核心资产，并在自己的目录下统一维护：

- `references/cdp-api.md`
- `references/site-patterns/`
- `references/video-research-contract.md`
- `scripts/check-web-deps.mjs`
- `scripts/cdp-proxy.mjs`
- `scripts/match-site.mjs`

为视频结构化链新增脚本入口，命名可以与现有脚本风格保持一致：

- `scripts/download_video_media.py`
- `scripts/transcribe_video_media.py`
- `scripts/segment_video_media.py`
- `scripts/build_video_research_json.py`

如现有脚本已覆盖其中部分职责，则不重复创建，改为在现有脚本上扩充并在 spec 落实边界：

- `scripts/collect_media_candidates.py`
- `scripts/extract_video_assets.py`
- `scripts/validate_media_assets.py`

### Web Access 目录的去留

`[.codex/skills/web-access](/d:/vscode/hello-world/.codex/skills/web-access)` 在迁移完成前暂时保留，用于对照和防止中途断链。只有满足下面条件后才删除：

- `travel-skill` 文档已改为内建联网能力
- 所需脚本与 references 已迁入
- 全仓活跃执行路径不再引用旧目录
- 至少完成一轮基本验证

## 研究执行流

合并后的 `research-run` 调整为固定判定链：

1. 页面直采
2. 结构化充分性判定
3. 视频回退
4. 页面与视频证据合并
5. 结构化 JSON 落盘
6. 覆盖状态与失败原因记录

### 1. 页面直采

对网页或视频页，优先获取：

- 页面标题
- 作者或发布主体
- 发布时间
- 页面正文
- 标签、简介、置顶说明
- 评论高频点
- 页面可直接提供的 transcript 或 timeline
- 截图候选
- 视频元数据，例如时长、封面、可用媒体 URL

### 2. 结构化充分性判定

若页面直采已经满足最小研究合同，可直接产出 `page-only` 结构化 JSON，不必进入下载链。最小合同至少包含：

- 可识别来源
- 标题或主题
- 发布时间或可替代时间上下文
- 核心内容摘要
- 至少一组可引用的证据字段

### 3. 视频回退触发条件

满足任一条件时进入视频回退链：

- 页面正文不足以支持事实抽取
- 页面没有可用 transcript 或时间线
- 需要画面证据、口播内容或关键帧
- 页面抓取失败，但媒体 URL 可取得
- 平台是视频主导型内容，且目标字段在页面层缺失

### 4. 视频回退链

视频回退链的标准顺序：

1. 尝试通过页面、播放器元素或平台元数据拿到媒体地址
2. 优先使用 `yt-dlp` 下载视频或音频
3. 使用 `ffmpeg` 产出音频、关键帧或定时截图
4. 使用 `whisper` 生成带时间戳的转录
5. 由 Codex 把页面信息、转录、关键帧观察、评论摘要合并成标准 JSON

### 5. 失败降级

若视频链部分失败，允许降级，但必须保留状态：

- 页面可用而视频不可用：产出 `partial` JSON，并记录媒体失败原因
- 视频已下载但转录失败：保留页面信息与媒体文件信息，记录转录失败
- 页面和视频都不足：标记 `failed`，不得伪装成站点已覆盖

## 视频结构化 JSON 合同

视频研究的默认主产物是 JSON，建议最小字段如下：

- `source_url`
- `platform`
- `collected_at`
- `collector_mode`
- `coverage_status`
- `failure_reason`
- `author`
- `title`
- `publish_time`
- `duration_sec`
- `page_text`
- `comment_highlights`
- `transcript_segments`
- `visual_segments`
- `timeline`
- `claims`
- `travel_facts`
- `travel_tips`
- `risk_notes`
- `evidence_links`
- `media_artifacts`

### 字段语义

- `collector_mode` 只能使用 `page-only`、`page+video`、`video-fallback`
- `coverage_status` 只能使用 `complete`、`partial`、`failed`
- `failure_reason` 在 `partial` 或 `failed` 时必填
- `media_artifacts` 记录实际落盘的媒体文件、抽帧、转录文件
- `transcript_segments` 必须带时间信息；没有时间信息则不可伪装成完整转录
- `visual_segments` 用于记录关键帧或画面观察结果，不与转录混写

## 文档与 Skill 合同调整

### SKILL.md

`[.codex/skills/travel-skill/SKILL.md](/d:/vscode/hello-world/.codex/skills/travel-skill/SKILL.md)` 需要从“协调 `web-access`”改成“内建联网研究能力”，至少包含：

- `travel-skill` 默认负责所有在线研究
- 页面直采优先，视频回退为默认降级链
- 需要视频结构化时使用 `yt-dlp`、`ffmpeg`、`whisper` 和 Codex 分析
- 若依赖缺失、下载失败或提取失败，必须显式记录并暴露问题
- 删除 “Use `web-access` for all online collection” 之类的外部依赖要求

### References

`travel-skill` 内的 references 调整为：

- `web-access-research-contract.md` 改写为 skill 内部研究合同，不再把能力归属给外部 skill
- 新增 `video-research-contract.md`，专门约束视频回退与 JSON 结构
- `site-patterns/` 迁入后继续作为站点经验库
- `cdp-api.md` 迁入后成为内建浏览器操作参考

## 脚本边界

### Node / CDP 脚本

迁入后的 Node 脚本职责：

- `check-web-deps.mjs`：检查 Node、Chrome remote debugging、CDP proxy 就绪状态
- `cdp-proxy.mjs`：提供页面导航、点击、评估、截图等代理能力
- `match-site.mjs`：匹配站点模式与站点经验文档

### Python / 媒体脚本

Python 脚本职责：

- 下载媒体
- 生成音频与关键帧
- 调用转录能力
- 把页面证据和媒体证据归并成 JSON

现有脚本如能承接这些职责，应优先扩展，而不是平行创建新脚本。

## 环境与依赖策略

遵守仓库现有规则：

- 优先复用已有 conda 环境
- Python 默认优先 `py313`
- 若后续浏览器验证需要专用环境，再按当时机器实际情况选择
- 若 `yt-dlp`、`ffmpeg`、`whisper` 缺失，先检查现有环境与可执行文件，再决定是否安装
- 依赖缺失不能被静默吞掉，必须在研究结果或验证结果里说明

## 迁移计划

### 阶段 1：文档与合同内聚

- 更新 `SKILL.md`
- 更新 `web-access-research-contract.md`
- 新增 `video-research-contract.md`
- 调整 `travel-skill` 中所有“调用 `web-access`”的表述

### 阶段 2：脚本与 references 迁入

- 迁入 `cdp` 相关脚本
- 迁入 `site-patterns`
- 修正相对路径和目录假设

### 阶段 3：视频结构化链补齐

- 明确复用现有媒体脚本还是新增脚本入口
- 把下载、抽帧、转录、JSON 归并串成稳定流程
- 明确失败状态和降级结果

### 阶段 4：验证与删除旧 skill

- 全仓搜索旧引用
- 执行基本验证
- 删除 `web-access` 目录

## 验收标准

满足以下条件才算完成：

1. `travel-skill` 的 `SKILL.md` 已声明内建联网能力，不再依赖外部 `web-access`
2. `travel-skill` 目录下已具备网页研究所需脚本和 references
3. 视频来源存在标准 JSON 结构化合同
4. 研究结果能区分 `complete`、`partial`、`failed`
5. 页面证据不足时存在明确的视频回退链
6. 全仓不存在对旧 `web-access` 路径的活跃执行引用
7. 删除旧目录后至少一轮基础验证通过，或未通过项被明确记录

## 验证策略

至少执行以下验证：

- 引用验证：全仓搜索 `web-access`，确认活跃执行路径已切换
- 文档验证：`travel-skill` 内部 references 和脚本入口引用闭合
- 脚本验证：迁入后的 Node/CDP 脚本仍可启动或至少通过依赖检查
- 合同验证：至少准备一个网页样本和一个视频样本，确认能产出符合合同的结构化 JSON

## 风险与缓解

### 风险 1：迁入后脚本路径失效

缓解：

- 迁入时同步修正脚本中的相对路径
- 先做依赖检查和入口调用验证，再删除旧目录

### 风险 2：视频链依赖在本机不完整

缓解：

- 实施前先检查现有 conda 环境和可执行文件
- 缺失时显式记录，不假装“已支持”

### 风险 3：与现有媒体脚本职责冲突

缓解：

- 先梳理 `collect_media_candidates.py`、`extract_video_assets.py`、`validate_media_assets.py` 的现有边界
- 优先扩展现有脚本，避免并列重复实现

### 风险 4：旧目录删除过早导致中断

缓解：

- 严格按阶段执行，删除放最后
- 删除前做全仓引用搜索和基础验证

## 完成定义

以下条件同时成立时，本设计视为落地完成：

1. `travel-skill` 已成为单一旅行研究入口
2. 网页采集与视频结构化链都已纳入同一 skill
3. 失败状态和降级路径被显式记录
4. 旧 `web-access` 目录已安全删除
5. 基本验证结果已记录，未验证项被如实说明
