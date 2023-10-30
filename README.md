# ConfocalScanUI Documentation
Comments, questions, reporting bugs: email **Hannah Kleidermacher (kleid @ stanford.edu)**.

## Introduction
ConfocalScanUI is a python app for executing raster scans, where position is controlled by a scanning mirror (or any motorized device with analog input) and displays data taken with a photon counter (or any device with a counter channel) at that position. The scan is displayed in real time in the user interface, with options for two different scan speeds. The scan is saved as a ```.png``` file, and the raw data is saved as a ```.json``` file, complete with various metadata. In the following sections, this document will detail the installation process for this app, a guide on usage, including customizability, and how to interpret the convenient ```.json``` file format in python.

## Installation
You will need a National Instruments Data Acquisition unit (DAQ) for communicating with hardware.
