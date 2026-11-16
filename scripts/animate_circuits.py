"""Social animation of the printed circuit assemblies chart (charts/2026-10/07-circuit-history.png).

The line draws in from June 1983 to October 2026 over about 8 seconds: quickly
through the first 40 years (a few months a frame), then one month a frame from
January 2024, so the 2026 climb can be seen. The finished chart then holds for
5 seconds, and that last frame is the published chart. Every label is a real
month's value. Writes, in posts/ppi-october-2026/social/:
  ppi-october-2026-circuits.gif   for X, Bluesky and LinkedIn
  ppi-october-2026-circuits.mp4   1080x1920 (9:16) for Instagram, with a square,
                                  large-type version of the chart in the center
                                  square, which every Instagram crop keeps
Needs ffmpeg for the MP4 (see video.py).
"""
from __future__ import annotations

import io
import subprocess

import matplotlib.pyplot as plt
from PIL import Image

from common import ROOT
from october import DATA_CENTER, circuit_history
from takeaways import BG, GRID, INK, MONTH, MUTED, UP, month_label, raw_levels, xpos
from video import ffmpeg

SLUG = "ppi-october-2026"
OUT = ROOT / "posts" / SLUG / "social"
FAST_S, SLOW_S, HOLD_S = 4.5, 3.5, 5.0
SLOW_FROM = "2024-01"
CODE = DATA_CENTER[0][1][0][0]


def series():
    lv = raw_levels(f"WPU{CODE}")
    base = lambda m: f"{int(m[:4]) - 1}{m[4:]}"
    months = [m for m in sorted(lv) if base(m) in lv and m <= MONTH]
    return months, [(lv[m] / lv[base(m)] - 1) * 100 for m in months]


def frames_and_timing(months):
    """Frame k = months drawn. Fast part: every 4th month; slow part: every month; last frame always."""
    slow = months.index(SLOW_FROM)
    fast = list(range(4, slow, 4))
    ks = fast + list(range(slow, len(months) + 1))
    n_fast, n_slow = len(fast), len(ks) - len(fast)
    ms = [round(FAST_S * 1000 / n_fast / 10) * 10] * n_fast + [round(SLOW_S * 1000 / n_slow / 10) * 10] * n_slow
    ms[-1] = int(HOLD_S * 1000)
    return ks, ms


def render(k, dpi=100):
    f, n = circuit_history(None, upto=k)
    buf = io.BytesIO()
    f.savefig(buf, dpi=dpi, facecolor=BG)
    plt.close(f)
    buf.seek(0)
    return Image.open(buf).convert("RGB"), n


def ig_frame(k, months, ys):
    """A 1080x1080 square for Instagram: big type, the line, the current value, the axis."""
    f = plt.figure(figsize=(7.2, 7.2), dpi=150)
    f.patch.set_facecolor(BG)
    f.text(0.06, 0.94, "Printed circuit assembly prices", fontsize=24, fontweight="bold", color=UP, va="top")
    f.text(0.06, 0.875, f"12-month change, {month_label(months[0])} to {month_label(MONTH)}", fontsize=13,
           color=INK, va="top")
    ax = f.add_axes([0.13, 0.12, 0.62, 0.66])
    ax.set_facecolor(BG)
    xs = [xpos(m) for m in months]
    ax.plot(xs[:k], ys[:k], color=UP, lw=3)
    ax.scatter([xs[k - 1]], [ys[k - 1]], s=70, color=UP, zorder=4)
    ax.text(xs[k - 1] + 0.8, ys[k - 1], f"{ys[k - 1]:+.1f}%\n{month_label(months[k - 1])}", color=INK, fontsize=15,
            fontweight="bold", va="center")
    ax.axhline(0, color=MUTED, lw=0.9)
    ax.set_ylim(-40, 190)
    ticks = list(range(0, 151, 50))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks], fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_xlim(xs[0] - 0.3, xs[-1] + 0.5)
    yt = list(range(1985, int(MONTH[:4]) + 1, 10))
    ax.set_xticks(yt)
    ax.set_xticklabels([str(y) for y in yt], fontsize=12, color=INK)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    f.text(0.06, 0.035, "Data 4 The People  ·  Source: BLS Producer Price Index", fontsize=10, color=MUTED)
    buf = io.BytesIO()
    f.savefig(buf, dpi=150, facecolor=BG)
    plt.close(f)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    months, ys = series()
    ks, d = frames_and_timing(months)
    gif = [render(k)[0] for k in ks]
    pal = gif[-1].quantize(colors=255, method=Image.Quantize.FASTOCTREE)
    q = [g.quantize(palette=pal, dither=Image.Dither.NONE) for g in gif]
    gif_out = OUT / f"{SLUG}-circuits.gif"
    q[0].save(gif_out, save_all=True, append_images=q[1:], duration=d, loop=0, optimize=True, disposal=1)
    gif[-1].save(OUT / f"{SLUG}-circuits-last-frame.png")
    # Instagram: 1080x1920; headline and chart inside the center 1080x1080 square.
    W, H = 1080, 1920
    sq = (H - W) // 2
    frames_dir = ROOT / "data" / "processed" / "circuit_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, (k, ms) in enumerate(zip(ks, d)):
        c = Image.new("RGB", (W, H), BG)
        c.paste(ig_frame(k, months, ys), (0, sq))
        p = frames_dir / f"{i:04d}.png"
        c.save(p)
        lines += [f"file '{p}'", f"duration {ms / 1000:.3f}"]
    lines.append(f"file '{p}'")
    lst = frames_dir / "frames.txt"
    lst.write_text("\n".join(lines) + "\n")
    mp4 = OUT / f"{SLUG}-circuits.mp4"
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-t", f"{sum(d) / 1000:.2f}", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "20", "-movflags", "+faststart", str(mp4)], check=True)
    print(f"wrote {gif_out.name} ({gif.__len__()} frames, {gif_out.stat().st_size / 1e6:.1f} MB, {gif[-1].size}, "
          f"draw {sum(d[:-1]) / 1000:.1f} s + hold {HOLD_S:.0f} s) and {mp4.name} "
          f"({mp4.stat().st_size / 1e6:.1f} MB, {sum(d) / 1000:.1f} s)")


if __name__ == "__main__":
    main()
