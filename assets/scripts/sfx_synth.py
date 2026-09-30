"""程序合成补充音效：只用 numpy + 标准库 wave，无第三方采样，版权归制作者。

用法：
    python sfx_synth.py out_dir [--seed 7]

产出 48kHz / 16-bit / mono WAV，峰值统一归一化到 -3 dBFS，文件名即用途：
    click-soft      真实感按键（短噪声瞬态 + 低通），配鼠标点击
    tick-row        极短木质刻度，配列表逐条打勾（连发时配合音量阶梯）
    whoosh-air      带通噪声扫频，配运镜/面板滑入
    riser-8s        8 秒上行噪声+锯齿音垫，配结尾组装（Sequence 截断到所需长度）
    boom-sub        低频冲击（正弦下滑 + 噪声头），配字标落地
    shimmer-tail    高频闪烁余韵，riser→impact 之后的 sparkle 位
    room-tone-10s   极低音量底噪，给纯字卡段保留空间感
这些是库内 Mixkit 素材的补位件：Mixkit 已有合适素材时优先用库内的；需要与画面严格等长或品牌专属音色时再用本脚本。
"""
import argparse
import wave
from pathlib import Path

import numpy as np

SR = 48_000


def env(n: int, attack: float, release: float) -> np.ndarray:
    """线性起音 + 指数释放包络，单位秒。"""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.exp(-np.maximum(t - attack, 0) / max(release, 1e-4))
    return a * r


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """一阶低通，足够做音色柔化。"""
    alpha = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def bandpass_sweep(noise: np.ndarray, f0: float, f1: float) -> np.ndarray:
    """用随时间变化的一阶高低通组合近似扫频带通。"""
    n = len(noise)
    freqs = np.geomspace(f0, f1, n)
    lo = hi = 0.0
    out = np.empty(n)
    for i in range(n):
        a_hi = 1 - np.exp(-2 * np.pi * freqs[i] * 1.6 / SR)
        a_lo = 1 - np.exp(-2 * np.pi * freqs[i] * 0.6 / SR)
        hi += a_hi * (noise[i] - hi)
        lo += a_lo * (hi - lo)
        out[i] = hi - lo
    return out


def normalize(x: np.ndarray, peak_db: float = -3.0) -> np.ndarray:
    peak = np.max(np.abs(x)) or 1.0
    return x / peak * (10 ** (peak_db / 20))


def write(path: Path, x: np.ndarray) -> None:
    pcm = (np.clip(normalize(x), -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n = int(0.09 * SR)
    click = lowpass(rng.standard_normal(n), 3800) * env(n, 0.0008, 0.012)
    click += 0.35 * np.sin(2 * np.pi * 1900 * np.arange(n) / SR) * env(n, 0.0005, 0.006)
    write(out / "click-soft.wav", click)

    n = int(0.06 * SR)
    t = np.arange(n) / SR
    tick = np.sin(2 * np.pi * 2600 * t) * env(n, 0.0003, 0.008) + 0.4 * lowpass(rng.standard_normal(n), 6000) * env(n, 0.0002, 0.003)
    write(out / "tick-row.wav", tick)

    n = int(0.7 * SR)
    whoosh = bandpass_sweep(rng.standard_normal(n), 300, 4200) * np.sin(np.pi * np.arange(n) / n) ** 1.6
    write(out / "whoosh-air.wav", whoosh)

    n = int(8 * SR)
    t = np.arange(n) / SR
    ramp = (t / t[-1]) ** 2.2
    saw_f = 80 * (1 + 3 * ramp)
    saw = 2 * ((np.cumsum(saw_f) / SR) % 1) - 1
    riser = 0.5 * lowpass(saw, 1500) * ramp + bandpass_sweep(rng.standard_normal(n), 400, 9000) * ramp
    write(out / "riser-8s.wav", riser)

    n = int(2.4 * SR)
    t = np.arange(n) / SR
    f = 34 + 70 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.004, 0.55)
    boom += 0.3 * lowpass(rng.standard_normal(n), 900) * env(n, 0.001, 0.05)
    write(out / "boom-sub.wav", boom)

    n = int(2.0 * SR)
    t = np.arange(n) / SR
    shimmer = np.zeros(n)
    for k, fr in enumerate((3520, 4186, 5274, 6272)):
        shimmer += np.sin(2 * np.pi * fr * t + k) * env(n, 0.02 + 0.03 * k, 0.5) * (0.5 + 0.5 * np.sin(2 * np.pi * (5 + k) * t))
    write(out / "shimmer-tail.wav", shimmer * 0.6)

    n = int(10 * SR)
    room = lowpass(rng.standard_normal(n), 500)
    fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.5 * SR))
    write(out / "room-tone-10s.wav", room * fade)
    print(f"wrote 7 files -> {out}")


if __name__ == "__main__":
    main()
