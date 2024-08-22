import numpy as np
from scipy.interpolate import interp1d
from math import pi
from seuif97 import *  # SteamPH and SteamPT (ph and pt)
from WSAProperties import air_calc, ksi_calc, lambda_calc  # Calculate fric resist, softening coef and air props
from CalculationValveRods.InputFromUser import entry_to_DB  # Func for import variables from DB
from typing import Tuple  # CleanCoding
from sys import exit
from time import sleep

'''
Functions PART (additional + steam/air)
'''


# Вспомогательная функция для нахождения G пара, или же воздуха для последней части
def G_find(last_part, ALFA, P_first, P_second, v):
    if last_part:
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


def exit_err(error_text="Неизвестная ошибка"):
    """
    Функция для прекращения работы программы при некорректных данных
    """
    print(error_text)
    sleep(3)
    exit()

'''
Variables & INPUTs PART

General geometric parameters
radius_rounding                                       - Radius of inlet rounding or chamfer size
delta_clearance                                       - Radial clearance
diameter_stock                                        - Stem diameter
len_part1, len_part2, len_part3, len_part4, len_part5 - Lengths of each section (to meters)
'''

count_finded, needed_BPs, BPs_info = entry_to_DB()

# Этого нет в таблице, из которой импортится
print("\nОбнаружены недостающие параметры для подсчетов!")
temperature_start_DB = float(input("Введите T0: "))
pressure_start_DB = float(input("Введите P0: "))
pout1 = float(input("Введите Pout1: "))
pout2 = float(input("Введите Pout2: "))
h_air = float(input("Введите h_air: "))
t_air = float(input("Введите t_air: "))

pressure_deaerator = pout1
pressure_ejector = pout2
temperature_start_valve = temperature_start_DB
pressure_start_valve = pressure_start_DB
enthalpy_steam = pt(pressure_start_valve * 98066.5, temperature_start_valve, 4) / 4186.8

radius_rounding_DB = BPs_info[11]  # Радиус скругления
delta_clearance_DB = BPs_info[5]  # Расчетный зазор либо Точность изготовления (хз)
diameter_stock_DB = BPs_info[2]  # Диаметр штока
len_part1_DB = BPs_info[6]  # Длина участка 1
len_part2_DB = BPs_info[7]  # Длина участка 2
len_part3_DB = BPs_info[8]  # Длина участка 3
len_part4_DB = BPs_info[9]  # Длина участка 4
len_part5_DB = BPs_info[10]  # Длина участка 5

# print(radius_rounding_DB, delta_clearance_DB, diameter_stock_DB,
#       len_part1_DB, len_part2_DB, len_part3_DB, len_part4_DB, len_part5_DB)

radius_rounding = radius_rounding_DB / 1000 if radius_rounding_DB is not None else None
delta_clearance = delta_clearance_DB / 1000 if delta_clearance_DB is not None else None
diameter_stock = diameter_stock_DB / 1000 if diameter_stock_DB is not None else None
len_part1 = len_part1_DB / 1000 if len_part1_DB is not None else exit_err("Нет данных об участке 1")
len_part2 = len_part2_DB / 1000 if len_part2_DB is not None else exit_err("Нет данных об участке 2")
len_part3 = len_part3_DB / 1000 if len_part3_DB is not None else None
len_part4 = len_part4_DB / 1000 if len_part4_DB is not None else None
len_part5 = len_part5_DB / 1000 if len_part5_DB is not None else None

count_valves = count_finded  # Number of valves
count_parts = sum([1 if i is not None else 0 for i in [len_part1, len_part2, len_part3, len_part4, len_part5]])
P1, P2, P3, P4, P5, P6 = [float(input(f"Введите параметр P{i}: ")) if i <= count_parts else None for i in range(1, 7)]
# Maybe P will need to be converted, that is, multiplied by 98066.5
proportional_coef = radius_rounding / (delta_clearance * 2)  # Proportionality coeff
S = delta_clearance * pi * diameter_stock  # Clearance area

# Calculate inlet softening coefficient (same for all sections)
KSI = ksi_calc(proportional_coef)

''' 
Defining parameters by parts
'''

# Props find for area 1
if len_part1:
    if len_part2:
        h_part1 = enthalpy_steam
        v_part1 = ph(P1, h_part1 * 4186.8, 3)
        t_part1 = ph(P1, h_part1 * 4186.8, 1)
        din_vis_part1 = ph(P1, h_part1 * 4186.8, 24)
        part_props_detection(P1, P2, v_part1, din_vis_part1, len_part1)

# Props find for area 2
if len_part2:
    if len_part3:
        h_part2 = enthalpy_steam
        v_part2 = ph(P2, h_part2 * 4186.8, 3)
        t_part2 = ph(P2, h_part2 * 4186.8, 1)
        din_vis_part2 = ph(P2, h_part2 * 4186.8, 24)
        part_props_detection(P2, P3, v_part2, din_vis_part2, len_part2)

# Props find for area 3
if len_part3:
    if len_part4:
        h_part3 = enthalpy_steam
        v_part3 = ph(P3, h_part3 * 4186.8, 3)
        t_part3 = ph(P3, h_part3 * 4186.8, 1)
        din_vis_part3 = ph(P3, h_part3 * 4186.8, 24)
        part_props_detection(P3, P4, v_part3, din_vis_part3, len_part3)
    else:
        h_part3 = h_air
        t_part3 = t_air
        v_part3 = air_calc(t_part3, 1)
        din_vis_part3 = lambda_calc(t_part3)
        part_props_detection(P3, 1.03, v_part3, din_vis_part3, len_part3, last_part=True)

# Props find for area 4
if len_part4:
    if len_part5:
        h_part4 = enthalpy_steam
        v_part4 = ph(P4, h_part4 * 4186.8, 3)
        t_part4 = ph(P4, h_part4 * 4186.8, 1)
        din_vis_part4 = ph(P4, h_part4 * 4186.8, 24)
        part_props_detection(P4, P5, v_part4, din_vis_part4, len_part4)
    else:
        h_part4 = h_air
        t_part4 = t_air
        v_part4 = air_calc(t_part4, 1)
        din_vis_part4 = lambda_calc(t_part4)
        part_props_detection(P4, 1.03, v_part4, din_vis_part4, len_part4, last_part=True)

# Props find for area 5
if len_part5:
    h_part5 = h_air
    t_part5 = t_air
    v_part5 = air_calc(t_part5, 1)
    din_vis_part5 = lambda_calc(t_part5)
    part_props_detection(P5, 1.03, v_part5, din_vis_part5, len_part5, last_part=True)

''' 
Determination of parameters by suction PART 
'''


# Определение параметров отсоса в деаэратор
def deaerator_options(G1: float, G2: float, h_part2: float, pressure_deaerator: float, count_valves: int) \
        -> Tuple[float, float, float, float]:
    """
    Рассчитывает параметры отсоса в деаэратор.

    Args:
        G1: Расход пара на первой секции.
        G2: Расход пара на второй секции.
        h_part2: Энтальпия пара на второй секции.
        pressure_deaerator: Давление в деаэраторе.
        count_valves: Количество секций клапана.

    Returns:
        Кортеж из расхода, температуры, давления и энтальпии пара в деаэраторе.
    """
    g_deaerator = (G1 - G2) * count_valves
    h_deaerator = h_part2
    t_deaerator = ph(pressure_deaerator * 98066.5, h_deaerator * 4186.8, 1)
    return g_deaerator, t_deaerator, pressure_deaerator, h_deaerator


# Определение параметров отсоса в эжектор уплотнений
def ejector_options(G1: float, G2: float, h_part2: float, G_part3: float,
                    h_part3: float, G_part4: float, h_part4: float, pressure_ejector: float,
                    count_valves: int) -> Tuple[float, float, float, float]:
    """
    Рассчитывает параметры отсоса в эжектор уплотнений.

    Args:
        G1: Расход пара на первой секции.
        G2: Расход пара на второй секции.
        h_part2: Энтальпия пара на второй секции.
        G_part3: Расход пара на третьей секции.
        h_part3: Энтальпия пара на третьей секции.
        G_part4: Расход пара на четвертой секции (если есть).
        h_part4: Энтальпия пара на четвертой секции (если есть).
        pressure_ejector: Давление в эжекторе.
        count_valves: Количество секций клапана.

    Returns:
        Кортеж из расхода, температуры, давления и энтальпии пара в эжекторе.
    """
    if count_valves == 3:
        # Два отсоса в эжектор
        g_ejector = G2 + G_part3
        h_ejector = (h_part2 * G2 + h_part3 * G_part3) / (G2 + G_part3)
        t_ejector = ph(pressure_ejector * 98066.5, h_ejector * 4186.8, 1)
        return g_ejector, t_ejector, pressure_ejector, h_ejector
    elif count_valves == 4:
        # Три отсоса в эжектор
        g_ejector = G2 + G_part3 + G_part4
        h_ejector = (h_part2 * G2 + h_part3 * G_part3 + h_part4 * G_part4) / (G2 + G_part3 + G_part4)
        t_ejector = ph(pressure_ejector * 98066.5, h_ejector * 4186.8, 1)
        return g_ejector, t_ejector, pressure_ejector, h_ejector
    elif count_valves == 5:
        # Четыре отсоса в эжектор
        g_ejector = G2 + G_part3 + G_part4
        h_ejector = (h_part2 * G2 + h_part3 * G_part3 + h_part4 * G_part4) / (G2 + G_part3 + G_part4)
        t_ejector = ph(pressure_ejector * 98066.5, h_ejector * 4186.8, 1)
        return g_ejector, t_ejector, pressure_ejector, h_ejector
    else:
        raise ValueError("Неверное количество секций клапана.")


# Основная функция для расчета параметров отсоса
def calculate_steam_venting(G1: float, G2: float, h_part2: float, G_part3: float, h_part3: float, G_part4: float,
                            h_part4: float, pressure_deaerator: float, pressure_ejector: float, count_valves: int) \
        -> Tuple[Tuple[float, float, float, float], list[Tuple[float, float, float, float]]]:
    """
    Рассчитывает параметры отсоса пара для всех секций клапана.

    Args:
        G1: Расход пара на первой секции.
        G2: Расход пара на второй секции.
        h_part2: Энтальпия пара на второй секции.
        G_part3: Расход пара на третьей секции.
        h_part3: Энтальпия пара на третьей секции.
        G_part4: Расход пара на четвертой секции (если есть).
        h_part4: Энтальпия пара на четвертой секции (если есть).
        pressure_deaerator: Давление в деаэраторе.
        pressure_ejector: Давление в эжекторе.
        count_valves: Количество секций клапана.

    Returns:
        Кортеж, содержащий параметры отсоса в деаэратор и список параметров отсоса в эжектор для каждой секции.
    """
    deaerator_params = deaerator_options(G1, G2, h_part2, pressure_deaerator, count_valves)

    ejector_params = []
    if count_valves == 3:
        ejector_params.append(ejector_options(G1, G2, h_part2, G_part3, h_part3, G_part4,
                                              h_part4, pressure_ejector, count_valves))
    if count_valves > 4:
        ejector_params.append(ejector_options(G1, G2, h_part2, G_part3, h_part3, G_part4,
                                              h_part4, pressure_ejector, count_valves))

    return deaerator_params, ejector_params


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

# # Определение суммарного расхода пара на штока клапанов
# g_valve = G_part1 * count_valves
# # Определение суммарного расхода воздуха
# g_vozd = G_part3 * count_valves

''' 
Variables OUTPUT PART 

G, h, t, p... bla bla bla
'''

print("FULL OUTPUT END")
