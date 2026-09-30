# 本地改动清单

上游：https://github.com/Vincentwei1021/video-shotcraft ，快照 commit `5ddbf521038b`（2026-09-29 00:15 +08:00）。
维护方：LAVEDA 投流助手项目（Kiro）。首次修改 2026-09-30。

| 类型 | 路径 | 内容 |
|------|------|------|
| 修改 | SKILL.md | “何时读哪个文件”追加 3 行；新增“本地扩展”一节（旁白先声后画、主张台账、故事先于镜头、Windows 注意事项） |
| 追加 | references/aesthetic-rules.md | 末尾追加 C4（主张可追溯）、S6（旁白片先声后画与 ducking），未改动原有编号 |
| 新增 | references/narration-tts.md | 旁白/字幕/四层混音方法，微软神经语音选型，Remotion VO 与 ducking 写法 |
| 新增 | references/opus55-methods-2026-09.md | Opus 5.5 发布首月社区做法与“一根线+三幕”故事结构，附来源 |
| 新增 | assets/scripts/tts_edge.py | edge-tts 逐句合成 → mp3 + 时间表 JSON + SRT（依赖 edge-tts 7.2.7、ffprobe） |
| 新增 | assets/scripts/sfx_synth.py | numpy 合成 7 个补位音效（click/tick/whoosh/riser/boom/shimmer/room tone），48kHz 16-bit |
| 新增 | references/storyboard-gate.md | 镜头稿放行门槛：定位四行、卖点台账、禁止上镜清单、故事与文案检查、交付格式 |
| 追加 | references/aesthetic-rules.md | C5（只讲核心卖点，手动操作/次要机制/降级描述不上镜），判例为 LAVEDA v1 用户反馈 |
| 新增 | LOCAL_CHANGES.md | 本文件 |

发布：公开 fork https://github.com/ryan-flow/video-shotcraft ，本地改动在分支 `laveda-local`。

## 验证（2026-09-30）

- `tts_edge.py`：两句中文样例合成成功（zh-CN-YunjianNeural，4.25s / 2.38s，分别 8 / 3 个边界事件），SRT 与时间表正确生成。
- `sfx_synth.py`：7 个 WAV 生成，时长与设计一致（0.06–10s）。音色未经人耳评审，使用前需试听。

## 同步上游

改动未提交。更新前：`git stash` → `git pull` → `git stash pop`，冲突时以上游为准重放本表改动。
也可在本地建分支 `laveda-local` 提交后 `git rebase origin/main`。

## 授权提醒

- Edge 在线朗读为非官方接口，仅用于样片与内部审片；对外商用改用 Azure Speech 官方服务。
- `sfx_synth.py` 产物为程序合成，无第三方采样；库内 Mixkit 素材按 `assets/audio/ATTRIBUTION.md`。
- Remotion 对超过 3 人的公司可能需要商用许可，出片前核对其 LICENSE。
