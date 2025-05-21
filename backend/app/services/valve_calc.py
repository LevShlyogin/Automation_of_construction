from math import sqrt, pi
from typing import Optional, List
import logging
from backend.app.schemas import CalculationParams, ValveInfo, CalculationResult
from seuif97 import pt2h, ph, ph2v, ph2t
from WSAProperties import air_calc, ksi_calc, lambda_calc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

class ValveCalculator:
    """Класс для выполнения всех расчетов, связанных с клапаном и турбиной."""

    def __init__(self, params: CalculationParams, valve_info: ValveInfo):
        self.params = params
        self.valve_info = valve_info
        try:
            # Инициализация всех необходимых полей
            self.temperature_start_DB = params.temperature_start
            self.t_air = params.t_air
            self.h_air = calculate_enthalpy_for_air(self.t_air)
            self.count_valves = params.count_valves

            self.radius_rounding_DB = valve_info.round_radius
            self.delta_clearance_DB = valve_info.clearance
            self.diameter_stock_DB = valve_info.diameter
            self.len_parts_DB = valve_info.section_lengths

            # Конвертация измерений в метры
            self.radius_rounding = convert_to_meters(self.radius_rounding_DB, "радиус скругления")
            self.delta_clearance = convert_to_meters(self.delta_clearance_DB, "зазор")
            self.diameter_stock = convert_to_meters(self.diameter_stock_DB, "диаметр штока")
            self.len_parts = [convert_to_meters(length, f"участок {i + 1}") for i, length in
                              enumerate(self.len_parts_DB) if
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
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}", exc_info=True)
            raise CalculationError(f"Ошибка при инициализации: {str(e)}")

    def perform_calculations(self) -> CalculationResult:
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
            return CalculationResult(**result)  # <-- Возврат результата после цикла
        except CalculationError as ce:
            logger.error(f"Calculation error: {ce.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during calculations: {str(e)}")
            raise CalculationError(f"Ошибка в расчётах: {str(e)}")

    def calculate_area1(self):
        """Выполняет расчеты для участка 1."""
        logger.info("Starting calculation for area 1")
        try:
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
        except Exception as e:
            logger.error(f"Error in calculate_area1: {str(e)}", exc_info=True)
            raise

    def calculate_area2(self):
        """Выполняет расчеты для участка 2."""
        logger.info("Starting calculation for area 1")
        try:
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
                logger.error("Клапан должен иметь как минимум два участка.")
                raise CalculationError("Клапан должен иметь как минимум два участка.")
        except Exception as e:
            logger.error(f"Error in calculate_area2: {str(e)}", exc_info=True)
            raise

    def calculate_area3(self):
        """Выполняет расчеты для участка 3."""
        logger.info("Starting calculation for area 3")
        try:
            if self.count_parts >= 3:
                if self.len_parts[2]:
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
                    logger.error("Длина третьего участка должна быть ненулевой.")
                    raise CalculationError("Длина третьего участка должна быть ненулевой.")
            else:
                logger.error("Клапан должен иметь как минимум три участка.")
                raise CalculationError("Клапан должен иметь как минимум три участка.")
        except Exception as e:
            logger.error(f"Error in calculate_area3: {str(e)}", exc_info=True)
            raise

    def calculate_area4(self):
        """Выполняет расчеты для участка 4."""
        logger.info("Starting calculation for area 4")
        try:
            if self.count_parts >= 4:
                if self.len_parts[3]:
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
                    logger.error("Длина четвертого участка должна быть ненулевой.")
                    raise CalculationError("Длина четвертого участка должна быть ненулевой.")
            else:
                logger.error("Клапан должен иметь как минимум четыре участка.")
                raise CalculationError("Клапан должен иметь как минимум четыре участка.")
        except Exception as e:
            logger.error(f"Error in calculate_area4: {str(e)}", exc_info=True)
            raise

    def calculate_area5(self):
        """Выполняет расчеты для участка 5."""
        logger.info("Starting calculation for area 5")
        try:
            if self.count_parts >= 5:
                if self.len_parts[4]:
                    self.p_ejector = self.p_suctions[3]
                    self.h_parts[4] = self.enthalpy_steam
                    self.v_parts[4] = ph(self.P_values[4], self.h_parts[4], 3)
                    self.t_parts[4] = ph(self.P_values[4], self.h_parts[4], 1)
                    self.din_vis_parts[4] = ph(self.P_values[4], self.h_parts[4], 24)
                    self.g_parts[4] = part_props_detection(
                        self.P_values[4], self.p_ejector, self.v_parts[4], self.din_vis_parts[4],
                        self.len_parts[4], self.delta_clearance, self.S, self.KSI
                    )
                    logger.info(
                        f"Calculated values for area 5: G={self.g_parts[4]}, T={self.t_parts[4]}, H={self.h_parts[4]}")
                else:
                    logger.error("Длина пятого участка должна быть ненулевой.")
                    raise CalculationError("Длина пятого участка должна быть ненулевой.")
            else:
                logger.error("Клапан должен иметь как минимум пять участков.")
                raise CalculationError("Клапан должен иметь как минимум пять участков.")
        except Exception as e:
            logger.error(f"Error in calculate_area5: {str(e)}", exc_info=True)
            raise

    def deaerator_options(self):
        """Вычисляет параметры отсоса в деаэратор."""
        g_deaerator = self.g_parts[0]
        t_deaerator = self.t_parts[0]
        h_deaerator = self.h_parts[0]
        p_deaerator = self.p_deaerator
        return g_deaerator, t_deaerator, h_deaerator, p_deaerator

    def ejector_options(self):
        """Вычисляет параметры отсоса в эжектор."""
        g_ejectors = [self.g_parts[i] for i in range(1, self.count_parts)]
        t_ejectors = [self.t_parts[i] for i in range(1, self.count_parts)]
        h_ejectors = [self.h_parts[i] for i in range(1, self.count_parts)]
        p_ejectors = [self.p_suctions[i] for i in range(len(self.p_suctions))]
        return g_ejectors, t_ejectors, h_ejectors, p_ejectors 