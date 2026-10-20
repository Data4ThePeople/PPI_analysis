"""Social animation of the long-distance trucking chart (charts/2026-09/06-trucking.png).

The line draws in one real month at a time, June 2010 to September 2026, over about
8 seconds, then the finished chart holds for 5. The last frame is the published chart.
Writes, in posts/ppi-september-2026/social/:
  ppi-september-2026-trucking.gif   1200x750, for X and LinkedIn
  ppi-september-2026-trucking.mp4   1080x1920 (9:16) for Instagram, with a square, large-type
                                    version of the chart in the center square, which every
                                    Instagram crop keeps
Needs ffmpeg for the MP4 (see video.py).
"""
from __future__ import annotations

import io
import subprocess

import matplotlib.pyplot as plt
from PIL import Image

from common import ROOT
from takeaways import BG, GRID, INK, LINE_A, MUTED, TRUCK, month_label, raw_levels, shift_month, trucking, xpos
from video import ffmpeg

SLUG = "ppi-september-2026"
OUT = ROOT / "posts" / SLUG / "social"
DRAW_S, HOLD_S, START_K = 8.0, 5.0, 12


def render(k, dpi):
    f, n = trucking(None, upto=k)
    buf = io.BytesIO()
    f.savefig(buf, dpi=dpi, facecolor=BG)
    plt.close(f)
    buf.seek(0)
    return Image.open(buf).convert("RGB"), n


def ig_series():
    lv = raw_levels(f"WPU{TRUCK}")
    months = [m for m in sorted(lv) if shift_month(m, 12) in lv and m <= "2026-09"]
    ys = [(lv[m] / lv[shift_month(m, 12)] - 1) * 100 for m in months]
    return months, ys, sum(ys[:-1]) / len(ys[:-1])


def ig_frame(k, months, ys, avg):
    """A 1080x1080 square for Instagram: big type, the line, the average, the axis."""
    f = plt.figure(figsize=(7.2, 7.2), dpi=150)
    f.patch.set_facecolor(BG)
    f.text(0.06, 0.94, "Long-haul trucking prices", fontsize=24, fontweight="bold", color=LINE_A, va="top")
    f.text(0.06, 0.875, "12-month change, June 2010 to September 2026", fontsize=13, color=INK, va="top")
    ax = f.add_axes([0.13, 0.12, 0.70, 0.66])
    ax.set_facecolor(BG)
    xs = [xpos(m) for m in months]
    ax.plot(xs[:k], ys[:k], color=LINE_A, lw=3)
    ax.scatter([xs[k - 1]], [ys[k - 1]], s=70, color=LINE_A, zorder=4)
    ax.text(xs[k - 1] + 0.3, ys[k - 1], f"{ys[k - 1]:+.1f}%", color=INK, fontsize=16, fontweight="bold", va="center")
    ax.text(xs[k - 1], ys[k - 1] + (3.6 if ys[k - 1] >= avg else -3.6), month_label(months[k - 1]),
            color=MUTED, fontsize=11, ha="center", va="center")
    ax.plot([xs[0], xs[-1]], [avg, avg], color=MUTED, lw=1.6, ls=(0, (4, 3)))
    ax.text(xs[-1] + 0.3, avg - 2.4, f"average\n{avg:+.1f}%", color=MUTED, fontsize=11, va="center")
    ax.axhline(0, color=MUTED, lw=0.9)
    ax.set_ylim(-18, 32)
    ax.set_yticks(range(-10, 31, 10))
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in range(-10, 31, 10)], fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_xlim(xs[0] - 0.2, xs[-1] + 0.3)
    ax.set_xticks(range(2012, 2027, 4))
    ax.set_xticklabels([str(y) for y in range(2012, 2027, 4)], fontsize=12, color=INK)
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
    _, n = render(START_K, 50)
    ks = list(range(START_K, n + 1))
    step_ms = int(DRAW_S * 1000 / len(ks) // 10 * 10) or 20
    gif = []
    months, ys, avg = ig_series()
    for k in ks:
        gif.append(render(k, 100)[0])                 # 12 x 7.5 in -> 1200 x 750
    # GIF: one palette for every frame.
    pal = gif[-1].quantize(colors=255, method=Image.Quantize.FASTOCTREE)
    q = [g.quantize(palette=pal, dither=Image.Dither.NONE) for g in gif]
    d = [step_ms] * (len(q) - 1) + [int(HOLD_S * 1000)]
    gif_out = OUT / f"{SLUG}-trucking.gif"
    q[0].save(gif_out, save_all=True, append_images=q[1:], duration=d, loop=0, optimize=True, disposal=1)
    # Instagram: 1080x1920; headline and chart inside the center 1080x1080 square.
    W, H = 1080, 1920
    sq = (H - W) // 2
    frames_dir = ROOT / "data" / "processed" / "trucking_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, (k, ms) in enumerate(zip(ks, d)):
        c = Image.new("RGB", (W, H), BG)
        c.paste(ig_frame(k, months, ys, avg), (0, sq))
        p = frames_dir / f"{i:04d}.png"
        c.save(p)
        lines += [f"file '{p}'", f"duration {ms / 1000:.3f}"]
    lines.append(f"file '{p}'")
    lst = frames_dir / "frames.txt"
    lst.write_text("\n".join(lines) + "\n")
    mp4 = OUT / f"{SLUG}-trucking.mp4"
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-t", f"{sum(d) / 1000:.2f}", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "20", "-movflags", "+faststart", str(mp4)], check=True)
    gif[-1].save(OUT / f"{SLUG}-trucking-last-frame.png")
    print(f"wrote {gif_out.name} ({gif_out.stat().st_size / 1e6:.1f} MB, {len(q)} frames, {step_ms} ms each, "
          f"hold {HOLD_S:.0f} s) and {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB, {sum(d) / 1000:.1f} s)")


if __name__ == "__main__":
    main()
