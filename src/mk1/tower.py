# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Benjamin Stanley Frohman
"""Render the MK-1 pipeline as an animated 'moving tower' GIF."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .kernel import VARIANTS, gram

STAGES = [
    ("HOST", "scale x, queue pair"),
    ("LATCH", "reset |0>^n"),
    ("MAP", "U_phi(x)"),
    ("UNCOMPUTE", "U_phi(x')^dag"),
    ("SHOTS", "P(0...0)  (exact statevector here)"),
    ("GRAM", "write K_ij"),
    ("DUAL", "fit alpha, b"),
    ("DECIDE", "f(z) = sum a y K + b"),
]


def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for p in (f"/usr/share/fonts/truetype/dejavu/{name}", name):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_tower(active: int, kij: float, frame_i: int, nframes: int) -> Image.Image:
    w, h = 900, 1100
    img = Image.new("RGB", (w, h), "#0e1116")
    d = ImageDraw.Draw(img)
    d.text((36, 28), "MK-1  MOVING TOWER", font=_font(28, True), fill="#f4f7fb")
    d.text((36, 68), "one pair climbing the kernel pipeline", font=_font(15), fill="#9aa4b2")
    d.text((36, 96), f"frame {frame_i + 1:02d} / {nframes}    K(x, x') = {kij:.4f}", font=_font(15), fill="#e6b35a")
    top, block_h, gap = 150, 100, 12
    for i, (name, detail) in enumerate(STAGES):
        y = top + i * (block_h + gap)
        on, done = i == active, i < active
        fill = "#1a3a32" if on else ("#1c2430" if done else "#141920")
        outline = "#7ee0c6" if on else ("#3d6a5c" if done else "#2c3644")
        d.rounded_rectangle((80, y, 820, y + block_h), radius=12, fill=fill, outline=outline, width=3)
        d.text((110, y + 22), f"{i:02d}   {name}", font=_font(22, True), fill="#f4f7fb" if on or done else "#6d7886")
        d.text((110, y + 58), detail, font=_font(16), fill="#7ee0c6" if on else "#9aa4b2")
        if on:
            d.ellipse((740, y + 34, 776, y + 70), fill="#7ee0c6")
    return img


def render(out_dir: Path, seed: int = 7, variant: str = "zz", frames_png: bool = False) -> np.ndarray:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    points = np.random.default_rng(seed).normal(size=(4, 2))
    k = gram(points, variant)
    np.save(out_dir / "gram.npy", k)
    kij = k[0, 1]
    n = len(STAGES)
    frames = [draw_tower(i, kij, i, n) for i in range(n)] + [draw_tower(n - 1, kij, n - 1, n)]
    if frames_png:
        for i, f in enumerate(frames[:n]):
            f.save(out_dir / f"tower_{i:02d}.png")
    frames[0].save(out_dir / "mk1-tower.gif", save_all=True, append_images=frames[1:], duration=700, loop=0)
    return k


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="mk1", description="MK-1 fidelity kernel + tower GIF")
    ap.add_argument("--out", default="artifacts/mk1", help="output directory")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--variant", choices=VARIANTS, default="zz")
    ap.add_argument("--frames", action="store_true", help="also write per-frame PNGs")
    a = ap.parse_args(argv)
    k = render(Path(a.out), a.seed, a.variant, a.frames)
    print("K =")
    print(np.array2string(k, precision=4, suppress_small=True))
    print("wrote", Path(a.out) / "mk1-tower.gif")


if __name__ == "__main__":
    main()
