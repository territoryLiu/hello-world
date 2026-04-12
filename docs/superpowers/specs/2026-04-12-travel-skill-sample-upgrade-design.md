# Travel Skill Sample Upgrade Design

**目标**

把 `travel-skill` 从“能生成基础攻略”提升到“能按样本密度稳定产出可选设计版本、复用 research 资产、并明确社媒评论区证据”的版本。

**范围**

1. 高铁未开售时，允许使用最近可售日班次作为稳定参考。
2. `xiaohongshu / douyin / bilibili` 的 research 合同必须显式要求评论区抓取结果。
3. research 数据除 trip 目录外，还要沉淀到固定复用目录。
4. 渲染层必须把 `classic / minimalist / original / vintage / zen` 五套模板全部输出。
5. 攻略内容结构要向 `E:\延吉\sample.html` 靠拢，增强 Hero、交通决策、每日执行表、美食备选与来源分组。

**非目标**

1. 不在这一轮里实现真实联网抓取器本身。
2. 不重写整个 compose / render 系统。
3. 不把样本 HTML 做像素级复刻。

## 现状问题

1. `build_research_tasks.py` 只要求正文摘要，评论区没有进入强制合同。
2. `build_web_research_runs.py` 只输出一句泛化 prompt，缺少“正文 + 评论区 + 时间轴 + 失败原因”的约束。
3. research 产物只在单次 trip 目录里使用，没有固定知识库位置。
4. `render_trip_site.py` 虽然接受 `style` 参数，但一次只渲染一种风格。
5. `build_portal.py` 只按设备和层级组织，不按风格组织。
6. 当前 guide model 信息密度偏低，距离样本里的“编辑型攻略页”还有明显差距。

## 设计决策

### 1. Research 合同增强

- 在 topic-site 规则中，为社媒站点统一补充：
  - `comment_highlights`
  - `comment_capture_status`
  - `comment_sample_size`
  - 对视频站点继续保留 `transcript / timeline / shot_candidates`
- 长途交通任务增加：
  - `latest_searchable_schedule`
  - `fallback_strategy`
  - `checked_date_context`

### 2. 高铁最近可售日兜底

- 在 guide model 的交通卡片组装中，若 fact 含 `fallback_strategy=latest-searchable-date`，正文明确写：
  - 当前目标日未开售
  - 使用最近可售日班次作时间参考
  - 因高铁班次稳定，正式售票后以 12306 复核为准

### 3. 固定复用存储

- 新增 repo 级路径：
  - `travel-data/places/<place-slug>/raw-web-research.json`
  - `travel-data/places/<place-slug>/structured-facts.json`
  - `travel-data/places/<place-slug>/media-raw.json`
  - `travel-data/places/<place-slug>/site-coverage.json`
- 新增脚本负责把 trip research 按 place 切分写入固定目录。

### 4. 多风格渲染

- `render_trip_site.py` 支持一次生成多个 style。
- 目录结构改为：
  - `desktop/<style>/<layer>/index.html`
  - `mobile/<style>/<layer>/index.html`
- 单文件导出支持指定 style。
- `portal.html` 按风格展示五套桌面端、手机端、单文件链接。

### 5. 内容密度增强

- 在 compose 阶段补入更强的结构：
  - hero 快速结论
  - transport matrix
  - daily execution cards
  - food backup matrix
  - grouped source blocks
- 如果 intake 提供绝对路径样本，保留到 `meta.sample_reference.path` 并在渲染层显式展示。

## 影响文件

- `docs/superpowers/plans/2026-04-12-travel-skill-sample-upgrade.md`
- `.codex/skills/travel-skill/SKILL.md`
- `.codex/skills/travel-skill/scripts/normalize_request.py`
- `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- `.codex/skills/travel-skill/scripts/build_web_research_runs.py`
- `.codex/skills/travel-skill/scripts/build_guide_model.py`
- `.codex/skills/travel-skill/scripts/render_trip_site.py`
- `.codex/skills/travel-skill/scripts/build_portal.py`
- `.codex/skills/travel-skill/scripts/export_single_html.py`
- `.codex/skills/travel-skill/scripts/package_trip.py`
- 新增 `.codex/skills/travel-skill/scripts/persist_research_knowledge.py`
- `tests/travel_skill/test_intake_research.py`
- `tests/travel_skill/test_render_package.py`
- 可能新增 `tests/fixtures/travel_skill/*`

## 验收标准

1. research task / run 中能看到评论区抓取字段与提示。
2. 交通事实支持“最近可售日班次”兜底。
3. trip research 能同步落到固定 `travel-data/places/` 目录。
4. 五套风格一次性生成，portal 可选。
5. 单文件导出和 ZIP 打包覆盖五套风格中的指定版本。
6. 测试覆盖新增行为并通过。
