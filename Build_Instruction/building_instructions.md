# Building Instructions

## Introduction

Ditogachi is an open-hardware platform designed for micrometric deformation measurements during uniaxial tensile testing. The system combines mechanical loading, optical imaging, electronic instrumentation, and computer vision algorithms to enable simultaneous force and deformation measurements.

The hardware architecture can be divided into four main subsystems:

1. **Tensile loading system**, responsible for generating the mechanical load applied to the specimen.
2. **Microscopic imaging system**, responsible for acquiring high-magnification images for deformation measurements.
3. **Electronic instrumentation system**, responsible for motor control, force acquisition, and synchronization.
4. **Macroscopic imaging system**, consisting of an external camera mounted on a tripod when mesoscopic observations are required.

The assembly videos provided in this section cover the fabrication and assembly of the two principal mechanical subsystems: the tensile loading hardware and the microscopic imaging support structure.

Additional information regarding electronics, illumination, software, and operation can be found in the corresponding sections of this repository.

---

## System Architecture

The complete system is composed of:

- Tensile loading module.
- Microscope support and positioning module.
- Load-cell-based force measurement system.
- Motor control electronics.
- Illumination system.
- Optional macroscopic camera mounted on an external tripod.
- Computer vision and data acquisition software.

---

## 1. Optical System Support and Positioning Module

This module provides mechanical support for the microscope camera used during deformation measurements. The structure ensures stability during testing while allowing positioning and fine adjustment of the optical system relative to the specimen.

The microscope support is designed to minimize vibrations and facilitate precise focusing and alignment during image acquisition.

### Assembly Video

https://youtu.be/Ijc06AQWEIM

<sub>
<strong>Credits:</strong><br>
Assembly and Editing: Santiago Rosas Mogollón<br>
Filming and Review: Serena Triviño Sáenz
</sub>

### Description

This video presents the complete assembly procedure for the microscope support structure, including the installation of positioning mechanisms and adjustment components required for stable image acquisition.

### Notes

- This module supports the **microscopic imaging system only**.
- The macroscopic camera used in some experiments is not part of this assembly and can be mounted independently using a conventional laboratory tripod.  

---

## 2. Tensile Loading Module

This module constitutes the mechanical core of Ditogachi. It generates the tensile load applied to the specimen and provides the structural framework required for uniaxial testing.

The system incorporates a motor-driven actuation mechanism, specimen grips, and a load cell capable of measuring forces during testing.

### Assembly Video

https://youtu.be/UyuWO1eD-a8

<sub>
<strong>Credits:</strong><br>
Assembly and Editing: Santiago Rosas Mogollón<br>
Filming and Review: Serena Triviño Sáenz
</sub>

### Description

This video presents the complete assembly procedure for the tensile loading hardware, including structural elements, actuation components, specimen grips, and force-measurement integration.

---

## Electronics and Wiring

The assembly of the electronic instrumentation is documented separately through wiring diagrams and circuit documentation included in this repository.

These documents describe:

- Motor control connections.
- Load cell instrumentation.
- Arduino-based control hardware.
- Power distribution.
- Communication interfaces.

Users should review the electronic documentation before operating the system.

---


## License

Build instruction videos and accompanying documentation are distributed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

https://creativecommons.org/licenses/by/4.0/
