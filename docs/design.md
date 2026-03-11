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
Currently, only the line ROI is supported.

## Analyzer class

The base unit of pyLEEM analysis is an `Analyzer` object, which converts a LEEM data file into
a set of analyses through the `reader` instance. The basic `Analyzer` class provides simple
analysis tools for raw data.

For domain-specific analysis, `Analyzer` subclasses can be created. Currently, the
available subclasses are:
- `SEESAnalyzer`: Secondary Electron Energy Spectroscopy (SEES) analyzer.
- `DESPAnalyzer`: Diffuse Elastic Scattering Pattern (DESP) analyzer.
- `XPSAnalyzer`: X-ray Photoelectron Spectroscopy (XPS) analyzer.
- `StitchAnalyzer`: Combines multiple overlapping spectra into a single continuous spectrum.

These subclasses provide domain-specific analysis tools for the raw data.

## AnalyzerGroup class

The `AnalyzerGroup` class is used to perform batch analysis on a set of LEEM data files.
The input of the class is a list of raw files. The class takes care of
the time stamp parsing and plotting. Domain specific analysis tools are provided by the
subclasses.

The available subclasses are:
- `SEESGroup`: Secondary Electron Energy Spectroscopy (SEES) group.
- `DESPGroup`: Diffuse Elastic Scattering Pattern (DESP) group.
- `XPSGroup`: X-ray Photoelectron Spectroscopy (XPS) group.
