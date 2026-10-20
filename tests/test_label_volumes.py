import csv
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from label_volumes import label_volumes, main, read_lut, voxel_volume, write_csv  # noqa: E402


def make_image(data, voxel=(1.0, 1.0, 1.0), kind="nifti"):
    affine = np.diag(list(voxel) + [1.0])
    if kind == "mgz":
        return nib.MGHImage(data.astype(np.int32), affine)
    return nib.Nifti1Image(data, affine)


def test_counts_and_volumes():
    data = np.zeros((10, 10, 10), dtype=np.uint8)
    data[:2] = 5            # 200 voxels
    data[5, 5, 5] = 7       # 1 voxel
    rows = label_volumes(make_image(data, voxel=(2.0, 2.0, 3.0)))   # 12 mm³ per voxel
    assert [r["label"] for r in rows] == [5, 7]
    assert [r["voxels"] for r in rows] == [200, 1]
    assert [r["volume_mm3"] for r in rows] == [2400.0, 12.0]
    assert rows[0]["volume_cm3"] == 2.4


def test_background_optional():
    data = np.zeros((4, 4, 4), dtype=np.int16)
    data[0, 0, 0] = 1
    assert [r["label"] for r in label_volumes(make_image(data))] == [1]
    assert [r["label"] for r in label_volumes(make_image(data), include_background=True)] == [0, 1]


def test_total_equals_field_of_view():
    rng = np.random.default_rng(0)
    data = rng.integers(0, 50, (8, 9, 10)).astype(np.int16)
    img = make_image(data, voxel=(1.5, 1.5, 1.5))
    rows = label_volumes(img, include_background=True)
    assert sum(r["volume_mm3"] for r in rows) == pytest.approx(data.size * 1.5 ** 3)


def test_float_labels_accepted_if_whole_numbers():
    data = np.zeros((3, 3, 3), dtype=np.float32)
    data[1, 1, 1] = 17.0
    assert label_volumes(make_image(data))[0]["label"] == 17


def test_rejects_non_integer_labels():
    data = np.full((3, 3, 3), 0.5, dtype=np.float32)
    with pytest.raises(ValueError):
        label_volumes(make_image(data))


def test_voxel_volume_ignores_time_axis():
    img = nib.Nifti1Image(np.zeros((2, 2, 2, 5), dtype=np.float32), np.diag([2.0, 2.0, 2.0, 1.0]))
    img.header.set_zooms((2.0, 2.0, 2.0, 3.0))
    assert voxel_volume(img) == 8.0


def test_names_from_lookup_table():
    names = read_lut(ROOT / "data" / "aseg_lut.txt")
    assert names[17] == "Left-Hippocampus"
    data = np.zeros((3, 3, 3), dtype=np.uint8)
    data[0, 0, 0] = 17
    assert label_volumes(make_image(data), names)[0]["name"] == "Left-Hippocampus"


def test_sample_data_and_command_line(tmp_path):
    out = tmp_path / "volumes.csv"
    main([str(ROOT / "data" / "aseg.mgz"), "--lut", str(ROOT / "data" / "aseg_lut.txt"), "-o", str(out)])
    with open(out) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 45                                  # 46 labels minus background
    by_name = {r["name"]: r for r in rows}
    assert float(by_name["Left-Cerebral-White-Matter"]["volume_mm3"]) == int(by_name["Left-Cerebral-White-Matter"]["voxels"]) * 27


def test_mgz_and_csv_round_trip(tmp_path):
    data = np.zeros((5, 5, 5), dtype=np.int32)
    data[1:3, 1:3, 1:3] = 2
    img = make_image(data, kind="mgz")
    path = tmp_path / "labels.mgz"
    nib.save(img, path)
    rows = label_volumes(nib.load(path))
    write_csv(rows, tmp_path / "v.csv")
    assert (tmp_path / "v.csv").read_text().splitlines()[1] == "2,,8,8.0,0.008"
