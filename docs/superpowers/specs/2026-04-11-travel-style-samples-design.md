---
title: Travel Style Samples Design
date: 2026-04-11
status: approved-in-chat
owner: Codex
---

# Travel Style Samples Design

## Goal

为 `travel-skill` 提供 4 套可直接打开查看的视觉样机，统一放入 `sample/` 目录，供用户比较桌面端与移动端的阅读风格。

## Scope

本轮只做样机，不改 `travel-skill` 生产模板。样机需要覆盖：

1. 桌面端阅读风格
2. 移动端阅读风格
3. 首页入口页
4. 四套彼此差异清楚的旅行攻略视觉方向

## Chosen Directions

### A. 黑白杂志风

- 桌面端：Editorial / Magazine
- 移动端：浅灰背景 + 白卡片
- 气质：克制、留白、黑白灰为主

### B. 目的地画报风

- 桌面端：旅行画报专题
- 移动端：更明显的色彩卡片层级
- 气质：图像驱动、目的地代表色更突出

### C. 轻奢酒店刊物风

- 桌面端：柔和、优雅、精品酒店手册感
- 移动端：圆角更柔、阴影更轻
- 气质：舒适、温和、偏生活方式

### D. 现代信息设计风

- 桌面端：信息结构清晰、适合复杂路线
- 移动端：标准 Bento Box
- 气质：理性、现代、模块分明

## Content Strategy

样机使用同一组旅行内容骨架，方便纯看视觉差异：

1. 最推荐路线
2. 多方案路线
3. 穿衣指南
4. 景点信息
5. 交通详细信息
6. 按城市划分的美食店铺
7. 注意事项
8. 信息来源

## Deliverables

在 `sample/travel-style-samples/` 下输出：

1. `index.html`
2. `style-a-editorial.html`
3. `style-b-destination.html`
4. `style-c-hotel.html`
5. `style-d-bento.html`
6. 共用资源目录

## Validation

至少完成：

1. 本地 HTML 结构可打开
2. 入口页能跳转到 4 个样机页
3. 每个样机页同时展示桌面端和移动端效果
4. 页面在静态条件下不依赖外部服务
