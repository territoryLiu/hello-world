---
title: Travel Skill V3 Design
date: 2026-04-11
status: approved-in-chat
owner: Codex
---

# Travel Skill V3 Design

## Background

`travel-skill` V2 已经打通了基础链路：

1. 结构化 intake
2. research task 拆分
3. 多源合并与事实抽取
4. review packet 人工确认
5. guide model 生成
6. 桌面端、移动端、单文件、ZIP 和校验产物输出

这一版已经可用，但还存在三类关键差距：

1. 内容合同需要进一步贴近真实出行决策。用户更关心最推荐路线、多方案路线、穿衣、景点、交通、美食和注意事项的固定顺序。
2. 交通策略需要更明确。跨省长距离行程里，高铁的确定性、飞机的速度、中转城市的可玩性都要写入默认规则。
3. 分享方式需要稳定默认值。生成目录工程便于维护，但单文件分享和 ZIP 才是最直接的交付形态。

V3 的目标是把这三点正式写进 skill 合同、参考文档、脚本行为和验证链路里。

## Goals

V3 默认满足以下目标：

1. 使用统一 research 底座，生成三层内容产物：
   - `daily-overview`
   - `recommended`
   - `comprehensive`
2. `recommended` 与 `comprehensive` 固定按以下顺序输出：
   - 最推荐路线
   - 多方案路线
   - 穿衣指南
   - 景点信息
   - 交通详细信息
   - 按城市划分的美食店铺
   - 注意事项和避坑指南
   - 信息来源
3. 桌面端与移动端内容一致，移动端通过分页提升阅读体验。
4. 默认同时交付：
   - 维护型工程目录
   - `portal.html`
   - `recommended.html`
   - `share.html`
   - `package.zip`
   - `verify-report.json`
5. 默认多源采集，正式写入 `web-access`、`frontend-design`、`theme-factory`、`playwright-skill` 的协作边界。
6. 允许 skill 内脚本完整跑通流程，优先使用已有 conda 环境；缺依赖时使用清华 PyPI 镜像补齐。

## Transport Policy

V3 固定采用以下交通策略：

1. 先给高铁方案。
2. 行程距离大于 `600km` 时，再补：
   - `飞机 + 高铁` 组合方案
   - 纯高铁方案
3. 当直达方案弱、时间不合适或班次稀少时，增加中转城市方案。
4. 中转城市方案要写清：
   - 中转城市名称
   - 中转半天或一天是否值得停留
   - 可顺手打卡的代表性内容
5. 对未来尚未开售或尚未放出的班次，正文写最近可查方案、核对日期、预计价格区间，不把未来细节写成确定事实。

## Source Strategy

V3 的默认来源结构分四层：

1. `official`
   - 景区官网
   - 官方公告
   - 12306
   - 航司 / 机场 / 客运站公开入口
2. `platform`
   - Trip / 携程 / 去哪儿等公开交通和酒店页面
3. `local-listing`
   - 大众点评
   - 美团
   - 其他店铺公开页
4. `social`
   - 小红书
   - 抖音
   - 哔哩哔哩

使用原则：

1. 规则、票务、预约、开闭园、车次、航班、天气入口优先官方源。
2. 体验、避坑、排队、出片点、口味反馈和节奏建议由社媒与本地生活平台补充。
3. 每条时效性信息都保留 `checked_at`。
4. 研究原始链接进入 JSON 和来源清单，便于复查和后续复用。

## Guide Contract

### 1. Daily Overview

`daily-overview` 固定包含：

1. `summary`
2. `days`
3. `wearing`
4. `transport`
5. `alerts`
6. `sources`

它的作用是把每天安排放在最前面，适合快速判断每天怎么走、怎么穿、当天重点看什么。

### 2. Recommended

`recommended` 固定包含：

1. `recommended_route`
2. `route_options`
3. `clothing_guide`
4. `attractions`
5. `transport_details`
6. `food_by_city`
7. `tips`
8. `sources`

这层是默认分享给大多数读者的主版本。

### 3. Comprehensive

`comprehensive` 与 `recommended` 使用同一章节顺序，但信息更全，额外容纳：

1. 更多交通备选
2. 更多城市分组餐厅
3. 更完整的景点收费和预约说明
4. 更充分的来源与核对信息

## Share Strategy

V3 把分享优先级固定为：

1. `single-html`
2. `zip-bundle`
3. `static-url`

默认产物说明：

1. `portal.html`
   - 分享入口页
   - 导航到推荐版和全面版
2. `recommended.html`
   - 最推荐攻略的单文件分享版
3. `share.html`
   - 最全面攻略的单文件分享版
4. `package.zip`
   - 包含 share 页面、来源说明和摘要文件

这样做的结果是：

1. 不依赖部署环境就能分享
2. 目录工程继续保留，便于后续补数据和重渲染
3. 单文件适合直接发送给读者

## Skill Coordination

### Required

1. `web-access`
   - 所有联网搜索和网页采集都通过它完成
   - 覆盖官网、交通、天气、社媒、点评和美食平台
2. `frontend-design`
   - 负责最终 HTML 阅读体验
3. `playwright-skill` 或现有 Playwright checker
   - 负责页面渲染验证

### Optional

1. `theme-factory`
   - 当客户需要多套旅行风格主题时启用
2. `visual-explainer`
   - 当需要把 research packet 或流程说明做成可视化页面时启用
3. `last30days`
   - 当旅程依赖近期热度和口碑波动时启用

## Script Policy

V3 继续以内置脚本跑通全流程，重点包括：

1. `normalize_request.py`
2. `build_research_tasks.py`
3. `merge_sources.py`
4. `extract_structured_facts.py`
5. `generate_review_packet.py`
6. `build_guide_model.py`
7. `fill_missing_sections.py`
8. `render_trip_site.py`
9. `build_portal.py`
10. `export_single_html.py`
11. `package_trip.py`
12. `verify_trip.py`

Python 环境规则：

1. 优先使用现有 conda 环境。
2. 当前默认环境为 `py313`。
3. Playwright 浏览器校验优先使用 `paper2any`。
4. 安装缺失依赖时，使用：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>
```

## Validation

完成 V3 升级后，至少验证：

1. 内容模型测试通过
2. 渲染和打包测试通过
3. Playwright 检查通过
4. 单文件分享页可独立打开
5. 桌面端和移动端关键 section 完整存在

## Outcome

V3 的最终定位不是“再写一篇攻略”，而是把旅游攻略生产升级为一套稳定、可复用、可分享、可验证的技能链路。

这套链路尤其适合像“南京出发，延吉 + 长白山 + 可选中转城市”这类多段交通、强时效、多来源融合的国内旅行场景。
