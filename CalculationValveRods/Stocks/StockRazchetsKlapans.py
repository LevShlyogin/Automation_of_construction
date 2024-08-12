import numpy as np
from scipy.interpolate import interp1d
from math import pi
from models import ClapanModel

# Input parameters
Delta_part1, W_part1 = None, None
Delta_part2, W_part2 = None, None
Delta_part3, W_part3 = None, None

# Output parameters
_Delta_part1, _W_part1 = None, None
_Delta_part2, _W_part2 = None, None
_Delta_part3, _W_part3 = None, None

t_valve = ClapanModel.T0
p_valve = ClapanModel.P0
h_valve = SteamPT(p_valve * 98066.5, t_valve, 3) / 4186.8
p_deaerator = ClapanModel.Pout_1
p_ejector = ClapanModel.Pout_2

# General geometric parameters
if ClapanModel.Calc_type == 0:
    r = ClapanModel.r_inlet / 1000  # Radius of inlet rounding or chamfer size
    delt = ClapanModel.delt_b_s / 1000  # Radial clearance
    d = ClapanModel.D_stem / 1000  # Stem diameter
    L1 = ClapanModel.L1_b / 1000  # Length of section 1
    L2 = ClapanModel.L2_b / 1000  # Length of section 2
    L3 = ClapanModel.L3_b / 1000  # Length of section 3
else:
    r = ClapanModel.r_inlet_DB / 1000
    delt = ClapanModel.delt_DB / 1000
    d = ClapanModel.D_stem_DB / 1000
    L1 = ClapanModel.L1_DB / 1000
    L2 = ClapanModel.L2_DB / 1000
    L3 = ClapanModel.L3_DB / 1000

Z = ClapanModel.Z_valve  # Number of valves
k_prop = r / (delt * 2)  # Proportionality coefficient
f = delt * pi * d  # Clearance area


# Additional functions

# Function to calculate friction resistance coefficient
def lambda_calc(B):
    matrix_lambda = np.array([
        [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200,
         1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2500, 3000,
         4000, 5000, 6000, 8000, 10000, 15000, 20000, 30000, 40000,
         50000, 60000, 80000, 100000, 150000, 200000, 300000, 400000,
         500000, 600000, 800000, 1000000, 1500000, 2000000, 3000000,
         4000000, 5000000, 8000000, 10000000, 15000000, 20000000,
         30000000, 60000000, 80000000, 100000000],
        [0.640, 0.320, 0.213, 0.160, 0.128, 0.107, 0.092, 0.080, 0.071,
         0.064, 0.058, 0.053, 0.049, 0.046, 0.043, 0.040, 0.038, 0.036,
         0.034, 0.032, 0.034, 0.040, 0.040, 0.038, 0.036, 0.033, 0.032,
         0.028, 0.026, 0.024, 0.022, 0.021, 0.020, 0.019, 0.018, 0.017,
         0.016, 0.015, 0.014, 0.013, 0.013, 0.012, 0.012, 0.011, 0.011,
         0.010, 0.010, 0.009, 0.009, 0.008, 0.008, 0.008, 0.007, 0.007,
         0.006, 0.006]
    ])
    f_interp = interp1d(matrix_lambda[0], matrix_lambda[1], fill_value="extrapolate")
    return f_interp(B)


# Function to calculate inlet softening coefficient
def ksi_calc(A):
    matrix_ksi = np.array([
        [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.12, 0.16, 0.20, 10.0],
        [0.50, 0.43, 0.36, 0.31, 0.26, 0.22, 0.20, 0.15, 0.09, 0.06, 0.03, 0.03]
    ])
    f_interp = interp1d(matrix_ksi[0], matrix_ksi[1], fill_value="extrapolate")
    return f_interp(A)


# Function to calculate air properties
def air_calc(A, B):
    RO = 353.089 / (A + 273.15)
    V = 1 / RO
    Din_vis = (1.7162 + A * 4.8210 / 10 ** 2 - A ** 2 * 2.17419 / 10 ** 5 - A ** 3 * 7.0665 / 10 ** 9) / 10 ** 6
    Kin_vis = (13.2 + 0.1 * A) / 10 ** 6
    return {0: RO, 1: V, 2: Din_vis, 3: Kin_vis}[B]


# Calculate inlet softening coefficient (same for all sections)
KSI = ksi_calc(k_prop)

# Определение параметров по участкам

# Определение параметров пара участка 1
if ClapanModel.Type_calc == 2:
    h_part1 = h_valve
    G_part1 = ClapanModel.G_fix1
    h_part2 = h_valve
    G_part2 = ClapanModel.G_fix2
    h_part3 = ClapanModel.h_vozd
    G_part3 = ClapanModel.G_fix3
else:
    h_part1 = h_valve
    P1_part1 = p_valve * 98066.5
    P2_part1 = p_deaerator * 98066.5
    v_part1 = steamPH(P1_part1, h_part1 * 4186.8, 4)
    t_part1 = steamPH(P1_part1, h_part1 * 4186.8, 2)
    din_vis_part1 = steamPH(P1_part1, h_part1 * 4186.8, 6)
    kin_vis_part1 = v_part1 * din_vis_part1
    Re_part1 = (W_part1 * 2 * delt) / kin_vis_part1
    Lambda_part1 = lambda_calc(Re_part1)
    ALFA_part1 = 1 / (1 + KSI + (0.5 * Lambda_part1 * L1) / delt) ** 0.5
    G_part1 = ALFA_part1 * f * ((P1_part1 ** 2 - P2_part1 ** 2) / (P1_part1 * v_part1)) ** 0.5 * 3.6
    DELT_W_part1 = W_part1 - v_part1 * G_part1 / (3.6 * f)
    if DELT_W_part1 <= 0.001:
        _W_part1 += max(0.001, Delta_part1)
        _Delta_part1 = Delta_part1
    else:
        if DELT_W_part1 >= 0.001:
            _W_part1 -= max(0.001, Delta_part1)
            _Delta_part1 = Delta_part1 * 0.9

# Определение параметров пара участка 2
h_part2 = h_valve
P1_part2 = p_deaerator * 98066.5
P2_part2 = p_ejector * 98066.5
v_part2 = steamPH(P1_part2, h_part2 * 4186.8, 4)
t_part2_ = steamPH(P1_part2, h_part2 * 4186.8, 2)
din_vis_part2 = steamPH(P1_part2, h_part2 * 4186.8, 6)
kin_vis_part2 = v_part2 * din_vis_part2
Re_part2 = (W_part2 * 2 * delt) / kin_vis_part2
Lambda_part2 = lambda_calc(Re_part2)
ALFA_part2 = 1 / (1 + KSI + (0.5 * Lambda_part2 * L2) / delt) ** 0.5
G_part2 = ALFA_part2 * f * ((P1_part2 ** 2 - P2_part2 ** 2) / (P1_part2 * v_part2)) ** 0.5 * 3.6
DELT_W_part2 = W_part2 - v_part2 * G_part2 / (3.6 * f)
if DELT_W_part2 <= 0.001:
    _W_part2 += max(0.001, Delta_part2)
    _Delta_part2 = Delta_part2
else:
    if DELT_W_part2 >= 0.001:
        _W_part2 -= max(0.001, Delta_part2)
        _Delta_part2 = Delta_part2 * 0.9

# Определение параметров пара участка 3
h_part3 = ClapanModel.h_vozd
P1_part3 = ClapanModel.p_vozd * 98066.5
P2_part3 = p_ejector * 98066.5
v_part3 = air_calc(ClapanModel.t_vozd, 1)
t_part3 = ClapanModel.t_vozd
din_vis_part3 = lambda_calc(ClapanModel.t_vozd, 2)
kin_vis_part3 = v_part3 * din_vis_part3
Re_part3 = (W_part3 * 2 * delt) / kin_vis_part3
Lambda_part3 = lambda_calc(Re_part3)
ALFA_part3 = 1 / (1 + KSI + (0.5 * Lambda_part3 * L3) / delt) ** 0.5
G_part3 = max(0.001, ALFA_part3 * f * ((P1_part3 ** 2 - P2_part3 ** 2) / (P1_part3 * v_part3)) ** 0.5 * 3.6)
DELT_W_part3 = W_part3 - v_part3 * G_part3 / (3.6 * f)
if DELT_W_part3 <= 0.001:
    _W_part3 += max(0.001, Delta_part3)
    _Delta_part3 = Delta_part3
else:
    if DELT_W_part3 >= 0.001:
        _W_part3 -= max(0.001, Delta_part3)
        _Delta_part3 = Delta_part3 * 0.9

# Определение параметров по отсосам

# Определение параметров отсоса в деаэратор
g_deaerator = (G_part1 - G_part2) * Z
h_deaerator = h_part2
t_deaerator = steamPH(p_deaerator * 98066.5, h_deaerator * 4186.8, 2)
X1 = (h_deaerator * 4186.8 - WaterPS(p_deaerator * 98066.5, 3)) / (
            SteamPS(p_deaerator * 98066.5, 3) - WaterPS(p_deaerator * 98066.5, 3))
x_deaerator = 1 if X1 > 1 else X1

# Определение параметров отсоса в эжектор уплотнений
g_ejector = (G_part2 + G_part3) * Z
if type_calc_SAM == 0:
    t_part2 = steamPH(p_ejector * 98066.5, h_part2 * 4186.8, 2)
    t_ejector = (ClapanModel.t_vozd * G_part3 + t_part2 * G_part2) / (G_part2 + G_part3)
    h_ejector = steamPT(p_ejector * 98066.5, t_ejector, 3) / 4186.8
else:
    h_ejector = (h_part2 * G_part2 + h_part3 * G_part3) / (G_part2 + G_part3)
    t_ejector = steamPH(p_ejector * 98066.5, h_ejector * 4186.8, 2)

X2 = (h_ejector * 4186.8 - WaterPS(p_ejector * 98066.5, 3)) / (
            SteamPS(p_ejector * 98066.5, 3) - WaterPS(p_ejector * 98066.5, 3))
x_ejector = 1 if X2 > 1 else X2

# Определение суммарного расхода пара на штока клапанов
g_valve = G_part1 * Z
# Определение суммарного расхода воздуха
g_vozd = G_part3 * Z

# Вывод переменных в свойства блока субмодели
ClapanModel.g_d = g_deaerator
ClapanModel.h_d = h_deaerator
ClapanModel.p_d = p_deaerator
ClapanModel.t_d = t_deaerator
ClapanModel.x_d = x_deaerator

ClapanModel.g_e = g_ejector
ClapanModel.h_e = h_ejector
ClapanModel.p_e = p_ejector
ClapanModel.t_e = t_ejector
ClapanModel.x_e = x_ejector

ClapanModel.g_valve = g_valve
ClapanModel.h_valve = h_valve
ClapanModel.p_valve = p_valve
ClapanModel.t_valve = t_valve

ClapanModel.G_part1 = G_part1
ClapanModel.H_part1 = H_part1
ClapanModel.v_part1 = v_part1
ClapanModel.P1_part1 = P1_part1
ClapanModel.T1_part1 = T_part1
ClapanModel.P2_part1 = P2_part1
ClapanModel.Re_part1 = Re_part1
ClapanModel.w_part1 = _w_part1

ClapanModel.G_part2 = G_part2
ClapanModel.H_part2 = H_part2
ClapanModel.v_part2 = v_part2
ClapanModel.P1_part2 = P1_part2
ClapanModel.T1_part2 = t_part2_
ClapanModel.P2_part2 = P2_part2
ClapanModel.Re_part2 = Re_part2
ClapanModel.w_part2 = _w_part2

ClapanModel.G_part3 = G_part3
ClapanModel.H_part3 = H_part3
ClapanModel.v_part3 = v_part3
ClapanModel.P1_part3 = P1_part3
ClapanModel.T1_part3 = T_part3
ClapanModel.P2_part3 = P2_part3
ClapanModel.Re_part3 = Re_part3
ClapanModel.w_part3 = _w_part3

ClapanModel.L1_Print = L1 * 1000
ClapanModel.L2_Print = L2 * 1000
ClapanModel.L3_Print = L3 * 1000
ClapanModel.D_Print = D * 1000
ClapanModel.delt_Print = delt * 1000
ClapanModel.f_zaz = f * 10 ** 6
