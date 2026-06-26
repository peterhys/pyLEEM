# Design

## Overview

pyLEEM is a Python toolkit for analyzing Low Energy Electron Microscopy (LEEM) data.
It provides tools for reading LEEM metadata and raw data, and for calibrating and
analyzing X-ray Photoelectron Spectroscopy (XPS), Secondary Electron Energy Spectroscopy (SEES),
and Diffuse Elastic Scattering Pattern (DESP).

Additional tools include stitching that can create a continuous spectrum from overlapping spectra.

The package is designed to be modular and extendable.

## Reader class

The `Reader` class takes care of converting a LEEM file into a Python-readable format, and
parses all the metadata from the file. Currently, the only available reader is the
`UViewReader` class, used to read UView `.dat` files. Custom readers can be
easily implemented to support other file formats.

## ROI class

The `ROI` class is used to define the region of interest (ROI) for the analysis.
ROI can either be manually defined or parsed from an ImageJ ROI file. Calibrated
ROI stores calibration parameters for the region of interest. For LEEM, the pixel per eV
and peak shift values are used to convert the pixel profile to the proper energy scale.

## Analyzer class

The base unit of pyLEEM analysis is an `Analyzer` object.
The basic `Analyzer` class provides simple analysis tools for raw data.

For domain-specific analysis, `Analyzer` subclasses can be created. Currently, the
available subclasses are:
- `SEESAnalyzer`: Secondary Electron Energy Spectroscopy (SEES) analyzer.
- `DESPAnalyzer`: Diffuse Elastic Scattering Pattern (DESP) analyzer.
- `XPSAnalyzer`: X-ray Photoelectron Spectroscopy (XPS) analyzer.

These subclasses provide domain-specific analysis tools for the raw data.

## Workflow

For reproducibility, workflow can be used to build readers, ROI, and analyzer
objects, and define tasks. Workflow can be loaded and saved from
configuration TOML files.

Users can instantiate readers, ROI, and analyzers directly without Config or
Workflow. Users use Workflow when they want standardized calibration,
reproducible input, parameters, and streamlined I/O.
