# 旅游攻略 HTML 项目流程与问题总结

日期：2026-04-11

## 1. 这次项目的目标

本次工作的目标分成两层：

1. 先把根目录的 `travel-planning-playbook.md` 重写成可复用的旅游攻略 HTML 执行手册。
2. 再基于这份手册，重建吉林 / 延吉 / 长白山项目，输出桌面端、手机端、信源文档和图位方案。

## 2. 已确认的用户需求

- 出发地：南京
- 日期：2026-04-30 至 2026-05-05
- 人员：4 位成年人，约 28 岁，2 男 2 女
- 节奏：接受早起
- 住宿：汉庭优先
- 房价接受区间：每标间 150-450 元
- 预算：先估算，不先设硬上限
- 输出形式：桌面端 HTML、手机端 HTML、图位方案、信源说明
- 页面顺序：每天安排放在前面，再展开推荐方案、备选方案、景点、美食、季节、穿衣、交通、信息源
- 手机端要求：分页展示，且与桌面端事实内容一致
- 文案要求：语气温和、直接、实用，不写幕后过程感语言

## 3. 实际执行流程

### 3.1 先做方法文档，再做具体项目

最开始先没有直接改吉林页面，而是先把执行方法沉淀下来，避免后面每做一个目的地都重新整理流程。

先后形成了三层文档：

- 需求与设计说明：`docs/superpowers/specs/2026-04-10-travel-planning-playbook-design.md`
- 实施计划：`docs/superpowers/plans/2026-04-10-travel-playbook-and-jilin-guide-implementation.md`
- 通用执行手册：`travel-planning-playbook.md`

### 3.2 用独立 worktree 做开发

为了不直接扰动主分支，在项目内创建了独立 worktree：

- worktree 路径：`.worktrees/travel-playbook-jilin-guide`
- 分支：`feature/travel-playbook-jilin-guide`

这样做的目的有两个：

- 把手册改造和页面重建放在隔离环境里做
- 主分支即使有用户自己的未提交内容，也能尽量减少互相干扰

### 3.3 重写执行手册

`travel-planning-playbook.md` 被重构为“执行手册”而不是“写作建议”。

当前手册已经覆盖：

- 开始前必须确认的信息
- 调研执行顺序
- 行程方案生成规则
- HTML 内容顺序规范
- 图位方案规范
- 交付检查清单
- 可复用输出模板
- 桌面端 / 手机端 / notes / assets 的推荐目录结构

### 3.4 搭建吉林项目的新结构

吉林项目最后落在：

- `trips/jilin-yanji-changbaishan/assets/`
- `trips/jilin-yanji-changbaishan/desktop/`
- `trips/jilin-yanji-changbaishan/mobile/`
- `trips/jilin-yanji-changbaishan/notes/`

核心做法不是复制两份内容，而是把事实内容放在共享文件里，再让桌面端和手机端分别渲染：

- `assets/guide-content.js`：共享内容
- `assets/render-guide.js`：共享渲染逻辑
- `desktop/index.html` + `desktop.css`
- `mobile/index.html` + `mobile.css`

### 3.5 先补 notes，再补页面

根据用户要求，先把研究支撑和图位规划独立出来：

- `notes/sources.md`
- `notes/image-plan.md`

这样后续继续优化页面时，信息源和图像位置不会散落在正文里。

### 3.6 增加回归检查

为了避免页面结构越改越散，新增并完善了两类检查：

- `tests/travel-guide-regression.ps1`
- `tests/playwright_trip_render_check.py`

检查目标包括：

- 必要文件是否存在
- 桌面端和手机端是否含有规定的 `section id`
- 手机端是否包含分页标记 `data-page`
- 页面是否出现横向溢出
- 两端结构是否匹配执行手册的章节顺序

### 3.7 合并回主分支并清理环境

用户后续选择了本地合并到 `main`。执行顺序是：

1. 将功能分支合并回 `main`
2. 在合并结果上完成回归验证
3. 删除功能分支
4. 删除 worktree

清理后目前只保留主工作区。

## 4. 过程中遇到的主要问题

### 4.1 初始需求信息不完整

一开始只有“做旅游攻略流程”和“完善吉林 HTML”两个大方向，缺少会直接影响行程判断的关键信息。

补齐的信息包括：

- 是否有小孩
- 年龄段
- 男女比例
- 出发地
- 日期范围
- 是否接受早起
- 预算方式
- 住宿偏好

这一步很重要，因为如果不先确认，后面的交通链路、住宿配置、节奏安排都会偏。

### 4.2 原始 `travel-planning-playbook.md` 不够像执行手册

旧版本已经有不少内容，但更偏“经验和建议”，离“拿来就能按步骤执行”还有距离。

处理方式：

- 重做文档结构
- 固定章节顺序
- 固定交付清单
- 固定 HTML 结构与 section id
- 固定 notes 和 assets 输出目录

### 4.3 吉林页面需要桌面端和手机端内容一致

如果直接做两份独立 HTML，很容易一边更新、一边遗漏。

处理方式：

- 把内容抽到 `guide-content.js`
- 通过 `render-guide.js` 保持输出规则一致
- 桌面端和手机端只保留布局差异

### 4.4 用户强调先做图位方案，而不是直接塞图

这和常见“先做页面，后面再找图”的顺序不同。

处理方式：

- 单独建立 `notes/image-plan.md`
- 把图位编号、位置、建议画面、来源类型、适合的视频时间轴/镜头说明独立沉淀

### 4.5 主分支当时不是干净状态

合并前主分支就存在用户自己的未提交改动和文件删改。

这类情况下最大的风险是误覆盖用户内容。

处理方式：

- 在独立 worktree 上开发
- 合并和清理时只处理本次功能分支相关内容
- 主分支上原有未提交文件全部保持原样

### 4.6 PowerShell 回归脚本兼容性问题

静态回归脚本里对标题匹配的写法，在 PowerShell 5.1 环境下需要更稳妥的转义方式。

处理方式：

- 调整为 `([regex]::Escape($heading))`

这样旧版 PowerShell 环境也能稳定检查中文标题。

### 4.7 共享内容文件的导出方式需要更稳

`guide-content.js` 如果只按一种导出方式写，在不同加载环境下容易出兼容问题。

处理方式：

- 采用 `globalThis.__TRIP_GUIDES__` 命名空间注册
- 同时保留 `module.exports`

这样浏览器端和脚本侧都更容易复用。

### 4.8 Playwright 检查在 Windows 沙箱环境下有权限波动

浏览器渲染检查在 Windows 环境里可能出现权限问题，之前跑这类检查时出现过需要提权的情况。

处理方式：

- 保留 Python + Playwright 检查脚本
- 增加更稳妥的临时产物目录管理
- 在必要时使用已批准方式执行

### 4.9 worktree 清理和分支删除需要顺序正确

在最后清理阶段，曾出现“分支仍被 worktree 占用，暂时不能删除”的情况。

处理方式：

- 先移除 worktree
- 再删除分支
- 最后重新核对 `git worktree list`

## 5. 最终产物

### 通用手册

- `travel-planning-playbook.md`

### 吉林项目

- `trips/jilin-yanji-changbaishan/assets/base.css`
- `trips/jilin-yanji-changbaishan/assets/guide-content.js`
- `trips/jilin-yanji-changbaishan/assets/render-guide.js`
- `trips/jilin-yanji-changbaishan/desktop/index.html`
- `trips/jilin-yanji-changbaishan/desktop/desktop.css`
- `trips/jilin-yanji-changbaishan/mobile/index.html`
- `trips/jilin-yanji-changbaishan/mobile/mobile.css`
- `trips/jilin-yanji-changbaishan/notes/sources.md`
- `trips/jilin-yanji-changbaishan/notes/image-plan.md`

### 验证工具

- `tests/travel-guide-regression.ps1`
- `tests/playwright_trip_render_check.py`

## 6. 当前状态判断

### `travel-planning-playbook.md` 现在是不是完整流程文档

结论：是，按“旅游攻略 HTML 通用执行手册”这个定位来看，它已经是完整流程文档。

它现在已经具备以下特点：

- 能指导一个新目的地从需求确认走到 HTML 交付
- 能约束页面固定结构和 section 顺序
- 能约束桌面端、手机端、notes、assets 的输出形式
- 能指导图位方案单独沉淀
- 能作为后续多个目的地复用的母版

### 它还不包含什么

它现在不承担以下角色：

- 本次吉林项目的完整过程复盘
- 每一步调研明细日志
- 每次修改的版本变更记录
- 项目级风险追踪表

所以更准确的说法是：

- `travel-planning-playbook.md` 已经是完整的“通用流程文档”
- 这份总结文档补上的是“本次项目执行过程与问题记录”

## 7. 后续如果继续完善，可以补哪些内容

如果你希望这套体系再往前走一步，可以继续加三类文档：

1. `research-log.md`
   记录每次检索了哪些站点、得到了什么结论、哪些信息仍待确认。
2. `change-log.md`
   记录每轮页面优化改了什么，方便回看版本差异。
3. `acceptance-checklist.md`
   把内容核对、视觉核对、移动端核对、链接核对拆成单独验收单。

这样会形成：

- Playbook 负责“标准流程”
- Summary 负责“项目复盘”
- Research Log 负责“调研轨迹”
- Acceptance Checklist 负责“交付验收”

