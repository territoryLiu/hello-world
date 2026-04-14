# travel-skill 单模板杂志式 render 重构方案

日期：2026-04-14  
状态：draft  
范围：render 体系重构，保留现有输出目录结构，移除旧五模板默认架构

## 1. 背景

上一轮改造已经让 `travel-skill` 在 skill 文档层具备了独立的高端旅游杂志式 HTML 设计基线，但实际渲染链路仍停留在旧体系：

- `travel_config.py` 仍定义五个模板 ID；
- `render_trip_site.py` 仍按五模板批量渲染；
- `assets/templates/` 仍以内置五模板 HTML 为核心；
- `build_portal.py`、`verify_trip.py`、`package_trip.py` 仍默认假设“五模板都存在”。

用户本轮要求更激进：**直接拆掉现有五模板体系，render 只剩新的单一模板输出**。同时，用户又明确要求：

- **目录结构不变**；
- 后续仍可能扩充风格模板。

因此，本轮要做的是：**保留模板目录形态，但移除旧五模板架构和联动假设，改为新的单模板内核。**

## 2. 目标

改造后应满足：

1. `travel-skill` 的实际 render 逻辑只保留一个真实模板；
2. 该模板默认采用高端旅游杂志式阅读体验；
3. 输出目录结构保持不变：
   - `guides/<trip-slug>/desktop/<template-id>/index.html`
   - `guides/<trip-slug>/mobile/<template-id>/index.html`
4. 当前唯一模板 ID 定为 `editorial`；
5. 旧五模板文件、常量、校验假设、门户文案和打包摘要不再作为默认行为存在；
6. 页面内容顺序继续严格遵循 `travel-skill` 的 `Guide Contract`。

## 3. 非目标

本轮不做以下事项：

- 不改动 research / planning / compose 数据模型；
- 不改动 guide 内容 section 顺序；
- 不引入多风格模板选择器；
- 不做地图引擎、动画系统、图片生成器等额外视觉能力；
- 不改变 desktop/mobile 双端都要产出的事实一致性要求。

## 4. 设计原则

### 4.1 单模板内核，不做旧体系兼容假象

这次不是“保留五模板名，但内部偷偷指向同一个模板”，而是明确去掉旧五模板体系。配置、渲染、验证、门户、摘要都要说真话：**当前只有一个模板**。

### 4.2 保留目录契约，释放未来扩展空间

虽然当前只有 `editorial` 一个模板，但仍保留 `<device>/<template-id>/index.html` 目录约定。这样未来新增 `minimal`、`photo-story` 等新模板时，无需再改路径协议。

### 4.3 内容顺序高于视觉变化

新模板可以彻底换版，但 section 顺序不能突破现有 `Guide Contract`。允许通过封面、导语、时间轴、引文块、比较块等方式增强叙事，不允许重排章节。

### 4.4 清理联动假设，而不是只改 render 一个文件

如果只改 `render_trip_site.py`，而 `portal`、`verify`、`package` 仍写死“五模板存在”，整条链路会断。因此这次必须做跨文件清理。

## 5. 新架构概览

### 5.1 新模板 ID

当前唯一模板 ID 固定为：

- `editorial`

它表示当前默认且唯一的高端旅游杂志式模板。

### 5.2 输出目录

目录结构保持为：

- `guides/<trip-slug>/desktop/editorial/index.html`
- `guides/<trip-slug>/mobile/editorial/index.html`

即保留“模板目录”这一层，但当前只生成 `editorial`。

### 5.3 模板文件组织

建议重构后：

- 删除五个旧模板 HTML 文件；
- 新增一个统一模板文件，例如 `template-editorial.html`；
- `base.css` 按新模板重写或显著收敛；
- `render-guide.js` 保留最小必要功能，不再服务五模板差异。

## 6. 文件级改造方案

### 6.1 `scripts/travel_config.py`

当前问题：

- `TEMPLATE_IDS`、`TEMPLATE_LABELS`、`TEMPLATE_SECTIONS` 全部围绕五模板建立；
- `SORTED_TEMPLATE_IDS` 也隐含“多模板发布”。

改造后应变为：

- `TEMPLATE_IDS = ["editorial"]`
- `SORTED_TEMPLATE_IDS = ["editorial"]`
- `TEMPLATE_LABELS = {"editorial": "杂志版"}`
- `TEMPLATE_SECTIONS = {"editorial": [...]}`，内容顺序必须严格遵守 `Guide Contract`

建议 `editorial` 的 section 顺序定义为：

对于主攻略页：
1. `recommended_route`
2. `route_options`
3. `clothing_guide`
4. `attractions`
5. `transport_details`
6. `food_by_city`
7. `tips`
8. `sources`

如需保留 `daily-overview`，应将其作为单独页面片段或在模板内作为补充块，而不是打乱主 section 顺序。

### 6.2 `scripts/render_trip_site.py`

当前问题：

- 代码按 `template_id` 做多路渲染；
- `STYLE_THEMES` 仍服务五模板差异；
- `_apply_template()` 明确依赖 `template-<id>.html`；
- 当前生成所有模板目录。

改造后应：

1. 删除五模板专用 `STYLE_THEMES` 分流；
2. 保留设备差异，但不再保留模板差异；
3. 新增或收敛为单一 `EDITORIAL_THEME`；
4. `_apply_template()` 只加载 `template-editorial.html`；
5. `render_site()` 只生成 `desktop/editorial/index.html` 与 `mobile/editorial/index.html`；
6. `--style` 参数如继续保留，应仅接受：
   - `editorial`
   - `default`
   - `all`（内部也只映射到 `editorial`）

### 6.3 `assets/templates/`

当前问题：

- 模板目录中保留五个旧 HTML 文件，形成实际架构噪音；
- `base.css` 当前风格仍是模板可切换思路。

改造后应：

- 删除：
  - `template-route-first.html`
  - `template-decision-first.html`
  - `template-destination-first.html`
  - `template-transport-first.html`
  - `template-lifestyle-first.html`
- 新增：
  - `template-editorial.html`
- 视实现情况决定是否保留 `portal.html`；若未使用，可在后续清理
- 重写 `base.css` 使其服务单一杂志式模板

### 6.4 `scripts/build_portal.py`

当前问题：

- 入口文案明确写着“固定只发布五套模板版本”；
- 桌面端/手机端链接组默认按多模板列出。

改造后应：

- 文案改为“当前默认发布杂志版桌面端与手机端”；
- 链接仍从模板目录中枚举，但默认只会枚举到 `editorial`；
- 不再出现“五套模板”“路线优先单文件”等旧话术；
- 单文件区域文案改为：
  - `share.html`：完整单文件分享版
  - `recommended.html`：当前主推荐分享页（如果仍保留）

### 6.5 `scripts/verify_trip.py`

当前问题：

- `desktop_templates_complete` / `mobile_templates_complete` 直接与旧模板列表比较；
- 存在 `exactly_five_templates` 强校验。

改造后应：

- 改为校验桌面端与手机端模板目录都等于 `["editorial"]`；
- 删除 `exactly_five_templates`；
- 新增更真实的校验语义，例如：
  - `desktop_template_complete`
  - `mobile_template_complete`
  - `single_template_is_editorial`
- 保留：
  - 中文正文检查
  - 来源文件存在检查
  - 不含 sample reference / fake media blocks
  - Playwright 感知校验

### 6.6 `scripts/package_trip.py`

当前问题：

- 摘要里仍会枚举旧模板；
- 单文件说明文案带有旧“路线优先版本”语义。

改造后应：

- 摘要中模板字段只记录 `editorial`
- 单文件说明改成：
  - `share.html` 是完整单文件分享版
  - `recommended.html` 是主推荐分享入口（若保留）
- 不再出现“五模板”与“路线优先”默认话术

## 7. 模板内容结构

新 `editorial` 模板必须满足：

### 7.1 内容顺序

主 section 顺序严格遵守：

1. `recommended_route`
2. `route_options`
3. `clothing_guide`
4. `attractions`
5. `transport_details`
6. `food_by_city`
7. `tips`
8. `sources`

### 7.2 可选增强

允许在主 section 之前或之间使用：

- cover / hero
- editorial lead
- meta chips
- route promise
- timeline summary

但这些都只是视觉增强，不构成对 section 顺序的替代。

### 7.3 双端策略

- desktop：强调沉浸感、跨栏、图文节奏
- mobile：强调分段、可滑读、信息层级压缩
- 二者必须共享同一事实集

## 8. 迁移策略

### 8.1 不做“兼容旧模板”中间层

本轮明确不做以下折中：

- 不保留五模板 ID 但内部复用一个模板；
- 不继续生成五个目录壳子；
- 不在 portal/verify 里同时兼容旧新两套逻辑。

### 8.2 一次性替换

替换顺序建议为：

1. 更新 `travel_config.py`
2. 改 `render_trip_site.py`
3. 替换模板资产
4. 改 `build_portal.py`
5. 改 `verify_trip.py`
6. 改 `package_trip.py`
7. 做端到端文档/产物验证

## 9. 风险与缓解

### 风险 1：脚本链路仍有旧模板硬编码

症状：render 看似成功，但 portal、verify、package 任一环节报错或输出错误文案。  
缓解：在实施前用全文搜索找出 `route-first`、`decision-first`、`five templates`、`TEMPLATE_IDS` 相关依赖点，一次清理。

### 风险 2：单模板后 `recommended.html` / `share.html` 语义混乱

症状：单文件产物仍沿用旧“路线优先版”语义。  
缓解：明确 `recommended.html` 是主推荐分享入口，而不是旧模板派生物。

### 风险 3：模板删除后引用路径失效

症状：运行时 `_load_asset()` 或 portal 链接访问失败。  
缓解：先完成代码引用替换，再删除旧模板文件。

### 风险 4：移动端与桌面端节奏差异导致事实不一致

症状：双端视觉不同步，部分 section 漏项。  
缓解：同一数据源、同一 section 列表、只让设备样式差异发生在布局层。

## 10. 验收标准

当本方案完成时，应满足：

1. 仓库中不再存在旧五模板的默认渲染逻辑；
2. `travel_config.py` 只定义 `editorial` 模板；
3. `render_trip_site.py` 只生成 `desktop/editorial` 与 `mobile/editorial`；
4. `build_portal.py`、`verify_trip.py`、`package_trip.py` 不再写死“五模板”语义；
5. 旧五模板 HTML 文件已删除；
6. 输出的 HTML 内容顺序仍符合 `Guide Contract`；
7. 验证脚本通过新的单模板校验逻辑。

## 11. 后续阶段建议

本设计获批后，下一步应进入新的 implementation planning，重点包括：

1. 清点所有旧模板依赖点；
2. 定义 `editorial` 模板的最小可运行 HTML 结构；
3. 改写 render / portal / verify / package；
4. 删除旧模板文件；
5. 跑一轮最小端到端验证，确认目录、门户、打包、校验都能接受单模板输出。
