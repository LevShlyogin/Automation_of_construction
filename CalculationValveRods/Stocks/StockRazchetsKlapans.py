import numpy as np
from scipy.interpolate import interp1d
from math import pi
from models import ClapanModel
from WSAProperties import steamPT, steamPH # Correct need

''' Functions PART '''


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


''' Variables PART '''

# # Input parameters - constant
# Delta_part1, W_part1 = None, None
# Delta_part2, W_part2 = None, None
# Delta_part3, W_part3 = None, None
#
# # Output parameters - constant
# _Delta_part1, _W_part1 = None, None
# _Delta_part2, _W_part2 = None, None
# _Delta_part3, _W_part3 = None, None

temperature_start_valve = ClapanModel.T0
pressure_start_valve = ClapanModel.P0
enthalpy_steam = steamPT(pressure_start_valve * 98066.5, temperature_start_valve, 3) / 4186.8
pressure_deaerator = ClapanModel.Pout_1
pressure_ejector = ClapanModel.Pout_2

# General geometric parameters
# if ClapanModel.Calc_type == 0:
#     r = ClapanModel.r_inlet / 1000  # Radius of inlet rounding or chamfer size
#     delt = ClapanModel.delt_b_s / 1000  # Radial clearance
#     d = ClapanModel.D_stem / 1000  # Stem diameter
#     L1 = ClapanModel.L1_b / 1000  # Length of section 1
#     L2 = ClapanModel.L2_b / 1000  # Length of section 2
#     L3 = ClapanModel.L3_b / 1000  # Length of section 3
# else:

radius_rounding = ClapanModel.r_inlet_DB / 1000 if ClapanModel.r_inlet_DB is not None else None
delta_clearance = ClapanModel.delt_DB / 1000 if ClapanModel.delt_DB is not None else None
diameter_stock = ClapanModel.D_stem_DB / 1000 if ClapanModel.D_stem_DB is not None else None
len_part1 = ClapanModel.L1_DB / 1000 if ClapanModel.L1_DB is not None else None
len_part2 = ClapanModel.L2_DB / 1000 if ClapanModel.L2_DB is not None else None
len_part3 = ClapanModel.L3_DB / 1000 if ClapanModel.L3_DB is not None else None
len_part4 = ClapanModel.L4_DB / 1000 if ClapanModel.L4_DB is not None else None
len_part5 = ClapanModel.L5_DB / 1000 if ClapanModel.L5_DB is not None else None

count_valves = ClapanModel.Z_valve  # Number of valves
proportional_coef = radius_rounding / (delta_clearance * 2)  # Proportionality coefficient
S = delta_clearance * pi * diameter_stock  # Clearance area

# Calculate inlet softening coefficient (same for all sections)
KSI = ksi_calc(proportional_coef)

''' Defining parameters by parts '''


# Функция для определения параметров пара участка
def steam_props_detection(P1, P2, v, din_vis, len_part, W=50):
    kin_vis = v * din_vis
    delta_speed = 1
    while not (-0.001 < delta_speed < 0.001):
        Re = (W * 2 * delta_clearance) / kin_vis
        ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
        G = ALFA * S * ((P1 ** 2 - P2 ** 2) / (P1 * v)) ** 0.5 * 3.6
        delta_speed = W - v * G / (3.6 * S)
        if delta_speed <= 0.001:
            W += max(0.001, W)
        elif delta_speed >= 0.001:
            W -= max(0.001, W * 0.9)
    Re = (W * 2 * delta_clearance) / kin_vis
    ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
    G = ALFA * S * ((P1 ** 2 - P2 ** 2) / (P1 * v)) ** 0.5 * 3.6
    return G


# Функция для определения параметров воздуха для последнего участка
def air_props_detection(P1, P2, v, din_vis, len_part, W=50):
    kin_vis = v * din_vis
    delta_speed = 1
    while not (-0.001 < delta_speed < 0.001):
        Re = (W * 2 * delta_clearance) / kin_vis
        ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
        G = max(0.001, ALFA * S * ((P1 ** 2 - P2 ** 2) / (P1 * v)) ** 0.5 * 3.6)
        delta_speed = W - v * G / (3.6 * S)
        if delta_speed <= 0.001:
            W += max(0.001, W)
        elif delta_speed >= 0.001:
            W -= max(0.001, W * 0.9)
    Re = (W * 2 * delta_clearance) / kin_vis
    ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
    G = max(0.001, ALFA * S * ((P1 ** 2 - P2 ** 2) / (P1 * v)) ** 0.5 * 3.6)
    return G


# Определение параметров пара участка 1
if len_part1 is not None and len_part2 is not None:
    # h_part1 = enthalpy_steam
    P1_part1 = pressure_start_valve * 98066.5
    P2_part1 = pressure_deaerator * 98066.5
    v_part1 = steamPH(P1_part1, enthalpy_steam * 4186.8, 4)
    # t_part1 = steamPH(P1_part1, enthalpy_steam * 4186.8, 2)
    din_vis_part1 = steamPH(P1_part1, enthalpy_steam * 4186.8, 6)
    steam_props_detection(P1_part1, P2_part1, v_part1, din_vis_part1, len_part1)
else:
    # air_props_detection()
    pass

# Определение параметров пара участка 2
if len_part2 is not None and len_part3 is not None:
    # h_part2 = enthalpy_steam
    # P1_part2 = pressure_start_valve * 98066.5
    # P2_part2 = pressure_deaerator * 98066.5
    # v_part2 = steamPH(P1_part2, h_part2 * 4186.8, 4)
    # t_part2 = steamPH(P1_part2, h_part2 * 4186.8, 2)
    # din_vis_part2 = steamPH(P1_part2, h_part2 * 4186.8, 6)
    # steam_props_detection(P1_part2, P2_part2, v_part2, din_vis_part2, len_part2)
    pass
else:
    # air_props_detection()
    pass

# Определение параметров пара участка 3
if len_part3 is not None and len_part4 is not None:
    # steam_props_detection()
    pass
else:
    # air_props_detection()
    pass

# Определение параметров пара участка 4
if len_part4 is not None and len_part5 is not None:
    # steam_props_detection()
    pass
else:
    # air_props_detection()
    pass

# Определние параметров воздуха при 5 участках
if len_part5 is not None:
    # air_props_detection()
    pass

# Определение параметров пара последнего участка
# h_part3 = ClapanModel.h_vozd
# P1_part3 = ClapanModel.p_vozd * 98066.5
# P2_part3 = pressure_ejector * 98066.5
# v = air_calc(ClapanModel.t_vozd, 1)
# t_part3 = ClapanModel.t_vozd
# din_vis_part3 = lambda_calc(ClapanModel.t_vozd, 2)

''' Determination of parameters by suction PART '''

# # Определение параметров отсоса в деаэратор
# g_deaerator = (G_part1 - G_part2) * count_valves
# h_deaerator = h_part2
# t_deaerator = steamPH(pressure_deaerator * 98066.5, h_deaerator * 4186.8, 2)
# X1 = (h_deaerator * 4186.8 - WaterPS(pressure_deaerator * 98066.5, 3)) / (
#         SteamPS(pressure_deaerator * 98066.5, 3) - WaterPS(pressure_deaerator * 98066.5, 3))
# x_deaerator = 1 if X1 > 1 else X1
#
# # Определение параметров отсоса в эжектор уплотнений
# g_ejector = (G_part2 + G_part3) * count_valves
# if type_calc_SAM == 0:
#     t_part2 = steamPH(pressure_ejector * 98066.5, h_part2 * 4186.8, 2)
#     t_ejector = (ClapanModel.t_vozd * G_part3 + t_part2 * G_part2) / (G_part2 + G_part3)
#     h_ejector = steamPT(pressure_ejector * 98066.5, t_ejector, 3) / 4186.8
# else:
#     h_ejector = (h_part2 * G_part2 + h_part3 * G_part3) / (G_part2 + G_part3)
#     t_ejector = steamPH(pressure_ejector * 98066.5, h_ejector * 4186.8, 2)
#
# X2 = (h_ejector * 4186.8 - WaterPS(pressure_ejector * 98066.5, 3)) / (
#         SteamPS(pressure_ejector * 98066.5, 3) - WaterPS(pressure_ejector * 98066.5, 3))
# x_ejector = 1 if X2 > 1 else X2
#
# # Определение суммарного расхода пара на штока клапанов
# g_valve = G_part1 * count_valves
# # Определение суммарного расхода воздуха
# g_vozd = G_part3 * count_valves


''' Variables OUTPUT PART '''

# ClapanModel.g_d = g_deaerator
# ClapanModel.h_d = h_deaerator
# ClapanModel.p_d = p_deaerator
# ClapanModel.t_d = t_deaerator
# ClapanModel.x_d = x_deaerator
#
# ClapanModel.g_e = g_ejector
# ClapanModel.h_e = h_ejector
# ClapanModel.p_e = p_ejector
# ClapanModel.t_e = t_ejector
# ClapanModel.x_e = x_ejector
#
# ClapanModel.g_valve = g_valve
# ClapanModel.h_valve = h_valve
# ClapanModel.p_valve = p_valve
# ClapanModel.t_valve = t_valve
#
# ClapanModel.G_part1 = G_part1
# ClapanModel.H_part1 = H_part1
# ClapanModel.v_part1 = v_part1
# ClapanModel.P1_part1 = P1_part1
# ClapanModel.T1_part1 = T_part1
# ClapanModel.P2_part1 = P2_part1
# ClapanModel.Re_part1 = Re_part1
# ClapanModel.w_part1 = _w_part1
#
# ClapanModel.G_part2 = G_part2
# ClapanModel.H_part2 = H_part2
# ClapanModel.v_part2 = v_part2
# ClapanModel.P1_part2 = P1_part2
# ClapanModel.T1_part2 = t_part2_
# ClapanModel.P2_part2 = P2_part2
# ClapanModel.Re_part2 = Re_part2
# ClapanModel.w_part2 = _w_part2
#
# ClapanModel.G_part3 = G_part3
# ClapanModel.H_part3 = H_part3
# ClapanModel.v_part3 = v_part3
# ClapanModel.P1_part3 = P1_part3
# ClapanModel.T1_part3 = T_part3
# ClapanModel.P2_part3 = P2_part3
# ClapanModel.Re_part3 = Re_part3
# ClapanModel.w_part3 = _w_part3
#
# ClapanModel.L1_Print = L1 * 1000
# ClapanModel.L2_Print = L2 * 1000
# ClapanModel.L3_Print = L3 * 1000
# ClapanModel.D_Print = D * 1000
# ClapanModel.delt_Print = delt * 1000
# ClapanModel.f_zaz = f * 10 ** 6
