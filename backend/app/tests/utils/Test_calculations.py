from math import sqrt, pi
from typing import Tuple
import logging

# Импорт необходимых функций из внешних библиотек
from seuif97 import pt2h, ph, ph2v, ph2t
from WSAProperties import air_calc, ksi_calc, lambda_calc

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            convert_pressure_to_mpa(p, unit=5) if p > 0 else ValueError(f"Давление участка не может быть нулевым или отрицательным")
            for p in self.params.p_values[:self.count_parts]
        ]
        if len(self.P_values) != self.count_parts:
            raise ValueError(
                f"Количество значений давления ({len(self.P_values)}) не соответствует количеству участков ({self.count_parts})."
            )

        #Давление в деаэратор всегда по дефолту равно
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

        # Инициализация дополнительных атрибутов
        self.p_ejector: Optional[float] = None

    def perform_calculations(self) -> dict:
        """Выполняет все расчеты и возвращает результаты."""
        try:
            # Динамически вызываем методы расчёта участков
            for i in range(self.count_parts):
                getattr(self, f'calculate_area{i + 1}')()

            # Вычисление параметров отсоса в деаэратор и эжектор
            g_deaerator, t_deaerator, p_deaerator_final, h_deaerator = self.deaerator_options()
            g_ejector, t_ejector, p_ejector_final, h_ejector = self.ejector_options()

            # Подготовка результатов
            result = {
                "Gi": self.g_parts[:self.count_parts],
                "Pi_in": self.P_values[:self.count_parts],
                "Ti": self.t_parts[:self.count_parts],
                "Hi": self.h_parts[:self.count_parts],
                "deaerator_props": [g_deaerator, t_deaerator, p_deaerator_final, h_deaerator],
                "ejector_props": [g_ejector, t_ejector, p_ejector_final, h_ejector]
            }
            return result

        except CalculationError as ce:
            logger.error(f"Calculation error: {ce.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during calculations: {str(e)}")
            raise CalculationError(f"Ошибка в расчётах: {str(e)}")

    def calculate_area1(self):
        """Выполняет расчеты для участка 1."""
        if self.count_parts >= 1:
            if self.len_parts[1]:
                self.h_parts[0] = self.enthalpy_steam
                self.v_parts[0] = ph2v(self.P_values[0], self.h_parts[0])
                self.t_parts[0] = ph2t(self.P_values[0], self.h_parts[0])
                self.din_vis_parts[0] = ph(self.P_values[0], self.h_parts[0], 24)
                self.g_parts[0] = part_props_detection(
                    self.P_values[0], self.P_values[1], self.v_parts[0], self.din_vis_parts[0],
                    self.len_parts[0], self.delta_clearance, self.S, self.KSI
                )

    def calculate_area2(self):
        """Выполняет расчеты для участка 2."""
        if self.count_parts >= 2:
            if self.len_parts[2]:  # Исправлено с len_part3 на len_parts[2]
                self.p_ejector = self.p_suctions[0]
                self.h_parts[1] = self.enthalpy_steam
                self.v_parts[1] = ph(self.P_values[1], self.h_parts[1], 3)
                self.t_parts[1] = ph(self.P_values[1], self.h_parts[1], 1)
                self.din_vis_parts[1] = ph(self.P_values[1], self.h_parts[1], 24)
                self.g_parts[1] = part_props_detection(
                    self.P_values[1], self.p_ejector, self.v_parts[1], self.din_vis_parts[1],
                    self.len_parts[1], self.delta_clearance, self.S, self.KSI
                )
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

                # Calculate properties for part 2
                self.h_parts[1] = self.h_air
                self.t_parts[1] = self.t_air
                self.v_parts[1] = air_calc(self.t_parts[1], 1)
                self.din_vis_parts[1] = air_calc(self.t_parts[1], 2)
                self.g_parts[1] = part_props_detection(
                    0.1013, self.p_ejector, self.v_parts[1], self.din_vis_parts[1],
                    self.len_parts[1], self.delta_clearance, self.S, self.KSI, last_part=True
                )

    def calculate_area3(self):
        """Выполняет расчеты для участка 3."""
        if self.count_parts >= 3:
            if self.len_parts[3]:  # Исправлено с len_part4 на len_parts[3]
                self.p_ejector = self.p_suctions[1]
                self.h_parts[2] = self.enthalpy_steam
                self.v_parts[2] = ph(self.P_values[2], self.h_parts[2], 3)
                self.t_parts[2] = ph(self.P_values[2], self.h_parts[2], 1)
                self.din_vis_parts[2] = ph(self.P_values[2], self.h_parts[2], 24)
                self.g_parts[2] = part_props_detection(
                    self.P_values[2], self.p_ejector, self.v_parts[2], self.din_vis_parts[2],
                    self.len_parts[2], self.delta_clearance, self.S, self.KSI
                )
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

    def calculate_area4(self):
        """Выполняет расчеты для участка 4."""
        if self.count_parts >= 4:
            if self.len_parts[4]:  # Исправлено с len_part5 на len_parts[4]
                self.p_ejector = self.p_suctions[2]
                self.h_parts[3] = self.enthalpy_steam
                self.v_parts[3] = ph(self.P_values[3], self.h_parts[3], 3)
                self.t_parts[3] = ph(self.P_values[3], self.h_parts[3], 1)
                self.din_vis_parts[3] = ph(self.P_values[3], self.h_parts[3], 24)
                self.g_parts[3] = part_props_detection(
                    self.P_values[3], self.p_ejector, self.v_parts[3], self.din_vis_parts[3],
                    self.len_parts[3], self.delta_clearance, self.S, self.KSI
                )
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

    def deaerator_options(self) -> Tuple[float, float, float, float]:
        """Рассчитывает параметры отсоса в деаэратор."""
        g_deaerator: float = 0.0
        t_deaerator: float = 0.0
        h_deaerator: float = self.h_parts[1]

        # Расчёт массового расхода и температуры в зависимости от количества участков
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

        return g_deaerator, t_deaerator, self.p_deaerator, h_deaerator


    def ejector_options(self) -> Tuple[float, float, float, float]:
        """Рассчитывает параметры отсоса в эжектор уплотнений."""
        g_ejector: float = 0.0
        t_ejector: float = 0.0
        h_ejector: float = 0.0

        # Расчёт в зависимости от количества участков
        if self.count_parts == 2:
            g_ejector = self.g_parts[1] * self.count_valves
            h_ejector = self.h_parts[1]
            t_ejector = ph(self.p_suctions[0], h_ejector, 1)
        elif self.count_parts == 3:
            g_ejector = (self.g_parts[1] + self.g_parts[2]) * self.count_valves
            h_ejector = (self.h_parts[1] * self.g_parts[1] + self.h_parts[2] * self.g_parts[2]) / (self.g_parts[1] + self.g_parts[2])
            t_ejector = ph(self.p_suctions[0], h_ejector, 1)
        elif self.count_parts == 4:
            g_first_suction = (self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * self.count_valves
            g_second_suction = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h_second_suction = (self.h_parts[3] * self.g_parts[3] + self.h_parts[2] * self.g_parts[2]) / (self.g_parts[3] + self.g_parts[2])
            g_ejector = g_first_suction + g_second_suction
            h_ejector = (g_second_suction * h_second_suction + g_first_suction * self.h_parts[1]) / (g_second_suction + g_first_suction)
            t_ejector = ph(self.p_suctions[0], h_ejector, 1)
        elif self.count_parts == 5:
            g_first_suction = self.g_parts[1] - self.g_parts[2] - self.g_parts[3]
            g_second_suction = abs(self.g_parts[2] - self.g_parts[3])
            g_third_suction = self.g_parts[3] + self.g_parts[4]
            h_third_suction = (self.h_parts[4] * self.g_parts[4] + self.h_parts[3] * self.g_parts[3]) / (self.g_parts[4] + self.g_parts[3])
            g_ejector = (g_first_suction + g_second_suction + g_third_suction) * self.count_valves
            h_ejector = (
                (g_third_suction * h_third_suction + g_second_suction * self.h_parts[1] + g_first_suction * self.h_parts[1]) /
                (g_third_suction + g_second_suction + g_first_suction)
            )
            t_ejector = ph(self.p_suctions[0], h_ejector, 1)
        else:
            handle_error("Неверное количество секций клапана.")

        return g_ejector, t_ejector, self.p_suctions[0], h_ejector

    def handle_error(self, message):
        raise ValueError(message)

import unittest
from math import sqrt, pi
from typing import Optional

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
        expected_Gi = [0.123, 0.234, 0.345, 0.456, 0.567]  # Пример ожидаемых значений Gi
        expected_Pi_in = [10, 5, 3, 2, 1]  # Ожидаемые значения давления
        expected_Ti = [450, 400, 350, 300, 250]  # Пример ожидаемых значений температур
        expected_Hi = [3000, 2500, 2000, 1500, 1000]  # Пример ожидаемых значений энтальпий

        self.assertEqual(result["Gi"], expected_Gi)
        self.assertEqual(result["Pi_in"], expected_Pi_in)
        self.assertEqual(result["Ti"], expected_Ti)
        self.assertEqual(result["Hi"], expected_Hi)

        # Проверка параметров деаэратора и эжектора
        expected_deaerator_props = [0.1, 300, 5, 2500]  # Пример ожидаемых значений для деаэратора
        expected_ejector_props = [0.2, 350, 1, 1500]  # Пример ожидаемых значений для эжектора

        self.assertEqual(result["deaerator_props"], expected_deaerator_props)
        self.assertEqual(result["ejector_props"], expected_ejector_props)

if __name__ == '__main__':
    unittest.main()