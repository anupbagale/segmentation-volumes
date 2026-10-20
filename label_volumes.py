"""Measure the volume of every label in a 3D label image.

Works with any image nibabel can read (.nii, .nii.gz, .mgz). Each voxel holds an integer label;
the volume of a label is the number of its voxels times the volume of one voxel. Names can be
added from a FreeSurfer-style lookup table (lines of ``label name R G B A``).

Command line use:

    python label_volumes.py aseg.mgz
    python label_volumes.py aseg.mgz --lut aseg_lut.txt --output volumes.csv
"""

import argparse
import csv
import sys

import nibabel as nib
import numpy as np


def read_lut(path):
    """Return {label: name} from a FreeSurfer-style colour lookup table."""
    names = {}
    with open(path) as f:
        for line in f:
            parts = line.split()
            if not parts or parts[0].startswith("#"):
                continue
            names[int(parts[0])] = parts[1]
    return names


def voxel_volume(img):
    """Volume of one voxel in mm³, from the first three voxel sizes in the header."""
    return float(np.prod(img.header.get_zooms()[:3]))


def label_volumes(img, names=None, include_background=False):
    """Return one row per label: label, name, voxel count, volume in mm³ and cm³."""
    data = np.asarray(img.dataobj)
    if data.ndim != 3:
        raise ValueError(f"expected a 3D label image, got shape {data.shape}")
    if not np.issubdtype(data.dtype, np.integer):
        if not np.all(data == np.round(data)):
            raise ValueError("label image contains non-integer values")
    labels = data.astype(np.int64)
    if labels.min() < 0:
        raise ValueError("labels must not be negative")

    counts = np.bincount(labels.ravel())
    vox = voxel_volume(img)
    rows = []
    for label in np.flatnonzero(counts):
        if label == 0 and not include_background:
            continue
        mm3 = counts[label] * vox
        rows.append({
            "label": int(label),
            "name": (names or {}).get(int(label), ""),
            "voxels": int(counts[label]),
            "volume_mm3": round(mm3, 3),
            "volume_cm3": round(mm3 / 1000, 4),
        })
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "name", "voxels", "volume_mm3", "volume_cm3"])
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Volume of every label in a 3D label image.")
    parser.add_argument("image", help="label image (.nii, .nii.gz, .mgz)")
    parser.add_argument("--lut", help="lookup table with label names")
    parser.add_argument("--output", "-o", help="write the table to this CSV file")
    parser.add_argument("--background", action="store_true", help="also report label 0")
    args = parser.parse_args(argv)

    img = nib.load(args.image)
    names = read_lut(args.lut) if args.lut else None
    rows = label_volumes(img, names, include_background=args.background)

    if args.output:
        write_csv(rows, args.output)
        print(f"wrote {len(rows)} labels to {args.output}")
    else:
        size = " x ".join(f"{z:g}" for z in img.header.get_zooms()[:3])
        print(f"voxel size {size} mm, one voxel = {voxel_volume(img):g} mm³")
        print(f"{'label':>5}  {'name':<30} {'voxels':>8} {'volume (mm³)':>13}")
        for r in rows:
            print(f"{r['label']:>5}  {r['name']:<30} {r['voxels']:>8} {r['volume_mm3']:>13.1f}")
        total = sum(r["volume_mm3"] for r in rows if r["label"] != 0)
        print(f"total of all non-zero labels: {total / 1000:.1f} cm³")


if __name__ == "__main__":
    sys.exit(main())
