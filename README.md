# Ditogachi
![](Potrometro.png)
## Open-Hardware System for Micrometric Deformation Measurement

This project presents the design and development of an open-hardware system that includes an extensometer capable of accurately measuring mechanical deformations at the micrometric scale, along with a set of open-source algorithms optimized for image analysis and the use of computer vision for the correct interpretation of the acquired data.

The system is intended for laboratory applications, teaching, and research. Priority is given to reproducibility, low cost, and easy access to the materials required for fabrication.

The source codes shared below, together with the referenced links and supporting materials under development, aim to enable anyone to build their own device for the analysis of stress, strain, and failure mechanisms.

This project combines Arduino and Python code.

## Repository content

- [`Build_Instruction`](./Build_Instruction/)
  Step-by-step instructions for the fabrication and assembly of the device.
  
- [`Operation_Instruction`](./Operation_Instruction/)
  Guidelines for proper use of the device, including calibration and safe operation.

- [`Bill_of_materials.md`](./Bill_of_materials.md)  
  Complete list of components, suppliers, and estimated costs.

- [`Software`](./Software/)
  Source code and scripts for data acquisition and analysis. Versions range from early alpha releases to version 2.0 of the code.

- [`Design_Files`](./Design_Files/) 
  Technical standards and references used in the design process (.stl files).

- [`Results`](./Results/)
  Experimental results obtained for the samples: force–elongation plots for each sample material.

- [`Complements/`](./Complements/)
  
  Supplementary documentation, including load cell characterization results and additional photographs of the system.

- [`Research_Output/`](./Research_Output/)
  
  Thesis manuscript and appendices documenting the first reported version of the system, provided as background and historical reference.

## Requirements

- 3D printer / access to a mechanical fabrication workshop
- Electronic components listed in the BOM
- Basic knowledge of instrumentation and electronics
- Software: Python (with required libraries: cv2, numpy, time, openpyxl, datetime, serial, os) / Arduino

## Instructions 

1. Consult the file [`Bill_of_materials.md`](./Bill_of_materials.md)).
2. Follow the construction instructions provided in [`Build_Instruction`](./Build_Instruction/).
3. Carefully review [`Operation_Instruction`](./Operation_Instruction/)) before operating the device.
4. Upload the firmware (.ino files) to the microcontrollers and run the Python scripts included in [`Software`](./Software/).

## Quick operation guide

1. **Setup**  
   Ensure the device is correctly assembled and all electrical connections
   are properly secured.

2. **Power on**  
   Connect the power supply and switch on the system.

3. **Operation**  
   Place the sample according to the specified orientation and initiate
   the measurement sequence using the provided software.

4. **Data acquisition**  
   Monitor real-time data on the interface and save measurement files
   after completion.

5. **Shutdown**  
   Stop the measurement, power off the device, and disconnect the power supply.

⚠️ **Important:**  
This section provides a high-level overview only.  
For calibration, safety precautions, and detailed operation procedures,
refer to [`Operation_instruction`](./Operation_instruction/).

## Project Status

- Functional prototype validated for laboratory use.
- Documentation is currently under development.
- Open to contributions.

## Licenses
<img width="211" height="109" alt="image" src="https://github.com/user-attachments/assets/82dd333d-4ac3-449e-8f60-66f543654aba" />

###### Documentation
<a href="https://github.com/GM-II/Ditogachi">Ditogachi's Documentation</a> © 2026 by <a href="https://github.com/GM-II">GM-II</a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International</a> <img width="20" height="20" margin-left="20" alt="image" style="max-width: 20;max-height:20;margin-left: 20;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" > <img width="20" height="20" margin-left="20" alt="image" style="max-width: 20;max-height:20;margin-left: 20;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg" >
