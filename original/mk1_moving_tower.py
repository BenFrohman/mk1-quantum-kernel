"""MK-1 moving-tower flow.

Simulates a 2-qubit ZZ feature map, estimates the kernel by
compute-uncompute, and renders the pipeline as a tower whose
active stage advances with the data.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/home/workdir/artifacts/mk1")
OUT.mkdir(parents=True, exist_ok=True)

I2 = np.eye(2, dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
CNOT = np.array(
    [[1, 0, 0, 0],
     [0, 1, 0, 0],
     [0, 0, 0, 1],
     [0, 0, 1, 0]],
    dtype=complex,
)


def rz(theta):
    return np.array(
        [[np.exp(-1j * theta / 2), 0],
         [0, np.exp(1j * theta / 2)]],
        dtype=complex,
    )


def kron(*ops):
    out = np.array([[1]], dtype=complex)
    for op in ops:
        out = np.kron(out, op)
    return out


def feature_map(x):
    """ZZ map on 2 qubits. x is length 2, scaled into radians."""
    u = kron(H, H)
    u = kron(rz(2 * x[0]), rz(2 * x[1])) @ u
    u = CNOT @ u
    u = kron(rz(2 * x[0] * x[1]), I2) @ u
    u = CNOT @ u
    return u


def kernel(x, xp):
    """P(00) after U(x) then U(xp)^dagger. Exact statevector."""
    psi = feature_map(xp).conj().T @ feature_map(x) @ np.array([1, 0, 0, 0], dtype=complex)
    return float(np.abs(psi[0]) ** 2)


def gram(points):
    m = len(points)
    k = np.eye(m)
    for i in range(m):
        for j in range(i + 1, m):
            k[i, j] = k[j, i] = kernel(points[i], points[j])
    return k


STAGES = [
    ("HOST", "scale x, queue pair"),
    ("LATCH", "reset |0>^n"),
    ("MAP", "U_phi(x)"),
    ("UNCOMPUTE", "U_phi(x')^dag"),
    ("SHOTS", "count P(0...0)"),
    ("GRAM", "write K_ij"),
    ("DUAL", "fit alpha, b"),
    ("DECIDE", "f(z) = sum a y K + b"),
]


def font(size, bold=False):
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    return ImageFont.truetype(path, size)


def draw_tower(active, kij, frame_i, nframes):
    w, h = 900, 1100
    img = Image.new("RGB", (w, h), "#0e1116")
    d = ImageDraw.Draw(img)
    d.text((36, 28), "MK-1  MOVING TOWER", font=font(28, True), fill="#f4f7fb")
    d.text((36, 68), "flow state  ·  one pair climbing the kernel engine", font=font(15), fill="#9aa4b2")
    d.text((36, 96), f"frame {frame_i + 1:02d} / {nframes}    K(x, x') = {kij:.4f}", font=font(15), fill="#e6b35a")

    top = 150
    block_h = 100
    gap = 12
    for i, (name, detail) in enumerate(STAGES):
        y = top + i * (block_h + gap)
        on = i == active
        done = i < active
        fill = "#1a3a32" if on else ("#1c2430" if done else "#141920")
        outline = "#7ee0c6" if on else ("#3d6a5c" if done else "#2c3644")
        d.rounded_rectangle((80, y, 820, y + block_h), radius=12, fill=fill, outline=outline, width=3)
        d.text((110, y + 22), f"{i:02d}   {name}", font=font(22, True), fill="#f4f7fb" if on or done else "#6d7886")
        d.text((110, y + 58), detail, font=font(16), fill="#7ee0c6" if on else "#9aa4b2")
        if on:
            d.ellipse((740, y + 34, 776, y + 70), fill="#7ee0c6")
    img.save(OUT / f"tower_{frame_i:02d}.png")
    return img


def main():
    rng = np.random.default_rng(7)
    points = rng.normal(size=(4, 2))
    k = gram(points)
    np.save(OUT / "gram.npy", k)
    kij = k[0, 1]

    frames = []
    for i in range(len(STAGES)):
        frames.append(draw_tower(i, kij, i, len(STAGES)))
    # hold the decision stage
    frames.append(draw_tower(len(STAGES) - 1, kij, len(STAGES) - 1, len(STAGES)))
    frames[0].save(
        OUT / "mk1-tower.gif",
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
    )
    print("K =")
    print(np.array2string(k, precision=4, suppress_small=True))
    print("wrote", OUT / "mk1-tower.gif")


if __name__ == "__main__":
    main()
