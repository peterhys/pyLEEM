# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.3.0]

### Added

- Add `analysis` module with base classes for LEEM data analysis.
    - `Analyzer` base class for single file analysis.
    - `ProfileAnalyzer` base class for line profile extraction and transformation.
    - `AnalyzerGroup` base class for batch analysis of multiple files.
    - `StitchAnalyzer` class for stitching multiple profiles together with configurable stitch points.
- Add `sees` module for Secondary Electron Energy Spectroscopy analysis.
    - `SEESAnalyzer` for analyzing secondary electron emission onset and surface potential.
    - `SEESGroup` for batch SEES analysis with automatic energy scale calibration.
- Add `amorphleed` module for amorphous LEED pattern analysis.
    - `AmorphLEEDAnalyzer` for detecting circular diffraction patterns and charging effects.
    - `AmorphLEEDGroup` for batch analysis with radius-to-voltage calibration.
    - Image preprocessing and circle detection utilities.
- Add `calibrate` module for configuration-based calibration workflows.
    - TOML configuration file support for calibration parameters.
    - Functions for reading/writing calibration results.
- Add `utils` module with utility functions.
    - `find_onset()` for detecting profile onset based on gradient analysis.
    - `find_stitch_points()` for locating stitch points between profile ranges.
    - `stitch_profiles()` for combining multiple profiles with masking.
- Comprehensive test suite additions.
    - `test_utils.py` with 19 tests covering all utility functions.
    - `test_analysis.py` extended with 17 tests for `StitchAnalyzer` class.
    - All existing tests updated to match new API changes.

### Changed

- Rename `calibration.py` to `calibrate.py`.
- Rename `se.py` to `sees.py`.
- Update `metadata`, `metainfo`, `reader`, `roi`, and `xps` modules.
- **Breaking**: Change `fit_xps()` parameter order from `(profile, abscissa, constraints, num_peaks, baseline)` to `(profile, abscissa, baseline, peak_labels, constraints)`.
- **Breaking**: Change `stitch_profiles()` parameter order from `(profiles, abscissas, mask_points)` to `(abscissas, profiles, mask_points)` for consistency.
- **Breaking**: `StitchAnalyzer` now uses `ordinate` and `abscissa` attributes instead of `profile` for consistency with `ProfileAnalyzer`.
- Update `StitchAnalyzer` to add sorting and descending order support for stitched profiles.
- Update `StitchAnalyzer` to store `stitch_points` attribute.
- Refactore `StitchAnalyzer` validation logic into separate `validate_analyzers()` method.
- Update test suite with new test files for `amorphleed`, `analysis`, `sees`, and `utils`.
- Update project documentation and README.

### Fixed

- Fixed `shirley_background` calculation method.


## [0.2.0]

- Simplify the reader class for LEEM experiments
    - ``reader.metadata`` now outputs the full metadata without the units
- Create the spectra classes
- Create the image classes


## [0.1.0]

Initial release. This version includes functionality to read raw LEEM data, and
analysis tools for LEEM XPS experiments.
