"""Instagram video: the same animation as gif.py, as a 1080x1350 MP4.

Instagram does not take GIF uploads. Frames come from dist/index.html in its
#gif=1 mode at 1.8x, which is exactly 1080x1350, and keep gif.py's timing:
quick through the early years, slower over the last two, then the release month
held for 5 seconds. Needs an ffmpeg binary: $FFMPEG, ffmpeg on the PATH, or the
imageio-ffmpeg package. Writes posts/ppi-scuba-diver/social/ppi-scuba-diver-diver.mp4.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import DIST, PROCESSED, ROOT
from gif import CHROME, CSS_H, CSS_W, SLUG, durations

SCALE = 1.8                                  # 600x750 CSS -> 1080x1350


def ffmpeg():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    order = json.loads((PROCESSED / "page_data.json").read_text())["order"]
    cache = PROCESSED / "gif_frames_1080"
    cache.mkdir(exist_ok=True)
    paths = []
    for m in order:
        p = cache / f"{m}.png"
        if not p.exists() or "--recapture" in sys.argv:
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--window-size={CSS_W},{CSS_H}", f"--force-device-scale-factor={SCALE}",
                            "--virtual-time-budget=3000", f"--screenshot={p}",
                            f"file://{DIST / 'index.html'}#gif=1&embed=0&month={m}"],
                           capture_output=True, timeout=120, check=True)
        paths.append(p)
        print(m, end=" ", flush=True)
    print()
    d = durations(len(paths))
    lst = cache / "frames.txt"                 # ffmpeg concat list: each frame with its duration
    lines = []
    for p, ms in zip(paths, d):
        lines += [f"file '{p}'", f"duration {ms / 1000:.3f}"]
    lines.append(f"file '{paths[-1]}'")        # the last duration needs the file repeated
    lst.write_text("\n".join(lines) + "\n")
    out = ROOT / "posts" / SLUG / "social" / f"{SLUG}-diver.mp4"
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", "fps=30,scale=1080:1350:flags=lanczos,format=yuv420p",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-movflags", "+faststart",
                    str(out)], check=True)
    print("wrote", out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB,",
          f"{sum(d) / 1000:.1f} s")


if __name__ == "__main__":
    main()
