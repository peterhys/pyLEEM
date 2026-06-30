# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

Improve the repository architecture and simplify the API. Breaking changes included. See [design documentation](https://peterhys.github.io/pyLEEM/design.html) for details.

## Changed

- Reader class now takes care of raw file interaction (image and metadata).
- Analyzer now takes care of domain specific analysis.
- Analyzer class is rewritten as a base class.
- ROI inputs are now explicitly defined instead of an ROI object.
- Config class now takes care workflow configurations.
- Updated domain specific analyzers. 
- Update design documentation and add examples to README.md.

## Added

- ReaderGroup class that adds time interval to the metadata.
- Analyzer workflow now more explicit for reproducibility.
- Workflow class now can read, run, and export the configuration file and content.
- Add AreaROIs such as circle, rectangle, and ellipse.
- Add XASAnalyzer for X-ray absorption image stack analysis.

## Removed

- Remove `AnalyzerGroup` class and associated domain specific analyzers.
- Remove `StitchAnalyzer` class and moved stitch functionality to the
  spectra analyzer.

## [0.2.1]

### Added

- Add GitHub templates for issues and pull requests.
- Add GitHub Actions workflow to publish distributions to PyPI on release.

### Fixed

- Decode LEEM/UView metadata strings (FOV, image title, recipe) as Windows cp1252 
  instead of UTF-8, fixing a `UnicodeDecodeError` on the micro sign (byte 0xb5, e.g. 
  a "10um" FOV).

## [0.2.0]

LICENSE changed to BSD 3-Clause license with BNL/DOE notices.

### Changed

- Change license to BSD 3-Clause license.
- Add `NOTICE` with Brookhaven National Laboratory, U.S. Department of Energy,
  and U.S. Government rights notices.
- Change "amorphleed" module to "desp" module to more accurate describe the diffuse elastic scattering
  pattern measurement.
- Change image processing and radius detect through contour method.
- Analyzer reader class moved to class attribute.
- Move the calibration output the analyzer group for a cleaner logic. Both domain analyer and
  analyer group requires calibration parameters.
- Change `filtered_profile` method to `process_profile`
- Change `calibrate` module to `config` module.
- Change configuration file logic and calibration method for domain specific analyzers.
- Rename `analysis.py` to `analyzer.py`.
- Move `StitchAnalyzer` to `pyleem.analysis.stitch` module.
- Move domain specific modules under analysis/ submodule.

### Added

- Add convolution based (template matching) method for desp disk pattern detection

## [0.1.1]

### Fixed

- Fixed the radius detection issue where the radius does not have to be an int.


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
