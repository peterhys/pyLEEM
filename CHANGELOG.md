# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0]

### Changed

- Change 'amorphleed' module to 'desp' module to more accurate describe the diffuse elastic scattering
  pattern measurement

## [0.1.0]

### Added

- `analysis` module: `Analyzer`, `ProfileAnalyzer`, `AnalyzerGroup`, and `StitchAnalyzer` base classes.
- `sees` module: `SEESAnalyzer` and `SEESGroup` for secondary electron energy spectroscopy.
- `amorphleed` module: `AmorphLEEDAnalyzer` and `AmorphLEEDGroup` for amorphous LEED pattern analysis.
- `calibrate` module: TOML-based calibration workflow with read/write helpers.
- `utils` module: `find_onset()`, `find_stitch_points()`, and `stitch_profiles()`.

### Changed

- Rename `calibration.py` to `calibrate.py`.
- Rename `se.py` to `sees.py`.
- Remove `h5` raw file and roi output.


### Fixed

- Fix `shirley_background` calculation method.


## [0.0.1]

Initial release. This version includes functionality to read raw LEEM data, and
analysis tools for LEEM XPS experiments.

- Create the spectra classes
- Create the image classes
