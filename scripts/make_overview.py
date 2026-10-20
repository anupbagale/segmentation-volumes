"""Make docs/overview.png, the figure at the top of the README.

Run from the repository root:  python scripts/make_overview.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from label_volumes import label_volumes, read_lut  # noqa: E402

out = root / "docs" / "overview.png"
out.parent.mkdir(exist_ok=True)

seg_img = nib.load(root / "data" / "aseg.mgz")
names = read_lut(root / "data" / "aseg_lut.txt")
rows = {r["name"]: r["volume_cm3"] for r in label_volumes(seg_img, names)}

# colour table for the slice
table = np.zeros((256, 4))
for line in open(root / "data" / "aseg_lut.txt"):
    p = line.split()
    if p and not p[0].startswith("#"):
        table[int(p[0])] = [int(p[2]) / 255, int(p[3]) / 255, int(p[4]) / 255, 0 if p[0] == "0" else 0.7]

t1 = np.asarray(nib.as_closest_canonical(nib.load(root / "data" / "T1.mgz")).dataobj)
seg = np.asarray(nib.as_closest_canonical(seg_img).dataobj).astype(int)

pairs = sorted(
    {n[5:] for n in rows if n.startswith("Left-") and "Right-" + n[5:] in rows},
    key=lambda s: -rows["Left-" + s],
)

fig, ax = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1, 1.4]})
ax[0].imshow(np.take(t1, 43, axis=1).T, cmap="gray", origin="lower")
ax[0].imshow(table[np.take(seg, 43, axis=1).T], origin="lower")
ax[0].set_title("FreeSurfer segmentation (coronal slice)")
ax[0].axis("off")

y = np.arange(len(pairs))
ax[1].barh(y - 0.2, [rows["Left-" + s] for s in pairs], height=0.4, color="#2a78d6", label="left")
ax[1].barh(y + 0.2, [rows["Right-" + s] for s in pairs], height=0.4, color="#eb6834", label="right")
ax[1].set_yticks(y, pairs)
ax[1].invert_yaxis()
ax[1].set_xscale("log")
ax[1].set_xlabel("volume (cm³, log scale)")
ax[1].set_title("Volume of each structure")
ax[1].legend(loc="lower right")
for side in ("top", "right"):
    ax[1].spines[side].set_visible(False)

fig.tight_layout()
fig.savefig(out, dpi=110, bbox_inches="tight")
print("wrote", out)
