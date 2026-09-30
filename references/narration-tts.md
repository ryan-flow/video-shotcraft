# narration-tts — 旁白片：配音、字幕与四层混音

本地扩展（上游无此文件）。片子需要人声旁白时读本文件；与 `sound-design.md`
（SFX/BGM）互补，冲突时本文件管人声相关的时序与混音，其余以 sound-design 为准。

## 1. 四层分工（每层只做一件事）

| 层 | 职责 | 默认音量系数 | 规则 |
|----|------|------------|------|
| 旁白 VO | 讲清故事和功能 | 1.0 | 全片最清楚的一层；不与字卡大标题说同一句话 |
| BGM | 能量骨架与情绪 | 0.30，VO 期间压到 0.12 | ducking 只在 VO 句内压低，句间 250ms 回升 |
| SFX | 钉画面关键动作 | 0.2–0.6（按素材峰值，见 sound-design 4.1） | VO 句内的 SFX 再降 30%，不和人声抢 2–4kHz |
| 字幕 | 静音可读 | — | 跟 VO 逐句出；字高按 Q11（≥56px） |

来源：HyperFrames 声音指南的分层与 ducking 原则（hyperframes.heygen.com/guides/voice-and-audio）。

## 2. 顺序：先声后画（旁白片的硬规则）

1. **写旁白稿**：一句一行，每句 ≤22 个汉字、只讲一个信息点；中文按约 4.2 字/秒估长。
   写成 `narration.json`（格式见 `assets/scripts/tts_edge.py` 顶部）。
2. **合成并试听**：`python assets/scripts/tts_edge.py narration.json public/audio/vo`。
   产出每句 `vo-<id>.mp3`、`narration-timing.json`（实测时长 + 分词边界）、参考 `narration.srt`。
   听完整遍再往下走；读音、停顿、语气问题改稿或改 `rate`，不在剪辑里硬切。
3. **按实测时长排镜头**：`SHOTS` 的每段 duration = 该段旁白实测时长 + 前后呼吸帧
   （句前 ≥6f 让画面先动，句后 ≥12f 让信息落定）。不要先定镜头长再塞配音。
4. **字幕从同一张时间表派生**：`CAPTIONS[i].from = SHOTS.x.from + VO_OFFSET_x`，与 VO
   `<Sequence>` 用同一个偏移常量，禁止单独手写字幕帧号。
5. **画面锁定后**再钉 SFX（sound-design 前置条件不变）。

## 3. 微软神经语音（Edge 在线）选型

`edge-tts` 免密钥、带分词边界，适合样片与内部审片。**对外商用发布改用 Azure Speech
官方服务**（同名音色、SSML 兼容，需用户自备订阅与密钥）；Edge 在线朗读属非官方接口，
授权与稳定性不作保证，交付时必须写明。

| 音色 | 气质 | 适用 |
|------|------|------|
| zh-CN-YunjianNeural | 沉稳、有力、偏纪录片旁白 | 大气/发布会/故事型开场（默认） |
| zh-CN-YunyangNeural | 新闻播音、字正腔圆 | 功能说明、数据陈述 |
| zh-CN-YunxiNeural | 年轻男声、亲和 | 投手第一人称、轻松段落 |
| zh-CN-XiaoxiaoNeural | 温暖女声、表现力强 | 情绪句、结尾口号 |
| zh-CN-XiaoyiNeural | 活泼女声 | 短视频竖版 |

语速：旁白默认 `+0%`；开场钩子与结尾口号 `-5%~-10%` 放慢留重音；功能段 `+5%` 以内。
英文品牌名（如 LAVEDA）先单句试听，读错时在稿里改写成读音友好的形式并保留字幕原文。

## 4. Remotion 落地写法

```tsx
// VO：每句一个 Sequence，from 相对镜头起点（与 sound-design 4.5 同规则）
export const VO = [{ id: 'hook', from: SHOTS.open.from + 12 }, /* … */] as const;
const vo = timing.lines; // import timing from '../public/audio/vo/narration-timing.json'
{VO.map((v) => {
  const line = vo.find((l) => l.id === v.id)!;
  return <Sequence key={v.id} from={v.from} durationInFrames={Math.ceil(line.duration * FPS) + 2}>
    <Audio src={staticFile(`audio/vo/${line.file}`)} volume={1} />
  </Sequence>;
})}

// BGM ducking：按帧查询是否处于 VO 句内，平滑插值，句间回升
const inVo = (f: number) => VO.some((v) => { const d = Math.ceil(vo.find((l) => l.id === v.id)!.duration * FPS);
  return f >= v.from - 6 && f <= v.from + d + 8; });
<Audio src={staticFile('audio/bgm.mp3')} volume={(f) => {
  const target = inVo(f) ? 0.12 : 0.3; // 需要更顺时对前后 6 帧的 target 取均值做平滑
  return interpolate(f, [0, 30, TOTAL - 60, TOTAL], [0, 1, 1, 0], { extrapolateRight: 'clamp' }) * target;
}} />
```

- `bgm` inputProp 双版本交付规则不变；**再加一个 `vo` inputProp**，交付带旁白 / 无旁白两版，
  方便投放平台另配口播。
- 旁白片的 SFX 钉帧表里，与 VO 重叠的条目音量 ×0.7，并在注释标 `// under VO`。

## 5. 验收（补充 final-review）

- 闭眼只听一遍：每句能听清，BGM 没盖住人声，句间没有突兀的音量跳变。
- 静音看一遍：字幕与画面独立能讲清故事。
- 抽查 3 句：字幕出现帧与 VO 起音误差 ≤3f。
- 数一遍：旁白里的每个功能主张都能在画面或产品证据里找到对应（aesthetic-rules C4）。
