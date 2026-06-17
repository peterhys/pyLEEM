---
title: 'pyLEEM: A Python package for dynamic Low-Energy Electron Microscopy data analysis'
tags:
  - Python
  - electron microscopy
  - LEEM
  - XPS
  - spectroscopy
  - materials science
  - surface science
authors:
  - name: Peter Sun
    orcid: 0000-0002-5241-100X
    affiliation: 1
  - name: Shyam Patel
    orcid: 0000-0002-2449-7918
    affiliation: 1
  - name: Chang-Yong Nam
    orcid: 0000-0002-9093-4063
    affiliation: 1
  - name: Jerzy Sadowski
    orcid: 0000-0002-4365-7796
    affiliation: 1
affiliations:
 - name: Brookhaven National Laboratory, Center for Functional Nanomaterials
   index: 1
date: June 17, 2026
bibliography: paper.bib
---

# Summary

`pyLEEM` is a Python package designed to streamline the analysis of Low-Energy Electron Microscopy (LEEM) experimental data. The package provides a unified framework for reading raw data files, performing energy calibrations, extracting spectroscopy profiles, and conducting domain-specific analyses, including X-ray photoelectron spectroscopy (XPS) peak fitting, secondary electron emission spectroscopy (SEES) energy correction, and diffused electron scattering pattern (DESP) characterization. Through modular and extensible base classes combined with batch processing capabilities, `pyLEEM` enables researchers to develop reproducible, automated analysis workflows for large-scale datasets. Using `pyLEEM` as the backend, we also provide a graphical user interface (GUI), `pyLEEM-GUI`, for direct interaction with and analysis of LEEM data.

# Statement of Need

Low-Energy Electron Microscopy (LEEM) is a full-field, surface-sensitive electron imaging technique that employs low-energy electrons (1–100 eV range) to study surface phenomena at nanometer-scale lateral resolution and millisecond temporal resolution. The combination of high lateral and temporal resolution with surface sensitivity makes it ideally suited for investigations of surface morphology and chemical dynamics [@Tromp2000jul; @Bauer2020may]. In addition to imaging, LEEM can be configured to perform reciprocal-space analysis through μLEED and integrated with photoemission electron microscopy (PEEM) to enable chemical analysis through soft X-ray-based measurements [@Sadowski2020aug; @Mandziak2018dec].

LEEM has been increasingly employed to study dynamic processes under in situ conditions, including varying temperature and pressure, enabling real-time observation of phenomena such as material growth, phase transitions, and chemical reactions. These dynamics can be probed through LEEM imaging [@Rogge2015apr; @Patel2025aug], XPS measurements [@Le2025mar], and μLEED measurements [@Cechal2025jul]. Together, these capabilities position LEEM as a uniquely versatile tool for quantitative, time-resolved surface science, capable of correlating nanoscale structure, electronic properties, and dynamics within a single sample.

These dynamic measurements generate large, multidimensional datasets that require complex instrument calibration, drift and distortion correction, and extraction and stitching of spectroscopic and kinetic data. However, current analysis workflows typically rely on manual feature extraction through ImageJ [@Schneider2012jul], manual post-processing (e.g., energy range calibration and stitching across the complete measurement stack), and manual calculations performed without utilizing the measurement metadata. These practices are time-consuming, error-prone, and lack reproducibility. `pyLEEM` addresses these challenges by providing a cohesive Python framework specifically designed for LEEM data analysis with extensibility for domain-specific applications. The software architecture implements a modular workflow that separates data I/O, image and profile extraction, domain-specific analysis, and post-processing operations. This modular and extensible design enables reproducible analysis pipelines, custom analysis development, and efficient large-scale data processing.

# State of the field

LEEM data analysis is often handled through general-purpose image analysis tools such as ImageJ. These workflows often truncate the metadata and provide limited domain-specific analysis. The domain-specific analysis often involves multiple steps, including I/O, calibration, image processing, and feature extraction, making it difficult to write plugins for the existing tools. To facilitate LEEM data analysis, we built `pyLEEM` and `pyLEEM-GUI` to provide a domain-specific Python workflow for LEEM files, metadata, calibration, spectroscopy extraction, and batch processing. For complex downstream analysis, the user can export files out to other domain-specific analysis tools such as CasaXPS for XPS and Athena for XAS.


# Software design

The `pyLEEM` package is designed to be modular, readable, and extensible. Since we are a user facility, we want the package to be easy to maintain, and we want tool managers and users to be able to write custom workflows for domain-specific operations. `pyLEEM-GUI` builds on top of `pyLEEM` to provide a simple graphical user interface for users to operate. 

Because LEEM is an image-based analysis technique, we split the workflow into three parts: I/O and metadata extraction, image processing, and data analysis. Each part of the workflow can be extended and tailored to custom operations. In `pyLEEM-GUI`, we add the functionality to display the workflow of image processing, annotation, and analysis. The complete workflow can be saved and imported, allowing tool managers to distribute domain-specific workflows to users.


# Research impact statement

`pyLEEM` and `pyLEEM-GUI` were developed at the Center for Functional Nanomaterials (CFN), a U.S. Department of Energy Office of Science user facility at Brookhaven National Laboratory. As a user facility, the CFN serves a broad community of visiting researchers, and `pyLEEM` has supported users' data analysis at both the CFN and the National Synchrotron Light Source II (NSLS-II) user facilities. Analysis based on `pyLEEM` has been presented in several conference talks.

# AI usage disclosure

Generative AI tools were not used in the software creation, documentation and paper authoring for `pyLEEM`. Generative AI tools were used to assist with the prototyping of the GUI interface for the `pyLEEM-GUI` package. AI-assisted content was reviewed manually, and the authors remain responsible for the final manuscript, software, and submission materials.

# Acknowledgements

This research is supported by the U.S. Department of Energy Office of Science Accelerate Initiative Award 2023-BNL-NC033-Fund. This research used resources (XPEEM/LEEM end station of the ESM beamline) of the Center for Functional Nanomaterials and the National Synchrotron Light Source II, which are the U.S. Department of Energy (DOE) Office of Science facilities at Brookhaven National Laboratory, under Contract No. DE-SC0012704.

# References
