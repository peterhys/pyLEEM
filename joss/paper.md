---
title: "pyLEEM: A Python platform for dynamic Low-Energy Electron Microscopy data analysis"
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
  - name: Center for Functional Nanomaterials, Brookhaven National Laboratory
    index: 1
date: June 18, 2026
bibliography: paper.bib
---

# Summary

`pyLEEM` is a Python package designed to streamline the analysis of Low-Energy Electron Microscopy (LEEM) experimental data. The package provides a unified framework for reading raw data files, performing energy calibrations, extracting spectroscopy profiles, and conducting domain-specific analyses, including X-ray photoelectron spectroscopy (XPS) stitching, secondary electron emission spectroscopy (SEES) energy correction, and diffuse electron scattering pattern (DESP) characterization. Through a modular and extensible core architecture combined with batch processing capabilities, `pyLEEM` enables researchers to develop reproducible, automated analysis workflows for large-scale datasets. Based on the `pyLEEM` platform, we developed `pyLEEM-GUI`, a graphical user interface for interactive inspection and analysis of LEEM experimental data.

# Statement of Need

LEEM is a full-field, surface-sensitive electron imaging technique that employs low-energy electrons in the 1 -- 100 eV range to study surface phenomena at nanometer-scale lateral resolution and millisecond temporal resolution. The combination of high lateral and temporal resolution with surface sensitivity makes it ideally suited for investigations of surface morphology, chemical dynamics, and in situ material growth [@Tromp2000jul; @Bauer2020may; @Rogge2015apr; @Patel2025aug]. In addition to imaging, LEEM instruments can acquire energy-dependent spectroscopic measurements and reciprocal-space diffraction patterns, and can be integrated with photoemission electron microscopy (PEEM) to enable soft X-ray-based chemical analysis [@Sadowski2020aug; @Mandziak2018dec; @Le2025mar]. Together, these capabilities make LEEM a uniquely versatile tool for quantitative, time-resolved surface science, capable of correlating nanoscale structure, electronic properties, and dynamics within a single sample.

These dynamic measurements generate large, multidimensional datasets that require complex instrument calibration, drift and distortion correction, and extraction and stitching of spectroscopic data [@DeJong2020jun]. However, current analysis workflows typically rely on manual feature extraction through ImageJ [@Schneider2012jul] or custom scripts, manual post processing (e.g., energy range calibration and stitching across the complete measurement stack), and manual calculations performed without utilizing the measurement metadata. These practices are time-consuming, error-prone, and lack reproducibility. `pyLEEM` addresses these challenges by providing a modular and extensible Python framework with standardized input/output, image and metadata extraction, while allowing extension to domain-specific analysis and post processing. 

# State of the field

Existing tools developed for LEEM analysis remain limited and are often highly customized and domain-specific [@DeJong2020jun; @Grady2018feb]. As a result, many LEEM datasets are still analyzed using general-purpose image-analysis tools such as ImageJ [@Schneider2012jul] for image and profile extraction, together with custom scripts for data analysis, post processing, and conversion into target formats for downstream domain-specific tools. These workflows are often non-trivial, error-prone, and difficult to reproduce. In addition, existing LEEM-related tools and ad hoc workflows do not provide the backend infrastructure needed for automated analysis, large dynamic datasets, or user-defined analysis modules.

 Therefore, we developed `pyLEEM` as a new platform rather than extending existing projects. `pyLEEM` is designed first as a headless, scriptable Python library, with `pyLEEM-GUI` built on top of the same backend for interactive graphical use. This separation allows the same analysis routines to be used in automated batch workflows, reproducible scripts, and graphical user sessions.
 
# Software design

`pyLEEM` is designed as a modular and extensible Python package for LEEM-family data analysis. The key design trade-off was to create a reusable backend API, which adds upfront abstraction but makes `pyLEEM` easier to test, maintain, extend, and use in reproducible headless workflows. The package separates the workflow into three main layers: data input/output and metadata extraction, image and profile processing, and domain-specific analysis. This separation supports long-term maintainability by allowing input/output, calibration, image processing and analysis operations to be developed, tested, and updated independently. The extensible structure also allows users and facility staff to implement custom workflows for new file formats, image-processing routines, and domain-specific analysis needs. The core `pyLEEM` library is intentionally separated from the graphical user interface, so that analysis routines remain readable, testable, and usable outside interactive sessions. This backend-first design enables large-scale batch processing through scripts, notebooks, and automated workflows.

A second design goal is workflow readability and reproducibility. Calibration settings and analysis parameters are stored in human-readable configuration files and can be applied consistently across workflow steps. In `pyLEEM-GUI`, image-processing, calibration, annotation, and analysis steps can be recorded, saved, reloaded, and shared. This allows facility staff and tool managers to distribute validated analysis workflows directly to users, while users can reproduce the same sequence of operations on related datasets or future experiments.

# Research impact statement

`pyLEEM` has supported both user-facility data analysis and method development. For the core developers, the package enables rapid development, testing, and validation of new workflows and analysis algorithms, including DESP calibration and characterization. More broadly, `pyLEEM` and `pyLEEM-GUI` were developed at the Center for Functional Nanomaterials (CFN), a U.S. Department of Energy Office of Science user facility at Brookhaven National Laboratory. As a user facility, the CFN serves a broad community of visiting researchers, and `pyLEEM` has supported and continues to support users' data analysis at both the CFN and the National Synchrotron Light Source II (NSLS-II) user facilities. 

# AI usage disclosure

Generative AI tools were not used in the software creation, documentation and paper authoring for `pyLEEM`. Generative AI tools were used to assist with the prototyping of the interface for the `pyLEEM-GUI` package. The AI-assisted code was reviewed manually, and the authors remain responsible for the final software.

# Acknowledgements

This research is supported by the U.S. Department of Energy Office of Science Accelerate Initiative Award 2023-BNL-NC033-Fund. This research used resources (XPEEM/LEEM end station of the ESM beamline) of the Center for Functional Nanomaterials and the National Synchrotron Light Source II, which are the U.S. Department of Energy (DOE) Office of Science facilities at Brookhaven National Laboratory, under Contract No. DE-SC0012704.

# References
