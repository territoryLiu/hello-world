# Travel Skill 冗余清理与规则收敛设计

日期：2026-04-13
范围：`.codex/skills/travel-skill`
状态：已获用户口头批准，待书面 spec 复核

## 背景

当前 `travel-skill` 存在三类问题：

1. 同一业务规则在多个位置重复维护，已经出现漂移。
2. 模板目录里存在当前主渲染路径不再引用的历史文件。
3. `SKILL.md`、`agents/openai.yaml`、`references/` 对输出结构、section 顺序、研究字段和交付物做了多点展开，维护成本高，且已经出现陈旧内容。

已确认的漂移包括：

- 长距离交通阈值在 `SKILL.md` 和运行时配置中是 `1000km`，但 `agents/openai.yaml` 仍写 `600km`。
- 输出路径主实现已写入 `guides/<slug>/...`，但部分 reference 仍保留旧的 `trips/<slug>/...`。

## 目标

1. 为 travel-skill 建立清晰的单一事实源。
2. 删除当前实现路径上无引用的旧模板和旧页面壳。
3. 将入口文档、reference 文档、运行时配置各自职责收紧，避免再次分叉。
4. 用测试或一致性检查约束关键规则，避免未来再次漂移。

## 非目标

1. 不重写 travel guide 的业务模型。
2. 不重做当前五套 `*-first` 模板的视觉实现。
3. 不重构整条研究、组合、渲染流水线的接口。
4. 不为了“极致去重”牺牲可读性；允许存在摘要，但不允许存在第二份权威定义。

## 单一事实源设计

### 运行时权威源

`scripts/travel_config.py` 作为脚本直接消费的唯一常量源，负责：

- 长距离交通阈值
- 模板 ID 集合
- 模板标签
- 模板 section mapping
- 发布产物文件名

运行时代码不再在别处手写这些值。

### 文档权威源

`references/` 中只保留少量权威文档：

- `content-schema.md`
  - 唯一负责字段、层级和 section 结构说明
- `sharing-modes.md`
  - 唯一负责输出布局、分享产物和发布路径说明
- `web-access-research-contract.md`
  - 唯一负责 research run 的任务字段、持久化字段和联网采集约束
- `source-priority.md`
  - 唯一负责来源优先级和时间敏感事实写法
- `research-checklists.md`
  - 仅保留人工 review 清单，不再重复规范定义

### 入口文档

`SKILL.md` 收紧为入口文档，只保留：

- 何时使用本 skill
- 默认交付物摘要
- 执行顺序
- 必须协同调用的其他 skills
- 若干关键硬规则
- 指向 reference 和脚本入口的跳转

`SKILL.md` 不再完整展开字段表、输出树、section 顺序、完整站点字段列表。

### Agent 提示

`agents/openai.yaml` 收紧为极短执行合同，只保留：

- 先 intake，再 research，再 review，再 compose/render/verify
- 必须使用 concrete site coverage
- 必须在 review 前显式暴露缺失 coverage
- 关键权威参考所在位置

`agents/openai.yaml` 不再重复距离阈值、完整字段表或模板完整列表。

## 删除范围

计划删除当前主路径未使用的历史模板和页面壳：

- `assets/templates/guide-template-classic.html`
- `assets/templates/guide-template-minimalist.html`
- `assets/templates/guide-template-original.html`
- `assets/templates/guide-template-vintage.html`
- `assets/templates/guide-template-zen.html`
- `assets/templates/desktop-index.html`
- `assets/templates/mobile-index.html`
- `assets/templates/mobile-classic.html`
- `assets/templates/mobile-minimalist.html`
- `assets/templates/mobile-original.html`
- `assets/templates/mobile-vintage.html`
- `assets/templates/mobile-zen.html`

删除前提：

- 仓库内搜索确认无运行时代码引用。
- 删除后相关测试和渲染检查仍通过。

如果发现这些文件只在人工流程中被引用，而不在代码中被引用，则不恢复旧文件，而是在文档中明确是否正式废弃。

## 结构调整

### `SKILL.md`

处理方式：

- 保留 Purpose、Execution Order、协同 skill 要求。
- 把 Guide Contract、Research Rules、Rendering Rules、Verification Rules 只保留高层要求。
- 将详细定义改为“以 reference/config 为准”的指针式写法。

### `references/sharing-modes.md`

处理方式：

- 修正输出路径到 `guides/<slug>/...`
- 只保留当前真实实现的布局和交付物
- 删除和 `content-schema.md` 重复的 ordered sections 定义，改为引用 schema/config

### `references/research-checklists.md`

处理方式：

- 保留 intake、transport、weather、attractions、food、sources、delivery 的 review checklist 价值
- 删除与 `web-access-research-contract.md` 或 `source-priority.md` 重复的规范型陈述

### `agents/openai.yaml`

处理方式：

- 删除 `600km transport rule` 旧说法
- 不再直接展开完整字段和完整 deliverables
- 如果需要提阈值，改为“遵循 runtime config”

## 验证策略

### 一致性测试

增加或调整 travel-skill 相关测试，至少覆盖：

- 距离阈值只来自 `travel_config.py`
- 模板数量固定为五套，渲染器与校验器一致
- reference 中发布路径与当前实现一致

### 渲染回归

至少验证：

- desktop/mobile 五套模板完整
- `notes/sources.md` 和 `notes/sources.html` 存在
- 单文件分享页和打包产物仍按当前约定输出
- 校验器仍能识别无 `sample_reference` 泄漏、无 fake media block

### 删除安全检查

删除历史模板前后都做引用搜索，并在删除后复跑相关测试。

## 实施顺序

1. 在 repo-local `.worktrees/` 中创建隔离工作树。
2. 先补失败测试或一致性检查，确认当前问题可被测试捕获。
3. 收紧 `SKILL.md`、`references/`、`agents/openai.yaml`。
4. 删除未引用旧模板。
5. 运行相关测试和回归检查。
6. 整理残余风险并回报。

## 风险与缓解

### 风险 1：旧模板被人工流程隐式依赖

缓解：

- 删除前做仓库范围搜索
- 删除后跑回归
- 如果确认存在人工依赖，则改为文档化废弃或显式迁移说明

### 风险 2：文档去重后可读性下降

缓解：

- `SKILL.md` 保留摘要和跳转，不让用户一上来只能看碎片 reference
- 每个 reference 只负责一类信息，避免再次碎片化

### 风险 3：测试只覆盖代码，不覆盖文档一致性

缓解：

- 增加专门的一致性检查，显式验证关键文档和运行时配置未再分叉

## 完成标准

满足以下条件才算完成：

1. 不再存在 `600km/1000km` 这类规则漂移。
2. 当前主路径未使用的旧模板和页面壳已删除。
3. `SKILL.md`、`agents/openai.yaml`、`references/` 的职责边界清晰。
4. 相关测试和回归检查通过，或未通过项被明确说明。
