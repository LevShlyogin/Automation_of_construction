import numpy as np
from scipy.interpolate import interp1d
from math import pi
from seuif97 import *  # Correct need

from CalculationValveRods.InputFromUser import entry_to_DB
# from models import *

'''
Functions PART (additional + steam/air)
'''

steamPH = ph(1, 2, 3)
steamPT = pt(1, 2, 3)

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


# Вспомогательная функция для нахождения G пара, или же воздуха для последней части
def G_find(last_part, ALFA, P_first, P_second, v):
    if not last_part:
        # Определение параметров воздуха последнего участка
        G = max(0.001, ALFA * S * ((P_first ** 2 - P_second ** 2) / (P_first * v)) ** 0.5 * 3.6)
    else:
        # Определение параметров пара от первого до предпоследнего участка
        G = ALFA * S * ((P_first ** 2 - P_second ** 2) / (P_first * v)) ** 0.5 * 3.6
    return G


# Функция для определения параметров пара участка
def part_props_detection(P_first, P_second, v, din_vis, len_part, last_part=False, W=50):
    if P_first == P_second:
        P_first += 0.03
    kin_vis = v * din_vis
    delta_speed = 1
    while not (-0.001 < delta_speed < 0.001):
        Re = (W * 2 * delta_clearance) / kin_vis
        ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
        G = G_find(last_part, ALFA, P_first, P_second, v)
        delta_speed = W - v * G / (3.6 * S)
        if delta_speed <= 0.001:
            W += max(0.001, W)
        elif delta_speed >= 0.001:
            W -= max(0.001, W * 0.9)
    Re = (W * 2 * delta_clearance) / kin_vis
    ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
    G = G_find(last_part, ALFA, P_first, P_second, v)
    return G


'''
Variables & INPUTs PART

General geometric parameters
radius_rounding                                       - Radius of inlet rounding or chamfer size
delta_clearance                                       - Radial clearance
diameter_stock                                        - Stem diameter
len_part1, len_part2, len_part3, len_part4, len_part5 - Lengths of each section (to meters)
'''

count_finded, needed_BPs, BPs_info = entry_to_DB()
print(count_finded, needed_BPs, BPs_info)

# Этого нет в таблице, из которой импортится
temperature_start_DB = None
pressure_start_DB = None
pout1 = None
pout2 = None
h_air = None
t_air = None

pressure_deaerator = pout1
pressure_ejector = pout2
temperature_start_valve = temperature_start_DB
pressure_start_valve = pressure_start_DB
# enthalpy_steam = steamPT(pressure_start_valve * 98066.5, temperature_start_valve, 3) / 4186.8

radius_rounding_DB = BPs_info[11]        # Радиус скругления
delta_clearance_DB = BPs_info[5]         # Расчетный зазор либо Точность изготовления (хз)
diameter_stock_DB = BPs_info[2]          # Диаметр штока
len_part1_DB = BPs_info[6]               # Длина участка 1
len_part2_DB = BPs_info[7]               # Длина участка 2
len_part3_DB = BPs_info[8]               # Длина участка 3
len_part4_DB = BPs_info[9]               # Длина участка 4
len_part5_DB = BPs_info[10]              # Длина участка 5

# print(radius_rounding_DB, delta_clearance_DB, diameter_stock_DB, len_part1_DB, len_part2_DB, len_part3_DB, len_part4_DB, len_part5_DB)

radius_rounding = radius_rounding_DB / 1000 if radius_rounding_DB is not None else None
delta_clearance = delta_clearance_DB / 1000 if delta_clearance_DB is not None else None
diameter_stock = diameter_stock_DB / 1000 if diameter_stock_DB is not None else None
len_part1 = len_part1_DB / 1000 if len_part1_DB is not None else None
len_part2 = len_part2_DB / 1000 if len_part2_DB is not None else None
len_part3 = len_part3_DB / 1000 if len_part3_DB is not None else None
len_part4 = len_part4_DB / 1000 if len_part4_DB is not None else None
len_part5 = len_part5_DB / 1000 if len_part5_DB is not None else None

count_valves = count_finded # Number of valves
count_parts = sum([1 if i is not None else 0 for i in [len_part1, len_part2, len_part3, len_part4, len_part5]])
P1, P2, P3, P4, P5, P6 = [input() if i <= count_parts else None for i in range(6)]
proportional_coef = radius_rounding / (delta_clearance * 2)  # Proportionality coefficient
S = delta_clearance * pi * diameter_stock  # Clearance area

# Calculate inlet softening coefficient (same for all sections)
KSI = ksi_calc(proportional_coef)

''' 
Defining parameters by parts
'''

# Определение параметров Участка 1
if len_part1:
    if len_part2:
        h_part1 = enthalpy_steam
        v_part1 = steamPH(P1, h_part1 * 4186.8, 4)
        t_part1 = steamPH(P1, h_part1 * 4186.8, 2)
        din_vis_part1 = steamPH(P1, h_part1 * 4186.8, 6)
        part_props_detection(P1, P2, v_part1, din_vis_part1, len_part1)
    else:
        h_part1 = h_air
        # P1_part1 = ClapanModel.p_vozd * 98066.5
        # P2_part1 = pressure_ejector * 98066.5
        t_part1 = t_air
        v_part1 = air_calc(t_part1, 1)
        din_vis_part1 = lambda_calc(t_part1)
        part_props_detection(P1, P2, v_part1, din_vis_part1, len_part1, last_part=True)

# Определение параметров Участка 2
if len_part2:
    if len_part3:
        h_part2 = enthalpy_steam
        v_part2 = steamPH(P2, h_part2 * 4186.8, 4)
        t_part2 = steamPH(P2, h_part2 * 4186.8, 2)
        din_vis_part2 = steamPH(P2, h_part2 * 4186.8, 6)
        part_props_detection(P2, P3, v_part2, din_vis_part2, len_part2)
    else:
        h_part2 = h_air
        # P1_part2 = ClapanModel.p_vozd * 98066.5
        # P2_part2 = pressure_ejector * 98066.5
        t_part2 = t_air
        v_part2 = air_calc(t_part2, 1)
        din_vis_part2 = lambda_calc(t_part2)
        part_props_detection(P2, P3, v_part2, din_vis_part2, len_part2, last_part=True)

# Определение параметров Участка 3
if len_part3:
    if len_part4:
        h_part3 = enthalpy_steam
        v_part3 = steamPH(P3, h_part3 * 4186.8, 4)
        t_part3 = steamPH(P3, h_part3 * 4186.8, 2)
        din_vis_part3 = steamPH(P3, h_part3 * 4186.8, 6)
        part_props_detection(P3, P4, v_part3, din_vis_part3, len_part3)
    else:
        h_part3 = h_air
        # P1_part3 = ClapanModel.p_vozd * 98066.5
        # P2_part3 = pressure_ejector * 98066.5
        t_part3 = t_air
        v_part3 = air_calc(t_part3, 1)
        din_vis_part3 = lambda_calc(t_part3)
        part_props_detection(P3, P4, v_part3, din_vis_part3, len_part3, last_part=True)

# Определение параметров Участка 4
if len_part4:
    if len_part5:
        h_part4 = enthalpy_steam
        v_part4 = steamPH(P4, h_part4 * 4186.8, 4)
        t_part4 = steamPH(P4, h_part4 * 4186.8, 2)
        din_vis_part4 = steamPH(P4, h_part4 * 4186.8, 6)
        part_props_detection(P4, P5, v_part4, din_vis_part4, len_part4)
    else:
        h_part4 = h_air
        # P4_part4 = ClapanModel.p_vozd * 98066.5
        # P5_part4 = pressure_ejector * 98066.5
        t_part4 = t_air
        v_part4 = air_calc(t_part4, 1)
        din_vis_part4 = lambda_calc(t_part4)
        part_props_detection(P4, P5, v_part4, din_vis_part4, len_part4, last_part=True)

# Определние параметров Участка 5
if len_part5:
    h_part5 = h_air
    # P1_part5 = ClapanModel.p_vozd * 98066.5
    # P2_part5 = pressure_ejector * 98066.5
    t_part5 = t_air
    v_part5 = air_calc(t_part5, 1)
    din_vis_part5 = lambda_calc(t_part5)
    part_props_detection(P5, P6, v_part5, din_vis_part5, len_part5, last_part=True)

''' 
Determination of parameters by suction PART 
'''

# # Определение параметров отсоса в деаэратор
# g_deaerator = (G_part1 - G_part2) * count_valves
# h_deaerator = h_part2
# t_deaerator = steamPH(pressure_deaerator * 98066.5, h_deaerator * 4186.8, 2)
#
# # X1 = (h_deaerator * 4186.8 - WaterPS(pressure_deaerator * 98066.5, 3)) / (
# #         SteamPS(pressure_deaerator * 98066.5, 3) - WaterPS(pressure_deaerator * 98066.5, 3))
# # x_deaerator = 1 if X1 > 1 else X1
#
# # Определение параметров отсоса в эжектор уплотнений
# g_ejector = (G_part2 + G_part3) * count_valves

notChosen_typeCalc = False
while notChosen_typeCalc:
    type_calc_SAM = int(input("Выберите способ вычисления: введите число 1 либо 2"))
    if type_calc_SAM == 1:
        # t_part2 = steamPH(pressure_ejector * 98066.5, h_part2 * 4186.8, 2)
        # t_ejector = (ClapanModel.t_vozd * G_part3 + t_part2 * G_part2) / (G_part2 + G_part3)
        # h_ejector = steamPT(pressure_ejector * 98066.5, t_ejector, 3) / 4186.8
        notChosen_typeCalc = True
    elif type_calc_SAM == 2:
        # h_ejector = (h_part2 * G_part2 + h_part3 * G_part3) / (G_part2 + G_part3)
        # t_ejector = steamPH(pressure_ejector * 98066.5, h_ejector * 4186.8, 2)
        notChosen_typeCalc = True
    else:
        print("Ввод не распознан.")

# # X2 = (h_ejector * 4186.8 - WaterPS(pressure_ejector * 98066.5, 3)) / (
# #         SteamPS(pressure_ejector * 98066.5, 3) - WaterPS(pressure_ejector * 98066.5, 3))
# # x_ejector = 1 if X2 > 1 else X2
#
# # Определение суммарного расхода пара на штока клапанов
# g_valve = G_part1 * count_valves
# # Определение суммарного расхода воздуха
# g_vozd = G_part3 * count_valves

''' 
Variables OUTPUT PART 

G, h, t, p... bla bla bla
'''

print("FULL OUTPUT END")
