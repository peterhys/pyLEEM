# Drift Correction

Drift correction aligns an image stack by estimating pairwise shifts, reducing
them to absolute correction shifts, and applying those shifts to the original
images.

The drift-correction workflow adapts the pairwise image-registration approach
described by de Jong et al., *Ultramicroscopy* 213, 112913 (2020),
DOI: [10.1016/j.ultramic.2019.112913](https://doi.org/10.1016/j.ultramic.2019.112913).

If you use the drift-correction workflow in published work, please cite:

  de Jong et al., Ultramicroscopy 213, 112913 (2020),
  DOI: 10.1016/j.ultramic.2019.112913.

On top of the algorithm, pyLEEM provides additional features to improve the
performance and the workflow.

## Tuning

The implemented drift correction prioritizes LEEM experiments, where only
transformational corrections (x, y shifts) are applied. The drift correction
varies from experiment to experiment, here we outline the parameters and how
each would change the drift correction behavior.

Parameters for drift correction (`calculate_drift`):

- `sigma`: Gaussian smoothing. 
  - For noisy data, increase `sigma`. Value too high would blur features.
- `crop_size`: Center crop used for drift correction.
  - Can increase the drift correction speed.
- `upsample_factor`: Pixel precision for correlation and shift.
  - 10 means 0.1 pixel precision.
  - Larger values are slower and usually only help after the pair registration is already stable.
- `max_workers`: Number of worker threads for multi-threading.
  - Recommend to 4 - 8 depending on the CPU.
- `chunk_size`: Number of image-pairs per threaded task.
  - Recommend to 16 - 64 depending on the CPU.
- `max_distance`: Pairing window size.
  - 1 means correct image based on the adjacent frames.
  - If there are a lot of frames with contrast or feature change, use higher values to calculate the overall correlation.
  - Higher values are much slower (1 is log(n), 2 is log(n^2), 3 is log(n^3), etc.)
  - Higher values may results in jitters depends on the data.
- `reference_index`: Center frame to reference the shift.
  - The reference index is important especially for ROI selection.

Parameters for the shift application (`apply_shifts`):

- `expand`: Whether to expand the canvas to fit all shifted content.
  - By default, the shifted content is cropped at the original boundary.
- `cval`: Fill value for empty pixels introduced by shifting.
  - Defaults to 0 (black).
