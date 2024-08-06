WaterProperties. ML Automation of construction
===============

Introduction
---------------

This library is a collection of functions for calculating various thermodynamic properties of water and steam. The library is based on the international formulation IAPWS (International Association for the Properties of Water and Steam) and allows for the calculation of properties of water and steam over a wide range of temperatures and pressures.

![SchemeWork.png](https://habrastorage.org/r/w1560/getpro/habr/upload_files/b71/af3/fda/b71af3fda61c88ee3a6f3d3e6149554b.jpg)

The module also is based on the following article:\
[Library of functions for calculating the properties of water and steam](https://habr.com/ru/articles/712656/)\
Which is written in the Visual Basic programming language.

Quick Guide
---------------

Install library, use the `pip install WSAProperties` construct.\
Using the library is as simple and convenient as possible:

First, import everything or needed functions from the library (use the `from WSAProperties import *` construct).\
Second, you can use any function from the library (use the `WSAProperties.Any_Function` construct).

### Example Usage

```python
import WSAProperties

t = 25  # temperature in degrees Celsius
p = 101325  # pressure in Pascals

# calculate the density of water
density = WSAProperties.Density(t, p)
print("Density of water:", density, "kg/m^3")

# calculate the specific entropy of water
entropy = WSAProperties.Specific_Entropy(t, p)
print("Specific entropy of water:", entropy, "J/kg·K")
```

### Functions

The purpose of each of the functions is contained directly in the name.

#### _Water and steam part_
The part of water and steam in library includes the following functions:

* `Region(t, p)`
* `Density3(t, p)`
* `Helmholtz_Energy(t, ro)`
* `Pressure3(t, ro)`
* `Specific_Energy3(t, ro)`
* `Specific_Entropy3(t, ro)`
* `Specific_Enthalpy3(t, ro)`
* `Heat_Isobary3(t, ro)`
* `Heat_Isochorny3(t, ro)`
* `Sound_Speed3(t, ro)`
* `Gibbs_Energy(t, p)`
* `Specific_Volume(t, p)`
* `Density(t, p)`
* `Specific_Energy(t, p)`
* `Specific_Entropy(t, p)`
* `Specific_Enthalpy(t, p)`
* `Heat_Capacity_Isobaric(t, p)`
* `Heat_Capacity_Isochoric(t, p)`
* `Speed_Sound(t, p)`
* `Saturation_Temperature(p)`
* `Saturation_Pressure(t)`
* `Border_Temperature(p)`
* `Border_Pressure(t)`
* `Viscosity(t, p)`
* `Density_MI(t, p)`
* `Specific_Enthalpy_MI(t, p)`
* `JF(t, p, Trigger, reg)`\

#### _Air Part_
Library also have formuls and thermal properties calculations for air:
* `lambda_calc(B)`
* `ksi_calc(A)`
* `air_calc(A, B)`

References
--------------

* [Library of functions for calculating the properties of water and steam](https://habr.com/ru/articles/712656/)
* [IAPWS](http://www.iapws.org/)
* [IAPWS Documentation](http://www.iapws.org/relguide/IAPWS-95.html)

#### Mikhail and Lev's DevTeam
