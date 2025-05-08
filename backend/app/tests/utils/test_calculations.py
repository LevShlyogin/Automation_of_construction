from typing import Optional, List
import logging

# Импорт необходимых функций из внешних библиотек
from seuif97 import pt2h, ph, ph2v, ph2t
from WSAProperties import air_calc, ksi_calc, lambda_calc

import unittest


class CalculationError(Exception):
    """Кастомное исключение для ошибок расчетов."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def handle_error(error_text: str):
    """Обрабатывает ошибки, выбрасывая исключение."""
    raise CalculationError(error_text)


def convert_to_meters(value: float, description: str) -> float:
    """Конвертирует значение в метры."""
    if value is not None:
        return float(value) / 1000
    else:
        raise ValueError(f"Нет данных о {description}")


def calculate_enthalpy_for_air(t_air: float) -> float:
    """Рассчитывает энтальпию для воздуха на основе температуры."""
    return t_air * 1.006  # Энтальпия воздуха (кДж/кг)


def convert_pressure_to_mpa(pressure: float, unit: int = 5) -> float:
    """Преобразует давление в МПа из различных единиц измерения."""
    conversion_factors = {
        1: 1e-6,  # Паскаль в МПа
        2: 1e-3,  # кПа в МПа
        3: 0.0980665,  # кгс/см² в МПа
        4: 0.101325,  # техническая атмосфера в МПа
        5: 0.1,  # бар в МПа
        6: 0.101325  # физическая атмосфера в МПа
    }

    if unit not in conversion_factors:
        raise ValueError("Неверный выбор единицы измерения.")

    return pressure * conversion_factors[unit]


def G_find(last_part: bool, ALFA: float, P_first: float, P_second: float, v: float, S: float) -> float:
    """Вычисляет значение G в зависимости от типа среды и входных параметров."""
    G = ALFA * S * sqrt((P_first ** 2 - P_second ** 2) / (P_first * v)) * 3.6
    if last_part:
        G = max(0.001, G)  # Для последнего участка G не может быть меньше 0.001
    return G


def part_props_detection(P_first: float, P_second: float, v: float, din_vis: float, len_part: float,
                         delta_clearance: float, S: float, KSI: float, last_part: bool = False,
                         W_min: float = 1, W_max: float = 1000) -> float:
    """Определяет параметры пара/воздуха участка с использованием бинарного поиска."""
    if P_first == P_second:
        P_first += 0.003  # Корректировка давления, если оно одинаково
    P_first *= 10 ** 6  # Преобразование давления из бар в Паскали
    P_second *= 10 ** 6  # Преобразование давления из бар в Паскали
    kin_vis = v * din_vis  # Кинематическая вязкость

    while W_max - W_min > 0.001:  # Цикл бинарного поиска
        W_mid = (W_min + W_max) / 2
        Re = (W_mid * 2 * delta_clearance) / kin_vis
        ALFA = 1 / sqrt(1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance)
        G = G_find(last_part, ALFA, P_first, P_second, v, S)
        delta_speed = W_mid - v * G / (3.6 * S)

        if delta_speed > 0:
            W_max = W_mid
        else:
            W_min = W_mid

    W_result = (W_min + W_max) / 2
    Re = (W_result * 2 * delta_clearance) / kin_vis
    ALFA = 1 / sqrt(1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance)
    G = G_find(last_part, ALFA, P_first, P_second, v, S)
    return G


import unittest
from math import sqrt, pi


# Определение минимальных классов для теста


class CalculationParams:
    def __init__(self, temperature_start, t_air, count_valves, p_ejector, p_values):
        self.temperature_start = temperature_start
        self.t_air = t_air
        self.count_valves = count_valves
        self.p_ejector = p_ejector
        self.p_values = p_values


class ValveInfo:
    def __init__(self, rounding_radius, calculated_gap, rod_diameter, section_lengths):
        self.rounding_radius = rounding_radius
        self.calculated_gap = calculated_gap
        self.rod_diameter = rod_diameter
        self.section_lengths = section_lengths


# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValveCalculator:
    """Класс для выполнения всех расчетов, связанных с клапаном и турбиной."""

    def __init__(self, params: CalculationParams, valve_info: ValveInfo):
        self.params = params
        self.valve_info = valve_info

        # Инициализация всех необходимых полей
        self.temperature_start_DB = params.temperature_start
        self.t_air = params.t_air
        self.h_air = calculate_enthalpy_for_air(self.t_air)
        self.count_valves = params.count_valves

        self.radius_rounding_DB = valve_info.rounding_radius
        self.delta_clearance_DB = valve_info.calculated_gap
        self.diameter_stock_DB = valve_info.rod_diameter
        self.len_parts_DB = valve_info.section_lengths

        # Конвертация измерений в метры
        self.radius_rounding = convert_to_meters(self.radius_rounding_DB, "радиус скругления")
        self.delta_clearance = convert_to_meters(self.delta_clearance_DB, "зазор")
        self.diameter_stock = convert_to_meters(self.diameter_stock_DB, "диаметр штока")
        self.len_parts = [convert_to_meters(length, f"участок {i + 1}") for i, length in enumerate(self.len_parts_DB) if
                          length is not None]

        # Подсчет количества непустых участков
        self.count_parts = len(self.len_parts)

        # Конвертация давлений на участках из бар в МПа
        self.P_values = [
            convert_pressure_to_mpa(p, unit=5) if p > 0 else ValueError(
                f"Давление участка не может быть нулевым или отрицательным")
            for p in self.params.p_values[:self.count_parts]
        ]
        if len(self.P_values) != self.count_parts:
            raise ValueError(
                f"Количество значений давления ({len(self.P_values)}) не соответствует количеству участков ({self.count_parts})."
            )

        # Давление в деаэратор всегда по дефолту равно
        self.p_deaerator = self.P_values[1]

        # Конвертация давлений отсоса из бар в МПа
        self.p_suctions = [
            convert_pressure_to_mpa(p, unit=5)
            for p in self.params.p_ejector
        ] if self.params.p_ejector else []

        # Расчет коэффициента пропорциональности и других параметров
        self.proportional_coef = self.radius_rounding / (self.delta_clearance * 2)
        self.S = self.delta_clearance * pi * self.diameter_stock
        self.enthalpy_steam = pt2h(self.P_values[0], self.temperature_start_DB)
        self.KSI = ksi_calc(self.proportional_coef)

        # Инициализация всех G, T и H параметров
        self.g_parts = [0.0] * self.count_parts
        self.t_parts = [0.0] * self.count_parts
        self.h_parts = [0.0] * self.count_parts
        self.v_parts = [0.0] * self.count_parts
        self.din_vis_parts = [0.0] * self.count_parts
        self.p_ejector: Optional[float] = None

    def perform_calculations(self) -> dict:
        """Выполняет все расчеты и возвращает результаты."""
        try:
            # Динамически вызываем методы расчёта участков
            for i in range(self.count_parts):
                getattr(self, f'calculate_area{i + 1}')()

            # Вычисление параметров отсоса в деаэратор и эжектор
            g_deaerator, t_deaerator, h_deaerator, p_deaerator = self.deaerator_options()
            g_ejectors, t_ejectors, h_ejectors, p_ejectors = self.ejector_options()

            # Подготовка результатов
            result = {
                "Gi": self.g_parts[:self.count_parts],
                "Pi_in": self.P_values[:self.count_parts],
                "Ti": self.t_parts[:self.count_parts],
                "Hi": self.h_parts[:self.count_parts],
                "deaerator_props": [g_deaerator, t_deaerator, h_deaerator, p_deaerator],
                "ejector_props": [
                    {"g": g, "t": t, "h": h, "p": p} for g, t, h, p in
                    zip(g_ejectors, t_ejectors, h_ejectors, p_ejectors)
                ]
            }
            return result  # <-- Возврат результата после цикла
        except CalculationError as ce:
            logger.error(f"Calculation error: {ce.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during calculations: {str(e)}")
            raise CalculationError(f"Ошибка в расчётах: {str(e)}")

    def calculate_area1(self):
        """Выполняет расчеты для участка 1."""
        if self.count_parts >= 2:
            if self.len_parts[0] and self.len_parts[1]:
                self.h_parts[0] = self.enthalpy_steam
                self.v_parts[0] = ph2v(self.P_values[0], self.h_parts[0])
                self.t_parts[0] = ph2t(self.P_values[0], self.h_parts[0])
                self.din_vis_parts[0] = ph(self.P_values[0], self.h_parts[0], 24)
                self.g_parts[0] = part_props_detection(
                    self.P_values[0], self.P_values[1], self.v_parts[0], self.din_vis_parts[0],
                    self.len_parts[0], self.delta_clearance, self.S, self.KSI
                )
                logger.info(
                    f"Calculated values for area 1: G={self.g_parts[0]}, T={self.t_parts[0]}, H={self.h_parts[0]}")
            else:
                logger.error("Длины первого и второго участков должны быть ненулевыми.")
                raise CalculationError("Длины первого и второго участков должны быть ненулевыми.")
        else:
            logger.error("Клапан должен иметь как минимум два участка.")
            raise CalculationError("Клапан должен иметь как минимум два участка.")

    def calculate_area2(self):
        """Выполняет расчеты для участка 2."""
        if self.count_parts >= 2:
            if self.count_parts > 2:  # Исправлено с len_part3 на len_parts[2]
                self.p_ejector = self.p_suctions[0]
                self.h_parts[1] = self.enthalpy_steam
                self.v_parts[1] = ph(self.P_values[1], self.h_parts[1], 3)
                self.t_parts[1] = ph(self.P_values[1], self.h_parts[1], 1)
                self.din_vis_parts[1] = ph(self.P_values[1], self.h_parts[1], 24)
                self.g_parts[1] = part_props_detection(
                    self.P_values[1], self.p_ejector, self.v_parts[1], self.din_vis_parts[1],
                    self.len_parts[1], self.delta_clearance, self.S, self.KSI
                )
                logger.info(
                    f"Calculated values for area 2: G={self.g_parts[1]}, T={self.t_parts[1]}, H={self.h_parts[1]}")
            else:
                # Если len_parts[2] == 0 (len_part3 было исправлено на len_parts[2])
                self.p_ejector = self.p_suctions[0]
                # Recalculate properties for part 1
                self.h_parts[0] = self.enthalpy_steam
                self.v_parts[0] = ph2v(self.P_values[0], self.h_parts[0])
                self.t_parts[0] = ph2t(self.P_values[0], self.h_parts[0])
                self.din_vis_parts[0] = ph(self.P_values[0], self.h_parts[0], 24)
                self.g_parts[0] = part_props_detection(
                    self.P_values[0], self.p_ejector, self.v_parts[0], self.din_vis_parts[0],
                    self.len_parts[0], self.delta_clearance, self.S, self.KSI
                )
                logger.info(
                    f"Calculated values for area 1: G={self.g_parts[0]}, T={self.t_parts[0]}, H={self.h_parts[0]}")

                # Calculate properties for part 2
                self.h_parts[1] = self.h_air
                self.t_parts[1] = self.t_air
                self.v_parts[1] = air_calc(self.t_parts[1], 1)
                self.din_vis_parts[1] = air_calc(self.t_parts[1], 2)
                self.g_parts[1] = part_props_detection(
                    0.1013, self.p_ejector, self.v_parts[1], self.din_vis_parts[1],
                    self.len_parts[1], self.delta_clearance, self.S, self.KSI, last_part=True
                )
                logger.info(
                    f"Calculated values for area 2: G={self.g_parts[1]}, T={self.t_parts[1]}, H={self.h_parts[1]}")

    def calculate_area3(self):
        """Выполняет расчеты для участка 3."""
        if self.count_parts >= 3:
            if self.count_parts > 3:  # Исправлено с len_part4 на len_parts[3]
                self.p_ejector = self.p_suctions[1]
                self.h_parts[2] = self.enthalpy_steam
                self.v_parts[2] = ph(self.P_values[2], self.h_parts[2], 3)
                self.t_parts[2] = ph(self.P_values[2], self.h_parts[2], 1)
                self.din_vis_parts[2] = ph(self.P_values[2], self.h_parts[2], 24)
                self.g_parts[2] = part_props_detection(
                    self.P_values[2], self.p_ejector, self.v_parts[2], self.din_vis_parts[2],
                    self.len_parts[2], self.delta_clearance, self.S, self.KSI
                )
                logger.info(
                    f"Calculated values for area 3: G={self.g_parts[2]}, T={self.t_parts[2]}, H={self.h_parts[2]}")
            else:
                # Если len_parts[3] == 0
                self.p_ejector = self.p_suctions[1]
                self.h_parts[2] = self.h_air
                self.t_parts[2] = self.t_air
                self.v_parts[2] = air_calc(self.t_parts[2], 1)
                self.din_vis_parts[2] = air_calc(self.t_parts[2], 2)
                self.g_parts[2] = part_props_detection(
                    0.1013, self.p_ejector, self.v_parts[2], self.din_vis_parts[2],
                    self.len_parts[2], self.delta_clearance, self.S, self.KSI, last_part=True
                )
                logger.info(
                    f"Calculated values for area 3: G={self.g_parts[2]}, T={self.t_parts[2]}, H={self.h_parts[2]}")

    def calculate_area4(self):
        """Выполняет расчеты для участка 4."""
        if self.count_parts >= 4:
            if self.count_parts > 4:  # Исправлено с len_part5 на len_parts[4]
                self.p_ejector = self.p_suctions[2]
                self.h_parts[3] = self.enthalpy_steam
                self.v_parts[3] = ph(self.P_values[3], self.h_parts[3], 3)
                self.t_parts[3] = ph(self.P_values[3], self.h_parts[3], 1)
                self.din_vis_parts[3] = ph(self.P_values[3], self.h_parts[3], 24)
                self.g_parts[3] = part_props_detection(
                    self.P_values[3], self.p_ejector, self.v_parts[3], self.din_vis_parts[3],
                    self.len_parts[3], self.delta_clearance, self.S, self.KSI
                )
                logger.info(
                    f"Calculated values for area 4: G={self.g_parts[3]}, T={self.t_parts[3]}, H={self.h_parts[3]}")
            else:
                # Если len_parts[4] == 0 (len_part5 было исправлено на len_parts[4])
                self.p_ejector = self.p_suctions[2]
                self.h_parts[3] = self.h_air
                self.t_parts[3] = self.t_air
                self.v_parts[3] = air_calc(self.t_parts[3], 1)
                self.din_vis_parts[3] = air_calc(self.t_parts[3], 2)
                self.g_parts[3] = part_props_detection(
                    0.1013, self.p_ejector, self.v_parts[3], self.din_vis_parts[3],
                    self.len_parts[3], self.delta_clearance, self.S, self.KSI, last_part=True
                )
                logger.info(
                    f"Calculated values for area 4: G={self.g_parts[3]}, T={self.t_parts[3]}, H={self.h_parts[3]}")

    def calculate_area5(self):
        """Выполняет расчеты для участка 5."""
        if self.count_parts >= 5:  # Исправлено с len_part5 на len_parts[4]
            self.p_ejector = self.p_suctions[3]
            self.h_parts[4] = self.h_air
            self.t_parts[4] = self.t_air
            self.v_parts[4] = air_calc(self.t_parts[4], 1)
            self.din_vis_parts[4] = air_calc(self.t_parts[4], 2)
            self.g_parts[4] = part_props_detection(
                0.1013, self.p_ejector, self.v_parts[4], self.din_vis_parts[4],
                self.len_parts[4], self.delta_clearance, self.S, self.KSI, last_part=True
            )
            logger.info(
                f"Calculated values for area 5: G={self.g_parts[4]}, T={self.t_parts[4]}, H={self.h_parts[4]}")

    def deaerator_options(self):
        """Рассчитывает параметры отсоса в деаэратор."""
        g_deaerator: float = 0.0
        t_deaerator: float = 0.0
        h_deaerator: float = self.h_parts[1]

        # Расчёт массового расхода и температуры в зависимости от количества участков
        if self.count_parts == 2:
            return self.ejector_options()
        if self.count_parts == 3:
            g_deaerator = (self.g_parts[0] - self.g_parts[1]) * self.count_valves
            t_deaerator = ph(self.p_deaerator, h_deaerator, 1)
        elif self.count_parts == 4:
            g_deaerator = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2]) * self.count_valves
            t_deaerator = ph(self.p_deaerator, h_deaerator, 1)
        elif self.count_parts == 5:
            g_deaerator = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * self.count_valves
            t_deaerator = ph(self.p_deaerator, h_deaerator, 1)
        else:
            handle_error("Неверное количество секций клапана.")
        logger.info(
            f"Calculated values for deaerator: G={g_deaerator}, T={t_deaerator}, H={h_deaerator}, P={self.p_deaerator}")

        return g_deaerator, t_deaerator, h_deaerator, self.p_deaerator

    def ejector_options(self):
        """Рассчитывает параметры отсоса в эжектор уплотнений."""
        g_ejectors: List[float] = [0.0] * (self.count_parts - 2)
        t_ejectors: List[float] = [0.0] * (self.count_parts - 2)
        h_ejectors: List[float] = [0.0] * (self.count_parts - 2)
        p_ejectors: List[float] = [0.0] * (self.count_parts - 2)

        # Расчёт в зависимости от количества участков
        if self.count_parts == 2:
            # Один отсос в эжектор
            g_ejectors[0] = (self.g_parts[1] + self.g_parts[0]) * self.count_valves
            h_ejectors[0] = (self.h_parts[1] * self.g_parts[1] + self.h_parts[0] * self.g_parts[0]) / (
                    self.g_parts[1] + self.g_parts[0])
            t_ejectors[0] = ph(p_ejectors[0], h_ejectors[0], 1)
            p_ejectors[0] = self.p_suctions[0]
        elif self.count_parts == 3:
            # Один отсос в эжектор
            g_ejectors[0] = (self.g_parts[2] + self.g_parts[1]) * self.count_valves
            h_ejectors[0] = (self.h_parts[2] * self.g_parts[2] + self.h_parts[1] * self.g_parts[1]) / (
                    self.g_parts[2] + self.g_parts[1])
            t_ejectors[0] = ph(self.p_suctions[0], h_ejectors[0], 1)
            p_ejectors[0] = self.p_suctions[0]
        elif self.count_parts == 4:
            # Два отсоса в эжектор
            # Первый отсос
            g_ejectors[0] = abs(self.g_parts[3] - self.g_parts[2] - self.g_parts[1]) * self.count_valves
            h_ejectors[0] = self.h_parts[1]
            t_ejectors[0] = ph(self.p_suctions[0], h_ejectors[0], 1)
            p_ejectors[0] = self.p_suctions[0]

            # Второй отсос
            g_ejectors[1] = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h_ejectors[1] = (self.h_parts[3] * self.g_parts[3] + self.h_parts[2] * self.g_parts[2]) / (
                    self.g_parts[3] + self.g_parts[2])
            t_ejectors[1] = ph(self.p_suctions[1], h_ejectors[1], 1)
            p_ejectors[1] = self.p_suctions[1]
        elif self.count_parts == 5:
            # Три отсоса в эжектор
            # Первый отсос
            g_ejectors[0] = abs(self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h_ejectors[0] = self.h_parts[1]
            t_ejectors[0] = ph(self.p_suctions[0], h_ejectors[0], 1)
            p_ejectors[0] = self.p_suctions[0]

            # Второй отсос
            g_ejectors[1] = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h_ejectors[1] = self.h_parts[2]
            t_ejectors[1] = ph(self.p_suctions[1], h_ejectors[1], 1)
            p_ejectors[1] = self.p_suctions[1]

            # Третий отсос
            g_ejectors[2] = (self.g_parts[4] + self.g_parts[3]) * self.count_valves
            h_ejectors[2] = (self.h_parts[4] * self.g_parts[4] + self.h_parts[3] * self.g_parts[3]) / (
                    self.g_parts[4] + self.g_parts[3])
            t_ejectors[2] = ph(self.p_suctions[2], h_ejectors[2], 1)
            p_ejectors[2] = self.p_suctions[2]
        else:
            handle_error("Неверное количество секций клапана.")
        logger.info(
            f"Calculated values for ejector: G={g_ejectors}, T={t_ejectors}, H={h_ejectors}, P={p_ejectors}")

        return tuple(g_ejectors), tuple(t_ejectors), tuple(h_ejectors), tuple(p_ejectors)


class TestValveCalculator(unittest.TestCase):
    def setUp(self):
        # Подготовка тестовых данных
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=2,
            p_ejector=[0.97, 0.97],
            p_values=[130, 6, 1.03]
        )
        valve_info = ValveInfo(
            rounding_radius=2,
            calculated_gap=0.271,
            rod_diameter=36,
            section_lengths=[513, 89, 68]
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations(self):
        # Выполнение расчётов
        result = self.calculator.perform_calculations()

        # Проверка результатов
        expected_Gi = [0.5588846211298416, 0.04259835717030393, 0.004582675946052876]  # Пример ожидаемых значений Gi
        expected_Pi_in = [13.0, 0.6000000000000001, 0.10300000000000001]  # Ожидаемые значения давления, в МПа
        expected_Ti = [554.9999999999999, 500.53486287352973, 40]  # Пример ожидаемых значений температур
        expected_Hi = [3484.4816426068674, 3484.4816426068674, 40.24]  # Пример ожидаемых значений энтальпий

        self.assertEqual(result["Gi"], expected_Gi)
        self.assertEqual(result["Pi_in"], expected_Pi_in)
        self.assertEqual(result["Ti"], expected_Ti)
        self.assertEqual(result["Hi"], expected_Hi)

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result["Gi"][i], expected_Gi[i], places=3)

        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result["Pi_in"][i], expected_Pi_in[i], places=2)

        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result["Ti"][i], expected_Ti[i], places=1)

        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result["Hi"][i], expected_Hi[i], places=0)

        expected_deaerator_props = [1.009, 500.53486287352973, 3484.4816426068674,
                                    0.6]  # Ожидаемые значения: [g_deaerator, t_deaerator, h_deaerator, p_deaerator]

        # Сравниваем ожидаемые значения с реальными
        for i, expected_value in enumerate(expected_deaerator_props):
            self.assertAlmostEqual(result["deaerator_props"][i], expected_value, places=1)

        # Проверка параметров эжектора
        expected_ejector_props = [
            {"g": 0.0943620662327136, "t": 337.26128079846364, "h": 3149.943751309693, "p": 0.097},
        ]

        for i, expected in enumerate(expected_ejector_props):
            ejector = result["ejector_props"][i]
            self.assertAlmostEqual(ejector["g"], expected["g"], places=1)
            self.assertAlmostEqual(ejector["t"], expected["t"], places=1)
            self.assertAlmostEqual(ejector["h"], expected["h"], places=0)
            self.assertAlmostEqual(ejector["p"], expected["p"], places=2)


class TestValveCalculatorTwo(unittest.TestCase):
    def setUp(self):
        # Подготовка тестовых данных
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=4,
            p_ejector=[0.97, 0.97, 0.97],
            p_values=[130, 10, 0.97, 1.03]
        )
        valve_info = ValveInfo(
            rounding_radius=2,
            calculated_gap=0.215,
            rod_diameter=40,
            section_lengths=[319.5, 50, 25, 37.5]
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations_two(self):
        # Выполнение расчётов
        result = self.calculator.perform_calculations()

        # Проверка результатов
        expected_Gi = [0.5588846211298416, 0.04259835717030393, 0.004582675946052876,
                       0.0001]  # Пример ожидаемых значений Gi
        expected_Pi_in = [13.0, 0.6000000000000001, 0.6000000000000001,
                          0.10300000000000001]  # Ожидаемые значения давления, в МПа
        expected_Ti = [554.9999999999999, 500.53486287352973, 40]  # Пример ожидаемых значений температур
        expected_Hi = [3484.4816426068674, 3484.4816426068674, 40.24]  # Пример ожидаемых значений энтальпий

        self.assertEqual(result["Gi"], expected_Gi)
        self.assertEqual(result["Pi_in"], expected_Pi_in)
        self.assertEqual(result["Ti"], expected_Ti)
        self.assertEqual(result["Hi"], expected_Hi)

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result["Gi"][i], expected_Gi[i], places=3)

        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result["Pi_in"][i], expected_Pi_in[i], places=2)

        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result["Ti"][i], expected_Ti[i], places=1)

        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result["Hi"][i], expected_Hi[i], places=0)

        expected_deaerator_props = [1.009, 500.53486287352973, 3484.4816426068674,
                                    0.6]  # Ожидаемые значения: [g_deaerator, t_deaerator, h_deaerator, p_deaerator]

        # Сравниваем ожидаемые значения с реальными
        for i, expected_value in enumerate(expected_deaerator_props):
            self.assertAlmostEqual(result["deaerator_props"][i], expected_value, places=1)

        # Проверка параметров эжектора
        expected_ejector_props = [
            {"g": 0.0943620662327136, "t": 337.26128079846364, "h": 3149.943751309693, "p": 0.097},
        ]

        for i, expected in enumerate(expected_ejector_props):
            ejector = result["ejector_props"][i]
            self.assertAlmostEqual(ejector["g"], expected["g"], places=1)
            self.assertAlmostEqual(ejector["t"], expected["t"], places=1)
            self.assertAlmostEqual(ejector["h"], expected["h"], places=0)
            self.assertAlmostEqual(ejector["p"], expected["p"], places=2)


class TestValveCalculatorThree(unittest.TestCase):
    def setUp(self):
        # Подготовка тестовых данных
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=4,
            p_ejector=[0.97, 0.97, 0.97],
            p_values=[130, 7, 0.97, 1.03]
        )
        valve_info = ValveInfo(
            rounding_radius=2,
            calculated_gap=0.205,
            rod_diameter=36,
            section_lengths=[438.5, 50, 25, 37.5]
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations_three(self):
        # Выполнение расчётов
        result = self.calculator.perform_calculations()

        # Проверка результатов
        expected_Gi = [0.5588846211298416, 0.04259835717030393, 0.004582675946052876,
                       0.0001]  # Пример ожидаемых значений Gi
        expected_Pi_in = [13.0, 0.6000000000000001, 0.6000000000000001,
                          0.10300000000000001]  # Ожидаемые значения давления, в МПа
        expected_Ti = [554.9999999999999, 500.53486287352973, 40]  # Пример ожидаемых значений температур
        expected_Hi = [3484.4816426068674, 3484.4816426068674, 40.24]  # Пример ожидаемых значений энтальпий

        self.assertEqual(result["Gi"], expected_Gi)
        self.assertEqual(result["Pi_in"], expected_Pi_in)
        self.assertEqual(result["Ti"], expected_Ti)
        self.assertEqual(result["Hi"], expected_Hi)

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result["Gi"][i], expected_Gi[i], places=3)

        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result["Pi_in"][i], expected_Pi_in[i], places=2)

        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result["Ti"][i], expected_Ti[i], places=1)

        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result["Hi"][i], expected_Hi[i], places=0)

        expected_deaerator_props = [1.009, 500.53486287352973, 3484.4816426068674,
                                    0.6]  # Ожидаемые значения: [g_deaerator, t_deaerator, h_deaerator, p_deaerator]

        # Сравниваем ожидаемые значения с реальными
        for i, expected_value in enumerate(expected_deaerator_props):
            self.assertAlmostEqual(result["deaerator_props"][i], expected_value, places=1)

        # Проверка параметров эжектора
        expected_ejector_props = [
            {"g": 0.0943620662327136, "t": 337.26128079846364, "h": 3149.943751309693, "p": 0.097},
        ]

        for i, expected in enumerate(expected_ejector_props):
            ejector = result["ejector_props"][i]
            self.assertAlmostEqual(ejector["g"], expected["g"], places=1)
            self.assertAlmostEqual(ejector["t"], expected["t"], places=1)
            self.assertAlmostEqual(ejector["h"], expected["h"], places=0)
            self.assertAlmostEqual(ejector["p"], expected["p"], places=2)


class TestValveCalculatorFour(unittest.TestCase):
    def setUp(self):
        # Подготовка тестовых данных
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=2,
            p_ejector=[0.97, 0.97],
            p_values=[130, 8.35, 1.03]
        )
        valve_info = ValveInfo(
            rounding_radius=2,
            calculated_gap=0.28,
            rod_diameter=38,
            section_lengths=[161.5, 102.5, 50.5]
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations_four(self):
        # Выполнение расчётов
        result = self.calculator.perform_calculations()

        # Проверка результатов
        expected_Gi = [0.5588846211298416, 0.04259835717030393, 0.004582675946052876,
                       0.0001]  # Пример ожидаемых значений Gi
        expected_Pi_in = [13.0, 0.6000000000000001, 0.6000000000000001,
                          0.10300000000000001]  # Ожидаемые значения давления, в МПа
        expected_Ti = [554.9999999999999, 500.53486287352973, 40]  # Пример ожидаемых значений температур
        expected_Hi = [3484.4816426068674, 3484.4816426068674, 40.24]  # Пример ожидаемых значений энтальпий

        self.assertEqual(result["Gi"], expected_Gi)
        self.assertEqual(result["Pi_in"], expected_Pi_in)
        self.assertEqual(result["Ti"], expected_Ti)
        self.assertEqual(result["Hi"], expected_Hi)

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result["Gi"][i], expected_Gi[i], places=3)

        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result["Pi_in"][i], expected_Pi_in[i], places=2)

        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result["Ti"][i], expected_Ti[i], places=1)

        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result["Hi"][i], expected_Hi[i], places=0)

        expected_deaerator_props = [1.009, 500.53486287352973, 3484.4816426068674,
                                    0.6]  # Ожидаемые значения: [g_deaerator, t_deaerator, h_deaerator, p_deaerator]

        # Сравниваем ожидаемые значения с реальными
        for i, expected_value in enumerate(expected_deaerator_props):
            self.assertAlmostEqual(result["deaerator_props"][i], expected_value, places=1)

        # Проверка параметров эжектора
        expected_ejector_props = [
            {"g": 0.0943620662327136, "t": 337.26128079846364, "h": 3149.943751309693, "p": 0.097},
        ]

        for i, expected in enumerate(expected_ejector_props):
            ejector = result["ejector_props"][i]
            self.assertAlmostEqual(ejector["g"], expected["g"], places=1)
            self.assertAlmostEqual(ejector["t"], expected["t"], places=1)
            self.assertAlmostEqual(ejector["h"], expected["h"], places=0)
            self.assertAlmostEqual(ejector["p"], expected["p"], places=2)


if __name__ == '__main__':
    unittest.main()
