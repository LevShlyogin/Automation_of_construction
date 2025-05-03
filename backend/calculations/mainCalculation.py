from math import pi
from seuif97 import *
from WSAProperties import air_calc, ksi_calc, lambda_calc
from calculations.userInput import entry_database
from typing import Tuple
from sys import exit
from time import sleep

'''
Functions PART (additional + steam/air)
'''


# Вспомогательная функция для нахождения G пара, или же воздуха для последней части
def G_find(last_part, ALFA, P_first, P_second, v):
    """
        Вычисляет значение G в зависимости от типа среды (пар или воздух)
        и входных параметров.

        Args:
            last_part (bool): Флаг, указывающий, является ли текущий участок последним.
            ALFA (float): Коэффициент, зависящий от числа Рейнольдса и геометрии.
            P_first (float): Давление в начале участка (в Паскалях).
            P_second (float): Давление в конце участка (в Паскалях).
            v (float): Скорость потока (в м/с).

        Returns:
            float: Значение G.
    """
    G = ALFA * S * ((P_first ** 2 - P_second ** 2) / (P_first * v)) ** 0.5 * 3.6
    if last_part:
        G = max(0.001, G)
    return G


def part_props_detection(P_first, P_second, v, din_vis, len_part, last_part=False, W_min=1, W_max=1000):
    """
        Определяет параметры пара/воздуха участка с использованием бинарного поиска.

        Args:
            P_first (float): Давление в начале участка (в бар).
            P_second (float): Давление в конце участка (в бар).
            v (float): Удельный объём (в м^3/кг).
            din_vis (float): Кинематическая вязкость (в м^2/с).
            len_part (float): Длина участка (в м).
            last_part (bool, optional): Флаг, указывающий, является ли текущий участок последним. Defaults to False.
            W_min (float, optional): Минимальное значение скорости потока (в м/с). Defaults to 1.
            W_max (float, optional): Максимальное значение скорости потока (в м/с). Defaults to 1000.

        Returns:
            float: Значение G.
    """
    if P_first == P_second:
        P_first += 0.003  # Корректировка давления, если оно одинаково
    P_first *= 10 ** 6  # Преобразование давления из бар в Паскали
    P_second *= 10 ** 6  # Преобразование давления из бар в Паскали
    kin_vis = v * din_vis  # Вычисление кинематической вязкости

    while W_max - W_min > 0.001:  # Цикл бинарного поиска
        W_mid = (W_min + W_max) / 2  # Вычисление середины диапазона
        Re = (W_mid * 2 * delta_clearance) / kin_vis  # Вычисление числа Рейнольдса
        ALFA = 1 / (1 + KSI + (
                0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5  # Вычисление коэффициента ALFA
        G = G_find(last_part, ALFA, P_first, P_second, v)  # Вычисление G
        delta_speed = W_mid - v * G / (3.6 * S)  # Вычисление разности скоростей

        if delta_speed > 0:
            W_max = W_mid  # Сужение диапазона поиска
        else:
            W_min = W_mid  # Сужение диапазона поиска

    W_result = (W_min + W_max) / 2  # Получение приближенного значения W
    Re = (W_result * 2 * delta_clearance) / kin_vis  # Вычисление числа Рейнольдса
    ALFA = 1 / (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance) ** 0.5  # Вычисление коэффициента ALFA
    G = G_find(last_part, ALFA, P_first, P_second, v)  # Вычисление G
    return G


def exit_err(error_text="Неизвестная ошибка"):
    """
        Функция для прекращения работы программы при некорректных данных
    """
    if "Нет данных о" in error_text:
        print(error_text)
        inp = float(input("Введите данные: "))
        return inp
    print(error_text)
    sleep(3)
    exit()
    return None


def convert_pressure_to_mpa(pressure):
    """
        Преобразует давление в МПа из различных единиц измерения.

        Returns:
            Давление в МПа, или сообщение об ошибке при неверном выборе единиц.
    """
    # Словарь для хранения коэффициентов перевода в МПа
    conversion_factors = {
        1: 1e-6,  # Паскаль в МПа
        2: 1e-3,  # кПа в МПа
        3: 0.0980665,  # кгс/см² в МПа
        4: 0.101325,  # техническая атмосфера в МПа
        5: 0.1,  # бар в МПа
        6: 0.101325  # физическая атмосфера в МПа
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
    return mpa_pressure


def kKal_to_kJ_kg(kKal):
    """
        Перевод килокалорий (kKal) в килоджоули на килограмм (kJ/kg).

        Args:
            kKal: Количество килокалорий в веществе.

        Returns:
            Количество килоджоулей на килограмм (kJ/kg).
    """
    return kKal * 4.184 / 1000  # 1 ккал = 4.184 kJ, делим на 1000 для kJ/kg


# Определение параметров отсоса в деаэратор
def deaerator_options(p_deaerator: float, count_parts: int, count_valves: int, h_part2: float, G_part1: float,
                      G_part2: float, G_part3: float, G_part4: float) -> Tuple[float, float, float, float]:
    """
        Рассчитывает параметры отсоса в деаэратор.

        Args:
            G_part1: Расход пара на первой секции.
            G_part2: Расход пара на второй секции.
            G_part3: Расход пара на третьей секции.
            G_part4: Расход пара на четвёртой секции.
            h_part2: Энтальпия пара на второй секции.
            p_deaerator: Давление в деаэраторе.
            count_valves: Количество клапанов.
            count_parts: Количество секций клапана.

        Returns:
            Кортеж из расхода, температуры, давления и энтальпии пара в деаэраторе.
    """
    g_deaerator, t_deaerator, h_deaerator = 0.0, 0.0, h_part2
    if count_parts == 3:
        g_deaerator = (G_part1 - G_part2) * count_valves
        t_deaerator = ph(p_deaerator, h_deaerator, 1)
    elif count_parts == 4:
        g_deaerator = (G_part1 - G_part2 - G_part3) * count_valves
        t_deaerator = ph(p_deaerator, h_deaerator, 1)
    elif count_parts == 5:
        g_deaerator = (G_part1 - G_part2 - G_part3 - G_part4) * count_valves
        t_deaerator = ph(p_deaerator, h_deaerator, 1)
    else:
        exit_err("Неверное количество секций клапана.")
    return g_deaerator, t_deaerator, p_deaerator, h_deaerator


# Определение параметров отсоса в эжектор уплотнений
def ejector_options(p_ejector: float, count_parts: int, count_valves: int, G_part2: float, h_part2: float,
                    G_part3: float, h_part3: float, G_part4=0.0, h_part4=0.0, G_part5=0.0, h_part5=0.0) -> Tuple[
    float, float, float, float]:
    """
        Рассчитывает параметры отсоса в эжектор уплотнений.

        Args:
            G_part2: Расход пара на второй секции.
            h_part2: Энтальпия пара на второй секции.
            G_part3: Расход пара на третьей секции.
            h_part3: Энтальпия пара на третьей секции.
            G_part4: Расход пара на четвертой секции (если есть).
            G_part5: Расход пара на пятой секции (если есть).
            h_part4: Энтальпия пара на четвертой секции (если есть).
            p_ejector: Давление в эжекторе.
            count_parts: Количество секций клапана.
            count_valves: Количество клапанов.

        Returns:
            Кортеж из расхода, температуры, давления и энтальпии пара в эжекторе.
    """
    g_ejector, t_ejector, h_ejector = 0.0, 0.0, 0.0
    if count_parts == 2:
        g_ejector = (G_part2 + G_part1) * count_valves
        h_ejector = (h_part2 * G_part2 + h_part1 * G_part1) / (G_part2 + G_part1)
        t_ejector = ph(p_ejector, h_ejector, 1)
    elif count_parts == 3:
        # Один отсос в эжектор
        g_ejector = (G_part2 + G_part3) * count_valves
        h_ejector = (h_part2 * G_part2 + h_part3 * G_part3) / (G_part2 + G_part3)
        t_ejector = ph(p_ejector, h_ejector, 1)
    elif count_parts == 4:
        # Два отсоса в эжектор
        g_first_suction = (G_part2 - G_part3 - G_part4) * count_valves  # Расход пара в первый отсос в деаэратор.
        g_second_suction = abs(G_part3 - G_part4) * count_valves  # Расход смеси во второй отсос в деаэратор.
        # Энтальпия смеси во втором отсосе в деаэратор.
        h_second_suction = (h_part4 * G_part4 + h_part3 * G_part3) / (G_part4 + G_part3)
        g_ejector = g_first_suction + g_second_suction
        # Энтальпия в первом отсосе в деаэратор равна энтальпии на втором участке
        h_ejector = (g_second_suction * h_second_suction + g_first_suction * h_part2) / (
                g_second_suction + g_first_suction)
        t_ejector = ph(p_ejector, h_ejector, 1)
    elif count_parts == 5:
        # Три отсоса в эжектор
        g_first_suction = G_part2 - G_part3 - G_part4  # Расход пара в первый отсос в деаэратор.
        g_second_suction = abs(G_part3 - G_part4)  # Расход пара во второй отсос в деаэратор.
        g_third_suction = G_part4 + G_part5  # Расход смеси в третий отсос в деаэратор.
        # Энтальпия смеси в третьем отсосе в деаэратор.
        h_third_suction = (h_part5 * G_part5 + h_part4 * G_part4) / (G_part5 + G_part4)
        g_ejector = (g_first_suction + g_second_suction + g_third_suction) * count_valves
        # Энтальпия в первом и втором отсосах в деаэратор равна энтальпии на втором участке
        h_ejector = ((g_third_suction * h_third_suction + g_second_suction * h_part2 + g_first_suction * h_part2)
                     / (g_third_suction + g_second_suction + g_first_suction))
        t_ejector = ph(p_ejector, h_ejector, 1)
    else:
        exit_err("Неверное количество секций клапана.")
    return g_ejector, t_ejector, p_ejector, h_ejector


def get_float_input(prompt):
    """
        Получает вещественное число от пользователя с обработкой ошибок.
    """
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Пожалуйста, введите корректное число.")


def get_int_input(prompt):
    """
        Получает целое число от пользователя с обработкой ошибок.
    """
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Пожалуйста, введите корректное целое число.")


def convert_to_meters(value, description):
    """
        Конвертирует значение в метры, с обработкой отсутствующих данных.
    """
    if value is not None:
        return float(value) / 1000
    else:
        exit_err(f"Нет данных о {description}")
        return None


def get_pressure_input(index, count_parts):
    """
        Получает давление от пользователя и преобразует его в МПа.
    """
    if index <= count_parts:
        return convert_pressure_to_mpa(get_float_input(f"Введите параметр P{index}: "))
    return 0.0


'''
Variables & inputs PART
General geometric parameters
radius_rounding                                       - Radius of inlet rounding or chamfer size
delta_clearance                                       - Radial clearance
diameter_stock                                        - Stem diameter
len_part1, len_part2, len_part3, len_part4, len_part5 - Lengths of each section (to meters)
'''

count_finded, needed_BPs, BPs_info = entry_database()

# Этого нет в таблице, из которой импортируется
print("\nОбнаружены недостающие параметры для подсчетов!")
temperature_start_DB = get_float_input("Введите T0: ")
t_air = get_float_input("Введите t_air: ")
h_air = t_air * 1.006  # Для расчёта энтальпии воздуха
count_valves = get_int_input("Введите количество клапанов: ")  # Number of valves

# Извлечение данных из BPs_info с проверкой
radius_rounding_DB = BPs_info[11]  # Радиус скругления
delta_clearance_DB = BPs_info[5]  # Расчетный зазор
diameter_stock_DB = BPs_info[2]  # Диаметр штока
len_parts_DB = BPs_info[6:11]  # Длины участков

# Конвертация данных
radius_rounding = convert_to_meters(radius_rounding_DB, "радиусе скругления")
delta_clearance = convert_to_meters(delta_clearance_DB, "зазоре")
diameter_stock = convert_to_meters(diameter_stock_DB, "диаметре штока")
len_parts = [convert_to_meters(length, f"участке {i + 1}") for i, length in enumerate(len_parts_DB)]

# Подсчет количества непустых участков
count_parts = sum(1 for length in len_parts if length is not None)

# Получение параметров давления
P_values = [get_pressure_input(i, count_parts) for i in range(1, 6)]
P1, P2, P3, P4, P5 = P_values
p_deaerator = P2

# Получение параметров длин участков
len_part1, len_part2, len_part3, len_part4, len_part5 = len_parts

# Расчёты
proportional_coef = radius_rounding / (delta_clearance * 2)  # Коэффициент пропорциональности
S = delta_clearance * pi * diameter_stock  # Площадь зазора
enthalpy_steam = pt2h(P1, temperature_start_DB)
KSI = ksi_calc(proportional_coef)  # Расчет коэффициента

''' 
Defining parameters by parts
'''

p_ejector = 0.0
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

# Props find for area 2
if len_part2:
    # If parts of valve more than 2
    if len_part3:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        h_part2 = enthalpy_steam
        v_part2 = ph(P2, h_part2, 3)
        t_part2 = ph(P2, h_part2, 1)
        din_vis_part2 = ph(P2, h_part2, 24)
        G_part2 = part_props_detection(P2, p_ejector, v_part2, din_vis_part2, len_part2)
    # If parts of valve is 2
    else:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        # Recalculate properties for part 1
        h_part1 = enthalpy_steam
        v_part1 = ph2v(P1, h_part1)
        t_part1 = ph2t(P1, h_part1)
        din_vis_part1 = ph(P1, h_part1, 24)
        G_part1 = part_props_detection(P1, p_ejector, v_part1, din_vis_part1, len_part1)
        # Calculate properties for part 2
        h_part2 = h_air
        t_part2 = t_air
        v_part2 = air_calc(t_part2, 1)
        din_vis_part2 = air_calc(t_part2, 2)
        G_part2 = part_props_detection(0.1013, p_ejector, v_part2, din_vis_part2, len_part2, last_part=True)

# Props find for area 3
if len_part3:
    if len_part4:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        h_part3 = enthalpy_steam
        v_part3 = ph(P3, h_part3, 3)
        t_part3 = ph(P3, h_part3, 1)
        din_vis_part3 = ph(P3, h_part3, 24)
        G_part3 = part_props_detection(P3, p_ejector, v_part3, din_vis_part3, len_part3)
    else:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        h_part3 = h_air
        t_part3 = t_air
        v_part3 = air_calc(t_part3, 1)
        din_vis_part3 = air_calc(t_part3, 2)
        G_part3 = part_props_detection(0.1013, p_ejector, v_part3, din_vis_part3, len_part3, last_part=True)

# Props find for area 4
if len_part4:
    if len_part5:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        h_part4 = enthalpy_steam
        v_part4 = ph(P4, h_part4, 3)
        t_part4 = ph(P4, h_part4, 1)
        din_vis_part4 = ph(P4, h_part4, 24)
        G_part4 = part_props_detection(P4, p_ejector, v_part4, din_vis_part4, len_part4)
    else:
        p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
        h_part4 = h_air
        t_part4 = t_air
        v_part4 = air_calc(t_part4, 1)
        din_vis_part4 = air_calc(t_part4, 2)
        G_part4 = part_props_detection(0.1013, p_ejector, v_part4, din_vis_part4, len_part4, last_part=True)

# Props find for area 5
if len_part5:
    p_ejector = convert_pressure_to_mpa(float(input("Введите P_ejector: ")))
    h_part5 = h_air
    t_part5 = t_air
    v_part5 = air_calc(t_part5, 1)
    din_vis_part5 = air_calc(t_part5, 2)
    G_part5 = part_props_detection(0.1013, p_ejector, v_part5, din_vis_part5, len_part5, last_part=True)

''' 
Determination of parameters by suction PART 
'''

g_deaerator, t_deaerator, p_deaerator, h_deaerator = deaerator_options(p_deaerator, count_parts, count_valves,
                                                                       h_part2, G_part1, G_part2, G_part3, G_part4)
g_ejector, t_ejector, p_ejector, h_ejector = ejector_options(p_ejector, count_parts, count_valves, G_part2, h_part2,
                                                             G_part3, h_part3, G_part4, h_part4, G_part5, h_part5)

# Определение суммарного расхода пара на штоки клапанов
g_valve = G_part1 * count_valves
# Определение суммарного расхода воздуха
g_vozd = G_part3 * count_valves

''' 
Variables OUTPUT PART 
G, h, t, p... bla bla bla
'''

print(f"Gi: {G_part1, G_part2, G_part3, G_part4, G_part5}")
print(f"Pi_in: {P1, P2, P3, P4, P5}")
print(f"Ti: {t_part1, t_part2, t_part3, t_part4, t_part5}")
print(f"Hi: {h_part1, h_part2, h_part3, h_part4, h_part5}")
print(f"deaerator props: {g_deaerator, t_deaerator, p_deaerator, h_deaerator}")
print(f"ejector props: {g_ejector, t_ejector, p_ejector, h_ejector}")
