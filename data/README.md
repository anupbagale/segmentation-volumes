# Data

| File | What it is |
|---|---|
| `T1.mgz` | T1-weighted MRI of the MNE "sample" subject |
| `aseg.mgz` | FreeSurfer subcortical segmentation (aseg) of the same subject, one integer label per voxel |
| `aseg_lut.txt` | Name and colour of every label in `aseg.mgz`, in the format of FreeSurfer's `FreeSurferColorLUT.txt` |

Both MRI files are downsampled copies (86 x 86 x 86 voxels, 3 mm) taken from the
[MNE-Python testing data](https://github.com/mne-tools/mne-testing-data/tree/master/subjects/sample/mri).
The MNE sample dataset is released under CC0 ([OpenNeuro ds000248](https://openneuro.org/datasets/ds000248)).
