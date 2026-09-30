# opus55-methods-2026-09 — Opus 5.5 发布首月的代码出片做法与故事结构

本地扩展（上游无此文件）。整理 2026-09-22 Opus 5.5 发布后一周内公开的做法，供阶段 0–3
（产品理解、方向、分镜）参考。条目为二手资料的转述，数值是作者自报，不是本库实测。
资料快照日期：2026-09-30；超过一个月后先联网复查再引用。

## 1. 共识：模型写程序，浏览器画帧

- Opus 5.5 不输出视频。它写一个“任意时刻 t 都能画出来”的程序，浏览器逐帧截图，FFmpeg 编码
  （HuggingFace/BeatAPI 教程；LaunchVideo/shipvideo 开源实现）。本库的 Remotion 路线同理。
- **确定性是可靠性的根**：禁止墙钟、未注入虚拟时钟的 rAF/定时器/CSS transition、未播种随机数。
  shipvideo 的做法是注入虚拟时钟，由 `__seek(t)` 统一驱动 rAF、Date、CSS/WAAPI 动画。
- **渲染前先做场景自检**：shipvideo 的 `check_scene` 在若干时间点报告 JS 错误与可见文字；
  本库对应动作是 `remotion still` 抽帧 + 文字可读性检查。

## 2. 提示词骨架（多份资料重合的部分）

先要分镜、后写代码；Facts 与 Style 两行最关键（BeatAPI 模板）：

```text
做一支 {时长}s、{画幅} 的 {片种}，面向 {受众}，看完要让人感到 {一句话情绪}。
Facts（只准用这些）：{已核实的功能与数据口径}
Style：配色 {产品 tokens}，字体 {产品字体}，动效性格 {三个词}。避免：{三到四个陈词滥调}
Audio：{旁白逐句时间表 / BPM 与卡点}
先只交付：节拍表（时间码+画面+旁白）和 4 张关键帧；我确认后再写完整工程。
```

Heather Cooper 的节拍模板：`0–x s 画面 → x–y s 变化 → y–end 转折/回报`，每拍只给一个运镜，
“大 hit 落在哪几秒”提前写死；交付前每秒抽一帧检查。

## 3. Harness 比一句提示词重要

Movez 课程转述（alekdobrohotov）：一句漂亮提示词只占结果的约一成，其余靠可复用的小工作台：
`references/` 放 3–8 张参考图或样片，`what-good-looks-like.md` 写受众、三个情绪词、配色、三条禁令；
出第一版后导出联系表，**只让模型列 5 条具体修改并只改这 5 条**，不整片重写。
本库对应：阶段 1 设计 spec + 阶段 5 静帧验收 + 阶段 7 独立终检，这里补一条“五条修改”纪律，
用于用户反馈轮次之间，防止每轮整片推倒。

## 4. 声音也在代码里做

- ft-motion（MIT）：Canvas `draw(ctx, t)` 场景，每帧 6 个子帧做 180° 快门运动模糊；
  音乐、UI 拟音、whoosh、riser 用 numpy 在同一节拍网格上合成，riser 精确落在 drop，母带 -14 LUFS。
- guizang-product-video-skill：配乐按本片分镜用代码合成，SFX 钉在画面动作上，重要提示处 ducking；
  区分“机器已验证”与“仍需人耳人眼复核”的项（许可证 AGPL-3.0，默认样式另为 BUSL-1.1，勿混用）。
- 本库落地：素材优先用 `assets/audio/`（Mixkit），需要严格等长或专属音色时用
  `assets/scripts/sfx_synth.py` 合成；人声见 `narration-tts.md`。

## 5. “大气 + 有故事性”的结构

发布首周点赞最高的是 15 秒 showreel 与发布片（revid.ai 统计 9/23–9/27 的 64 支 X 视频）。
但宣传片要“大气、有故事”，更值得借鉴的是 Anthropic 官方 20 秒 Opus 5.5 片（Mother London）：
全片不出现一块 UI，只用一条贯穿不同尺度的弧线（地平线→细胞→图纸→器皿边缘→液体），
一句文案收束，再出字标（bretkerr 解读：抓住品牌论点里“唯一不断的那根线”，全片围绕它重复）。

给 B2B 工具片的可执行版本——**一根线 + 三幕**：

| 幕 | 占比 | 内容 | 大气的来源 |
|----|------|------|-----------|
| 一、处境 | 15–20% | 主角（真实用户角色）面对的具体难题，用一句旁白 + 一个抽象意象讲，不上 UI | 留白、慢推、低频铺底；意象是全片那根线的第一次出现 |
| 二、转折 | 55–65% | 产品接管：每个功能都是“那根线”在界面里的一次再现（线→预算分配曲线→概率分布→证据连线） | 真实页面 2.5D 运镜；每镜一个动作；字卡当章节标题 |
| 三、回报 | 15–20% | 回到主角的决定时刻，线收束成字标 | riser→impact→sparkle；字标 hold ≥1s；一句口号 |

写分镜前先回答三句话，答不出就不开工：
1. 主角是谁、他在哪一刻最难？（必须是产品真实面对的用户场景）
2. 贯穿全片的那根线是什么视觉形状，它在每个功能里怎么变形？
3. 结尾观众记住的一句话是什么，它能被产品证据支撑吗？

常见陈词滥调（写进禁令）：柔和渐变上居中大标题当全片主意、逐元素群发光效、
无依据的增长数字/客户 logo、所有镜头同一种飞入、结尾堆满功能名。

## 6. 成本与工期参考（作者自报）

- LaunchVideo：单片约 4 分钟、约 9 万输入 + 1.5 万输出 token；按 $4/$20 列表价约 $0.66/片（未含渲染、TTS、返工）。
- Heather Cooper：空工程到首渲约 9 分钟，带配乐 4K 成片约 26 分钟；某 3 分钟旁白片用掉约 7% 周额度。
- 局限：生物与人脸、过曝光效、长任务易中断、分章节子代理拼接不顺；先渲短区间再整片。

## 来源

- https://huggingface.co/blog/karmen-beatapi/how-to-make-videos-with-claude-opus-5-5
- https://github.com/diggerhq/shipvideo
- https://alekdobrohotov.substack.com/p/how-to-make-motion-videos-with-opus-5-5
- https://github.com/imserhatdemir/ft-motion
- https://www.orcarouter.ai/blog/claude-opus-5-5-product-video-skill
- https://heatherbcooper.substack.com/p/claude-opus-55-for-video
- https://bretkerr.substack.com/p/the-architecture-of-creative-rigor-76e
- https://www.revid.ai/claude-motion-graphics
- https://deepseekartifacts.com/prompts/opus-5-5-video
- https://hyperframes.heygen.com/guides/voice-and-audio

内容为转述，未逐字引用；各项目许可证以其仓库为准。
