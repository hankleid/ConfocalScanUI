# ConfocalScanUI Documentation
Comments, questions, reporting bugs: email **Hannah Kleidermacher (kleid @ stanford.edu)**.

## Introduction
ConfocalScanUI is a python app for executing raster scans, where position is controlled by a scanning mirror (or any motorized device with analog input) and displays data taken with a photon counter (or any device with a counter channel) at that position. The scan is displayed in real time in the user interface, with options for two different scan speeds. The scan is saved as a ```.png``` file, and the raw data is saved as a ```.json``` file, complete with various metadata. In the following sections, this document will detail the installation process for this app, a guide on usage, including customizability, and how to interpret the convenient ```.json``` file format in python.

## Installation
You will need a National Instruments Data Acquisition unit (DAQ) for communicating with hardware. You will also need to install the following python libraries into whatever environment you choose to run the program: ```numpy```, ```nidaqmx```, ```scikit-image```.
1. Install the app. From GitHub, clone the repository into any directory on your computer. If installation was successful, you should see a folder called ConfocalScanUI at the directory in which you cloned the repository.
2. In any text editor, open the ```HardwareConfig.py``` and edit the channels to correspond to your computer's own connection to the hardware. For example: In the string ```Dev1/ao1```, ```Dev1``` refers to the port on your computer to which your DAQ is connected, and ```ao1``` refers to the specific channel on the DAQ to which your hardware is connected. In the case of ```ao1```, this is **a**nalog-**o**utput channel #1 on the DAQ.
3. When choosing the two DAQ channels for the scanning mirror's x and y analog channels, please note that you may have to switch 
4. 
