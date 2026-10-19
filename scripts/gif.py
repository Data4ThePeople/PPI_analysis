"""Social GIF: the diver through every month, October 2016 to the release month.

One frame per month from dist/index.html in its #gif=1 mode (the scene at its
normal scale, so depth and bubble sizes compare across months). Every frame is
a real month; nothing is interpolated. The frames run quickly through the early
years and slow down over the last two, then the release month holds for 5
seconds. Writes posts/ppi-scuba-diver/social/ppi-scuba-diver-diver.gif.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from common import DIST, PROCESSED, ROOT

SLUG = "ppi-scuba-diver"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS_W, CSS_H, SCALE = 600, 750, 1.4      # 4:5, the feed shape on LinkedIn and X
OUT_W, OUT_H = 560, 700
COLORS = 255
FAST_MS, SLOW_MS, SLOW_N, HOLD_MS = 50, 500, 24, 5000


def frame(month: str, path: Path):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={CSS_W},{CSS_H}", f"--force-device-scale-factor={SCALE}",
                    "--virtual-time-budget=3000", f"--screenshot={path}",
                    f"file://{DIST / 'index.html'}#gif=1&embed=0&month={month}"],
                   capture_output=True, timeout=120, check=True)


def durations(n):
    """FAST_MS per month, then the last SLOW_N months ease up to SLOW_MS, then the hold."""
    out = []
    for k in range(n - 1):
        j = k - (n - 1 - SLOW_N)                    # 0..SLOW_N-1 inside the slow stretch
        f = 0 if j < 0 else ((j + 1) / SLOW_N) ** 2
        out.append(int(round((FAST_MS + f * (SLOW_MS - FAST_MS)) / 10) * 10))
    return out + [HOLD_MS]


def main():
    order = json.loads((PROCESSED / "page_data.json").read_text())["order"]
    out_dir = ROOT / "posts" / SLUG / "social"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = PROCESSED / "gif_frames"            # captured frames, kept so the GIF can be re-encoded
    cache.mkdir(exist_ok=True)
    frames = []
    for k, m in enumerate(order):
        p = cache / f"{m}.png"
        if not p.exists() or "--recapture" in sys.argv:
            frame(m, p)
        frames.append(Image.open(p).convert("RGB").resize((OUT_W, OUT_H), Image.LANCZOS))
        print(m, end=" ", flush=True)
    print()
    # One palette for every frame, built from frames across all ten years, so
    # colors neither flicker nor drift in the early months.
    picks = [frames[i] for i in range(0, len(frames), 10)] + [frames[-1]]
    sheet = Image.new("RGB", (OUT_W, OUT_H * len(picks)))
    for j, f in enumerate(picks):
        sheet.paste(f, (0, OUT_H * j))
    # Octree keeps small bright colors (the yellow fins and fish) that median cut gives to the water.
    pal = sheet.quantize(colors=COLORS, method=Image.Quantize.FASTOCTREE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    d = durations(len(q))
    out = out_dir / f"{SLUG}-diver.gif"
    q[0].save(out, save_all=True, append_images=q[1:], duration=d, loop=0, optimize=True, disposal=1)
    frames[-1].save(out_dir / f"{SLUG}-diver-last-frame.png")
    print("wrote", out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB,", len(q), "frames,",
          f"{sum(d[:-1]) / 1000:.1f} s of months, last held {HOLD_MS / 1000:.0f} s")


if __name__ == "__main__":
    main()
