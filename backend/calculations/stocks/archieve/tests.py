from math import pi
from sys import exit
from time import sleep

from WSAProperties import air_calc, ksi_calc, lambda_calc  # Calculate fric resist, softening coef and air props
from seuif97 import *  # SteamPH and SteamPT (ph and pt)

<<<<<<<< HEAD:other_files/CalculationValveRods/Stocks/TestingCalcs.py
from other_files.CalculationValveRods.InputFromUser import entry_to_DB  # Func for import variables from DB
========
from calculations.database.userInput import entry_to_DB  # Func for import variables from DB
>>>>>>>> origin/backend-react-fastapi:backend/calculations/stocks/archieve/tests.py

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
def part_props_detection(P_first , P_second, v, din_vis, len_part, last_part=False, W=50):
    P_first *= 10.197162
    P_second *= 10.197162
    if P_first == P_second:
        P_first += 0.03
    kin_vis = v * din_vis
    delta_speed = 1
    iters = 0
    while not (-0.001 < delta_speed < 0.001):
        Re = (W * 2 * delta_clearance) / kin_vis
        ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
        G = G_find(last_part, ALFA, P_first, P_second, v)
        delta_speed = W - v * G / (3.6 * S)
        if delta_speed <= 0.001:
            W += max(0.001, W)
        elif delta_speed >= 0.001:
            W -= max(0.001, W * 0.9)
        iters += 1
    Re = (W * 2 * delta_clearance) / kin_vis
    ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5
    G = G_find(last_part, ALFA, P_first, P_second, v)
    print(iters)
    return G


def exit_err(error_text="Неизвестная ошибка"):
    """
    Функция для прекращения работы программы при некорректных данных
    """
    if "Нет данных" in error_text:
        print(error_text)
        inp = float(input("Введите данные: "))
        return inp
    print(error_text)
    sleep(3)
    exit()


def convert_pressure_to_mpa(pressure):
    """Преобразует давление в МПа из различных единиц измерения.

      Returns:
        Давление в МПа, или сообщение об ошибке при неверном выборе единиц.
      """
    # Словарь для хранения коэффициентов перевода в МПа
    conversion_factors = {
        1: 1e-6,# Паскаль в МПа
        2: 1e-3,# кПа в МПа
        3: 0.0980665,# кгс/см² в МПа
        4: 0.101325,# техническая атмосфера в МПа
        5: 0.1,# бар в МПа
        6: 0.101325# физическая атмосфера в МПа
    }
    # Выводим меню выбора единиц измерения
    print("Выберите единицы измерения:", "1 - Па", "2 - кПа", "3 - кгс/см²", "4 - атм (техническая атмосфера)",
          "5 - бар", "6 - атм (физическая атмосфера)", sep='\n')
    # Запрашиваем выбор единиц измерения
    unit = 3
    # unit = int(input("Введите номер единицы измерения: "))

    # Проверяем, что выбор пользователя валиден
    if unit not in conversion_factors:
        return exit_err("Неверный выбор единицы измерения.")
    # Выполняем конвертацию
    mpa_pressure = pressure * conversion_factors[unit]
    # Возвращаем результат
    return mpa_pressure


count_finded, needed_BPs, BPs_info = entry_to_DB()
print(count_finded, needed_BPs, BPs_info, sep=", ")

# Этого нет в таблице, из которой импортится
print("\nОбнаружены недостающие параметры для подсчетов!")
temperature_start_DB = float(input("Введите T0: "))
t_air = float(input("Введите t_air: "))
h_air = t_air * 1.006

radius_rounding_DB = BPs_info[11]   # Радиус скругления
delta_clearance_DB = BPs_info[5]    # Расчетный зазор либо Точность изготовления (хз)
diameter_stock_DB = BPs_info[2]     # Диаметр штока
len_part1_DB = BPs_info[6]          # Длина участка 1
len_part2_DB = BPs_info[7]          # Длина участка 2
len_part3_DB = BPs_info[8]          # Длина участка 3
len_part4_DB = BPs_info[9]          # Длина участка 4
len_part5_DB = BPs_info[10]         # Длина участка 5

# print(radius_rounding_DB, delta_clearance_DB, diameter_stock_DB,
#       len_part1_DB, len_part2_DB, len_part3_DB, len_part4_DB, len_part5_DB)

radius_rounding = radius_rounding_DB / 1000 if radius_rounding_DB is not None else exit_err(
    "Нет данных о радиусе скругления")
delta_clearance = float(delta_clearance_DB) / 1000 if delta_clearance_DB is not None else exit_err("Нет данных о зазоре")
diameter_stock = float(diameter_stock_DB) / 1000 if diameter_stock_DB is not None else exit_err("Нет данных о диаметре штока")
len_part1 = float(len_part1_DB) / 1000 if len_part1_DB is not None else exit_err("Нет данных об участке 1")
len_part2 = float(len_part2_DB) / 1000 if len_part2_DB is not None else exit_err("Нет данных об участке 2")
len_part3 = float(len_part3_DB) / 1000 if len_part3_DB is not None else None
len_part4 = float(len_part4_DB) / 1000 if len_part4_DB is not None else None
len_part5 = float(len_part5_DB) / 1000 if len_part5_DB is not None else None

count_valves = count_finded  # Number of valves
count_parts = sum([1 if i is not None else 0 for i in [len_part1, len_part2, len_part3, len_part4, len_part5]])
P1, P2, P3, P4, P5 = [convert_pressure_to_mpa(float(input(f"Введите параметр P{i}: "))) if i <= count_parts else 0.0 for i in range(1, 6)]
p_deaerator = P1
p_ejector = P2

proportional_coef = radius_rounding / (delta_clearance * 2)  # Proportionality coeff
S = delta_clearance * pi * diameter_stock  # Clearance area

enthalpy_steam = pt2h(P1, temperature_start_DB)

# Calculate inlet softening coefficient (same for all sections)
KSI = ksi_calc(proportional_coef)

''' 
Defining parameters by parts
'''

G_part1, G_part2, G_part3, G_part4, G_part5 = 0.0, 0.0, 0.0, 0.0, 0.0
t_part1, t_part2, t_part3, t_part4, t_part5 = 0.0, 0.0, 0.0, 0.0, 0.0
h_part1, h_part2, h_part3, h_part4, h_part5 = 0.0, 0.0, 0.0, 0.0, 0.0

# Props find for area 1
if len_part1:
    if len_part2:
        h_part1 = enthalpy_steam
        v_part1 = ph2v(P1, h_part1)
        t_part1 = ph2t(P1, h_part1)
        din_vis_part1 = ph(P1, h_part1, 24)
        G_part1 = part_props_detection(P1, P2, v_part1, din_vis_part1, len_part1)
        print(f"Динамическая вязкость: {din_vis_part1}")
        print(f"Удельный объём: {v_part1}")

# Props find for area 2
if len_part2:
    if len_part3:
        h_part2 = enthalpy_steam
        v_part2 = ph(P2, h_part2, 3)
        t_part2 = ph(P2, h_part2, 1)
        din_vis_part2 = ph(P2, h_part2, 24)
        G_part2 = part_props_detection(P2, P3, v_part2, din_vis_part2, len_part2)

# Props find for area 3
if len_part3:
    if len_part4:
        h_part3 = enthalpy_steam
        v_part3 = ph(P3, h_part3, 3)
        t_part3 = ph(P3, h_part3, 1)
        din_vis_part3 = ph(P3, h_part3, 24)
        G_part3 = part_props_detection(P3, P4, v_part3, din_vis_part3, len_part3)
    else:
        h_part3 = h_air
        t_part3 = t_air
        v_part3 = air_calc(t_part3, 1)
        din_vis_part3 = lambda_calc(t_part3)
        G_part3 = part_props_detection(P3, 0.1013, v_part3, din_vis_part3, len_part3, last_part=True)