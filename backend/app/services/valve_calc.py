from math import sqrt, pi
from typing import Optional, List
import logging
from enum import Enum
from backend.app.schemas import CalculationParams, ValveInfo, CalculationResult
from seuif97 import pt2h, ph, ph2v, ph2t
from WSAProperties import air_calc, ksi_calc, lambda_calc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- КОНСТАНТЫ ---
MM_TO_METERS_CONVERSION_FACTOR = 0.001
STANDARD_ATMOSPHERIC_PRESSURE_MPA = 0.101325
AIR_ENTHALPY_COEFFICIENT = 1.006  # кДж/(кг*К) для воздуха (приближенно cp)
G_FIND_CONVERSION_FACTOR = 3.6 # кг/ч
PASCAL_TO_MPA = 1e-6
KPA_TO_MPA = 1e-3
KGS_CM2_TO_MPA = 0.0980665
TECH_ATM_TO_MPA = 0.101325 # Это фактически стандартная атмосфера, обычно атм. техн. другая
BAR_TO_MPA = 0.1
PHYS_ATM_TO_MPA = 0.101325

# Коды свойств для seuif97.ph (если библиотека не предоставляет свои)
class SteamProperty(Enum):
    TEMPERATURE = 1         # T, °C
    PRESSURE = 2            # P, МПа
    SPECIFIC_VOLUME = 3     # v, м³/кг
    # ... добавьте другие по мере необходимости
    DYNAMIC_VISCOSITY = 24  # мю, Па·с


# Коды свойств для WSAProperties.air_calc
class AirProperty(Enum):
    SPECIFIC_VOLUME = 1     # v, м³/кг
    DYNAMIC_VISCOSITY = 2   # мю, Па·с


# --- ИСКЛЮЧЕНИЯ ---
class CalculationError(Exception):
    """Кастомное исключение для ошибок расчетов."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# --- РЕЗУЛЬТИРУЮЩАЯ МОДЕЛЬ ---
class EjectorProperties(BaseModel):
    g: float
    t: float
    h: float
    p: float

# --- УТИЛИТАРНЫЕ ФУНКЦИИ ---
def convert_mm_to_meters(value: Optional[float], description: str) -> float:
    """Конвертирует значение из мм в метры. Выбрасывает ValueError, если значение None."""
    if value is None:
        raise ValueError(f"Отсутствует значение для '{description}' (ожидалось в мм).")
    return float(value) * MM_TO_METERS_CONVERSION_FACTOR

def calculate_air_enthalpy(t_air_celsius: float) -> float:
    """Рассчитывает энтальпию для воздуха на основе температуры в °C."""
    # Приближенно h = cp * T(K). Для T в °C: h = cp * (T°C + 273.15)
    # Если 1.006 используется как cp, и результат должен быть в кДж/кг,
    # а t_air в °C, то исходная формула t_air * 1.006 предполагает, что это некая удельная теплоемкость,
    # умноженная на температуру в Цельсиях, что физически не совсем корректно для абсолютной энтальпии.
    # Однако, если это для расчета РАЗНОСТИ энтальпий или это условная энтальпия, оставим как есть.
    # Уточнение: для идеального газа энтальпия зависит только от температуры. h = cp*T.
    # cp для воздуха ~1.005 кДж/(кг*К). Если t_air в градусах Цельсия, то
    # h = 1.005 * (t_air + 273.15) [кДж/кг] если нулевая энтальпия при 0К.
    # Если нулевая энтальпия при 0°C, то h = 1.005 * t_air.
    # Формула t_air * 1.006 очень похожа на последнее. Будем считать, что это условная энтальпия относительно 0°C.
    return t_air_celsius * AIR_ENTHALPY_COEFFICIENT

def convert_pressure_to_mpa(pressure: float, unit_code: int = 5) -> float:
    """Преобразует давление в МПа из различных единиц измерения."""
    conversion_factors = {
        1: PASCAL_TO_MPA,    # Паскаль в МПа
        2: KPA_TO_MPA,       # кПа в МПа
        3: KGS_CM2_TO_MPA,   # кгс/см² в МПа
        4: TECH_ATM_TO_MPA,  # техническая атмосфера в МПа (нужно проверить это значение, обычно 1 ат = 0.0980665 МПа)
                              # Если 0.101325 - это физ. атмосфера, то код 6.
        5: BAR_TO_MPA,       # бар в МПа
        6: PHYS_ATM_TO_MPA   # физическая атмосфера в МПа
    }
    if unit_code not in conversion_factors:
        # Вместо ValueError лучше использовать CalculationError или более специфичное
        raise ValueError(f"Неверный код единицы измерения давления: {unit_code}.")
    return pressure * conversion_factors[unit_code]

class ValveCalculator:
    """
    Класс для выполнения расчетов параметров потоков в лабиринтных уплотнениях клапана.
    """

    def __init__(self, params: CalculationParams, valve_info: ValveInfo):
        self.params = params
        self.valve_info = valve_info
        logger.info("Инициализация ValveCalculator...")

        try:
            # --- Инициализация основных параметров ---
            self.temperature_start_steam_c = params.temperature_start
            self.t_air_c = params.t_air
            self.h_air = calculate_air_enthalpy(self.t_air_c)
            self.num_valves = params.count_valves

            # --- Геометрические параметры (конвертация в метры) ---
            self._initialize_geometric_parameters()

            # --- Параметры давлений (конвертация в МПа и валидация) ---
            self._initialize_pressure_parameters()

            # Давление в деаэратор (по условию задачи, равно P_values[1])
            # Это предположение может потребовать уточнения, если P_values[1] не всегда давление деаэратора
            if self.num_parts < 2:
                raise CalculationError(
                    "Для определения давления деаэратора (P_parts_in_mpa[1]) необходимо как минимум 2 участка.")
            self.p_deaerator_mpa = self.P_parts_in_mpa[1]

            # --- Расчет общих термодинамических и гидравлических параметров ---
            # Коэффициент пропорциональности для KSI (ksi_calc)
            self.proportional_coef_ksi = self.radius_rounding_m / (self.delta_clearance_m * 2)
            self.ksi = ksi_calc(self.proportional_coef_ksi)

            # Площадь проходного сечения в зазоре
            self.S_flow_area_m2 = self.delta_clearance_m * pi * self.diameter_stock_m

            # Начальная энтальпия пара на входе в первый участок
            # Давление на входе в первый участок берется из P_parts_in_mpa[0]
            self.h_steam_initial_kj_kg = pt2h(self.P_parts_in_mpa[0], self.temperature_start_steam_c)

            # --- Инициализация списков для хранения результатов по участкам ---
            self.g_parts_kg_h: List[float] = [0.0] * self.num_parts
            self.t_parts_c: List[float] = [0.0] * self.num_parts
            self.h_parts_kj_kg: List[float] = [0.0] * self.num_parts
            self.v_parts_m3_kg: List[float] = [0.0] * self.num_parts
            self.dyn_vis_parts_pa_s: List[float] = [0.0] * self.num_parts

            logger.info("Инициализация ValveCalculator завершена успешно.")

        except ValueError as ve:  # Перехватываем ValueError из convert_mm_to_meters и др.
            logger.error(f"Ошибка значения при инициализации: {str(ve)}", exc_info=True)
            raise CalculationError(f"Ошибка значения при инициализации: {str(ve)}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при инициализации: {str(e)}", exc_info=True)
            raise CalculationError(f"Непредвиденная ошибка при инициализации: {str(e)}")

    def _initialize_geometric_parameters(self):
        """Инициализирует и валидирует геометрические параметры."""
        logger.debug("Инициализация геометрических параметров...")
        self.radius_rounding_m = convert_mm_to_meters_1(self.valve_info.round_radius, "радиус скругления")
        self.delta_clearance_m = convert_mm_to_meters_1(self.valve_info.clearance, "зазор в уплотнении")
        self.diameter_stock_m = convert_mm_to_meters_1(self.valve_info.diameter, "диаметр штока")

        # Длины участков, отфильтрованные от None и сконвертированные
        self.len_parts_m = []
        for i, length_mm in enumerate(self.valve_info.section_lengths):
            if length_mm is not None:
                # Проверка на нулевую или отрицательную длину
                if length_mm <= 0:
                    raise ValueError(
                        f"Длина участка {i + 1} должна быть положительным числом (получено: {length_mm} мм).")
                self.len_parts_m.append(convert_mm_to_meters_1(length_mm, f"длина участка {i + 1}"))

        self.num_parts = len(self.len_parts_m)
        if self.num_parts == 0:
            raise CalculationError("Не определено ни одного участка (длины участков не заданы или все нулевые).")
        logger.debug(f"Количество активных участков: {self.num_parts}")

    def _initialize_pressure_parameters(self):
        """Инициализирует и валидирует параметры давлений."""
        logger.debug("Инициализация параметров давлений...")
        # Давления на входе участков (P0, P1, P2, ...)
        # params.p_values должно содержать давления для КАЖДОГО УЧАСТКА, включая первый.
        if len(self.params.p_values) < self.num_parts:
            raise CalculationError(
                f"Количество заданных давлений на входе участков ({len(self.params.p_values)}) "
                f"меньше количества активных участков ({self.num_parts})."
            )

        self.P_parts_in_mpa: List[float] = []
        for i in range(self.num_parts):
            p_val = self.params.p_values[i]
            if p_val <= 0:
                raise ValueError(
                    f"Давление на входе участка {i + 1} должно быть положительным (получено: {p_val} бар).")
            self.P_parts_in_mpa.append(convert_pressure_to_mpa(p_val, unit_code=5))  # unit=5 для бар

        # Давления отсоса в эжекторы
        # Количество давлений отсоса должно соответствовать количеству эжекторов.
        # Обычно, если есть N участков, может быть до N-1 эжекторов (последний участок может идти в атмосферу или эжектор).
        # Исходный код связывает p_suctions с участками, начиная со второго.
        # Если num_parts = 2, нужен 1 p_suction. Если num_parts = 3, нужно 2 p_suction (для выхода из 2-го и 3-го).
        # Это означает, len(p_ejector) должно быть self.num_parts - 1.
        # Однако, исходный код в calculate_areaX обращается к self.p_suctions[0], self.p_suctions[1] и т.д.
        # для участков 2, 3 .... Это значит, что self.p_suctions[i] - это давление на выходе из участка (i+2).
        # Например, self.p_suctions[0] - давление на выходе из участка 2 (part_index=1).
        # self.p_suctions[1] - давление на выходе из участка 3 (part_index=2).
        # Количество p_ejector должно быть self.num_parts - 1.

        expected_p_ejector_count = self.num_parts - 1  # Если первый участок не идет в эжектор напрямую
        if not self.params.p_ejector and expected_p_ejector_count > 0:
            raise CalculationError(
                f"Ожидается {expected_p_ejector_count} давлений отсоса в эжекторы (p_ejector), получено 0.")
        if self.params.p_ejector and len(self.params.p_ejector) != expected_p_ejector_count:
            raise CalculationError(
                f"Количество давлений отсоса в эжекторы ({len(self.params.p_ejector)}) "
                f"не соответствует ожидаемому ({expected_p_ejector_count} для {self.num_parts} участков)."
            )

        self.P_ejectors_mpa: List[float] = []
        if self.params.p_ejector:
            for i, p_val in enumerate(self.params.p_ejector):
                if p_val <= 0:
                    raise ValueError(
                        f"Давление отсоса эжектора {i + 1} должно быть положительным (получено: {p_val} бар).")
                self.P_ejectors_mpa.append(convert_pressure_to_mpa(p_val, unit_code=5))

    @staticmethod
    def _g_find(is_last_part_of_flow_path: bool, alfa: float, p_start_pa: float, p_end_pa: float,
                spec_volume_m3_kg: float, flow_area_m2: float) -> float:
        """
        Вычисляет массовый расход G.
        Давления p_start_pa, p_end_pa должны быть в Паскалях.
        Результат в кг/ч.
        """
        if p_start_pa <= p_end_pa:  # Предотвращение sqrt от отрицательного или нуля, если давления равны или инвертированы
            # Если p_start_pa == p_end_pa, то G будет 0, что логично.
            # Если p_start_pa < p_end_pa, это нефизично для прямого потока, G также будет 0 по этой формуле (или ошибка).
            # Можно добавить небольшую дельту, как в оригинале, если это специфическое требование.
            # Однако, лучше если вызывающий код обеспечит p_start_pa > p_end_pa.
            # В данном случае, оригинальный код добавлял 0.003 к P_first если они равны, но P_first было в МПа.
            # Здесь давления в Па, так что такая корректировка должна быть больше.
            # Для большей строгости, лучше вызывать ошибку или возвращать 0.
            if p_start_pa == p_end_pa:
                p_start_pa += 0.003 * 1e6  # Добавим эквивалент 0.003 МПа, если это критично
                # logger.warning("_g_find: p_start_pa == p_end_pa. Добавлена малая дельта к p_start_pa.")
            elif p_start_pa < p_end_pa:
                logger.warning(
                    f"_g_find: p_start_pa ({p_start_pa} Pa) < p_end_pa ({p_end_pa} Pa). Расход будет 0 или ошибка.")
                return 0.0

        term_under_sqrt = (p_start_pa ** 2 - p_end_pa ** 2) / (p_start_pa * spec_volume_m3_kg)
        if term_under_sqrt < 0:  # Дополнительная проверка
            logger.error(f"Отрицательное значение под корнем в _g_find: {term_under_sqrt}. "
                         f"P1_Pa={p_start_pa}, P2_Pa={p_end_pa}, v={spec_volume_m3_kg}")
            # raise CalculationError("Расчет G невозможен: отрицательное значение под корнем.")
            return 0.0  # Или другое поведение в случае ошибки

        g_calc = alfa * flow_area_m2 * sqrt(term_under_sqrt) * G_FIND_CONVERSION_FACTOR  # кг/с -> кг/ч

        if is_last_part_of_flow_path:
            # "Для последнего участка G не может быть меньше 0.001"
            # Этот комментарий из оригинала. "Последний участок" здесь означает
            # участок, где среда - воздух, и он выходит в атмосферу/эжектор.
            g_calc = max(0.001, g_calc)
        return g_calc

    @staticmethod
    def _part_props_detection(
            p_start_mpa: float, p_end_mpa: float,
            spec_volume_m3_kg: float, dyn_vis_pa_s: float,
            len_part_m: float, delta_clearance_m: float,
            flow_area_m2: float, ksi_coeff: float,
            is_last_part_of_flow_path: bool = False,
            w_min_m_s: float = 1.0, w_max_m_s: float = 1000.0,
            tolerance: float = 0.001
    ) -> float:
        """
        Определяет массовый расход G для участка с использованием бинарного поиска скорости W.
        p_start_mpa, p_end_mpa - давления в МПа.
        """
        logger.debug(f"part_props_detection: P1={p_start_mpa:.4f}MPa, P2={p_end_mpa:.4f}MPa, v={spec_volume_m3_kg:.4g}, "
                      f"len={len_part_m:.4f}, clearance={delta_clearance_m:.4e}, area={flow_area_m2:.4e}, KSI={ksi_coeff:.4f}, "
                      f"last_part={is_last_part_of_flow_path}")

        # Корректировка давления, если оно одинаково (как в оригинале)
        # if abs(p_start_mpa - p_end_mpa) < 1e-6 : # Сравнение float
        #     p_start_mpa += 0.003  # Корректировка давления, если оно одинаково (в МПа)
        #     logger.warning(f"part_props_detection: P1 ~ P2. P1 скорректировано до {p_start_mpa:.4f} MPa.")
        # elif p_start_mpa < p_end_mpa:
        #     # Это может быть нормальной ситуацией, если поток идет против градиента давления (например, эжектор)
        #     # но для данной формулы G_find это приведет к ошибке.
        #     # В оригинальном коде такая ситуация не обрабатывалась явно на этом уровне.
        #     logger.warning(f"part_props_detection: P1 < P2 ({p_start_mpa:.4f} < {p_end_mpa:.4f}). Результат может быть неверным.")
        #     # Для избежания ошибки в sqrt в _g_find, можно вернуть 0 или обработать иначе.
        #     # Однако, _g_find уже имеет защиту.

        p_start_pa = p_start_mpa * 1e6  # Преобразование давления из МПа в Паскали
        p_end_pa = p_end_mpa * 1e6  # Преобразование давления из МПа в Паскали

        kin_vis_m2_s = spec_volume_m3_kg * dyn_vis_pa_s  # Кинематическая вязкость (v = nu / rho = v_spec * mu)

        # Бинарный поиск для скорости W
        current_w_min, current_w_max = w_min_m_s, w_max_m_s
        iteration_count = 0
        max_iterations = 100  # Защита от бесконечного цикла

        while (current_w_max - current_w_min) > tolerance and iteration_count < max_iterations:
            w_mid_m_s = (current_w_min + current_w_max) / 2
            if w_mid_m_s == 0:  # Избегаем деления на 0 в Re, если w_min и w_max близки к 0
                # Если скорость нулевая, Re тоже 0, lambda_calc может дать ошибку или большое значение.
                # Поток G тоже будет 0.
                # Эта ситуация должна обрабатываться аккуратно.
                # Если w_mid очень мал, Re будет мал, lambda может быть большим.
                # Если w_min=0, w_max=tolerance, то w_mid=tolerance/2.
                # Re = (tolerance/2 * 2 * delta_clearance_m) / kin_vis_m2_s
                # Если kin_vis_m2_s тоже мал, Re может быть большим.
                # Для простоты, если w_mid близок к нулю, G тоже должен быть близок к нулю.
                # Пропустим итерацию или установим delta_speed так, чтобы сузить диапазон.
                logger.debug("w_mid_m_s is zero or very small, adjusting search range.")
                # Если delta_speed > 0, W_max = W_mid. Если G=0, то delta_speed = W_mid > 0.
                # Значит, если w_mid -> 0, то G -> 0, delta_speed -> w_mid.
                # Это корректно приведет к W_max = W_mid, сужая диапазон к нулю.
                # Однако, lambda_calc(Re) может быть проблемой при Re=0.
                # WSAProperties.lambda_calc должна уметь обрабатывать Re=0 или очень малые Re.
                # Для Re -> 0 (ламинарный режим), lambda = 64/Re (для труб). Для щелей формула может отличаться.
                # Если lambda_calc не готова к Re=0, нужна доп. обработка.
                # Предположим, lambda_calc корректно работает.
                pass

            reynolds_num = (w_mid_m_s * 2 * delta_clearance_m) / kin_vis_m2_s

            # Обработка Re = 0 или очень малых Re, если lambda_calc к этому не готова.
            if abs(reynolds_num) < 1e-9:  # Практически нулевой Re
                lambda_val = float('inf')  # Для ламинарного потока lambda = A/Re, так что lambda -> inf при Re -> 0
                # Это приведет к ALFA -> 0, G -> 0. Что логично.
                # Однако, если lambda_calc(0) возвращает конкретное число, используем его.
                try:
                    lambda_val = lambda_calc(reynolds_num)
                except ZeroDivisionError:  # Если lambda_calc делит на Re
                    logger.warning(f"Reynolds number is near zero ({reynolds_num:.2e}), lambda might be unstable.")
                    # Установка lambda в очень большое число приведет к Alfa -> 0, G -> 0
                    lambda_val = 1e12  # Очень большое значение для lambda
                except Exception as e_lambda:
                    logger.error(f"Error in lambda_calc for Re={reynolds_num:.2e}: {e_lambda}")
                    lambda_val = 0.02  # Некоторое дефолтное значение, чтобы избежать падения
            else:
                lambda_val = lambda_calc(reynolds_num)

            # Коэффициент расхода ALFA
            # Убедимся, что знаменатель для ALFA не отрицательный и не ноль
            # (1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance)
            alfa_denominator_sq = 1 + ksi_coeff + (0.5 * lambda_val * len_part_m) / delta_clearance_m
            if alfa_denominator_sq <= 0:
                logger.warning(f"Некорректный знаменатель для ALFA^2 ({alfa_denominator_sq:.3e}) на итерации. "
                               f"Re={reynolds_num:.2e}, lambda={lambda_val:.3e}. W_mid={w_mid_m_s:.3f}")
                # Если знаменатель некорректен, это может означать, что параметры потока вышли за рамки применимости модели
                # или ошибка в lambda_calc. В такой ситуации ALFA стремится к 0 или не определена.
                # Если G должно быть 0, то delta_speed = w_mid. W_max = w_mid.
                # Это сузит диапазон к меньшим скоростям.
                current_w_max = w_mid_m_s
                iteration_count += 1
                continue

            alfa = 1 / sqrt(alfa_denominator_sq)

            g_calculated_kg_h = ValveCalculator._g_find(
                is_last_part_of_flow_path, alfa, p_start_pa, p_end_pa,
                spec_volume_m3_kg, flow_area_m2
            )

            # Расчетная скорость по G: W = G * v / S (G в кг/с)
            # G_calculated_kg_h нужно перевести в кг/с для сопоставления с W_mid_m_s
            g_calculated_kg_s = g_calculated_kg_h / 3600.0

            # Скорость, соответствующая рассчитанному G
            # W_from_G = spec_volume_m3_kg * g_calculated_kg_s / flow_area_m2 (это если G_FIND_CONVERSION_FACTOR = 1)
            # В оригинале: delta_speed = W_mid - v * G / (3.6 * S)
            # Где G - это g_calculated_kg_h (т.к. 3.6 - это G_FIND_CONVERSION_FACTOR)
            # Значит, v * G / (3.6 * S) = spec_volume_m3_kg * g_calculated_kg_h / (G_FIND_CONVERSION_FACTOR * flow_area_m2)
            # Это и есть W_from_G в м/с.
            w_from_g_m_s = spec_volume_m3_kg * g_calculated_kg_h / (G_FIND_CONVERSION_FACTOR * flow_area_m2)

            delta_speed = w_mid_m_s - w_from_g_m_s

            if delta_speed > 0:
                current_w_max = w_mid_m_s
            else:
                current_w_min = w_mid_m_s

            iteration_count += 1

        if iteration_count >= max_iterations:
            logger.warning(
                f"Достигнуто максимальное количество итераций ({max_iterations}) в бинарном поиске скорости. "
                f"P1={p_start_mpa:.3f}, P2={p_end_mpa:.3f}. Результат может быть неточным.")

        # Финальный расчет G с найденной скоростью
        w_result_m_s = (current_w_min + current_w_max) / 2
        reynolds_num_final = (w_result_m_s * 2 * delta_clearance_m) / kin_vis_m2_s

        lambda_val_final = lambda_calc(reynolds_num_final)  # Предполагаем, что lambda_calc корректно работает для Re=0
        if abs(reynolds_num_final) < 1e-9:
            try:
                lambda_val_final = lambda_calc(reynolds_num_final)
            except ZeroDivisionError:
                lambda_val_final = 1e12
            except Exception as e_lambda_final:
                logger.error(f"Error in lambda_calc (final) for Re={reynolds_num_final:.2e}: {e_lambda_final}")
                lambda_val_final = 0.02

        alfa_denominator_sq_final = 1 + ksi_coeff + (0.5 * lambda_val_final * len_part_m) / delta_clearance_m
        if alfa_denominator_sq_final <= 0:
            logger.error(f"Некорректный знаменатель для ALFA^2 (финальный расчет: {alfa_denominator_sq_final:.3e}). "
                         f"Re={reynolds_num_final:.2e}, lambda={lambda_val_final:.3e}. W_res={w_result_m_s:.3f}")
            return 0.0  # Возвращаем 0, если расчет невозможен

        alfa_final = 1 / sqrt(alfa_denominator_sq_final)

        g_final_kg_h = ValveCalculator._g_find(
            is_last_part_of_flow_path, alfa_final, p_start_pa, p_end_pa,
            spec_volume_m3_kg, flow_area_m2
        )
        # logger.debug(f"part_props_detection result: G={g_final_kg_h:.4f} kg/h, W={w_result_m_s:.4f} m/s, Re={reynolds_num_final:.2e}, Alfa={alfa_final:.4f}")
        return g_final_kg_h

    def _calculate_single_part_properties(self, part_idx: int):
        """
        Выполняет расчеты для одного участка (part_idx от 0 до num_parts-1).
        """
        logger.info(f"Расчет для участка {part_idx + 1} (из {self.num_parts})...")

        # Определение давлений на входе и выходе участка
        p_start_mpa: float = self.P_parts_in_mpa[part_idx]
        p_end_mpa: float
        is_last_physical_segment = (part_idx == self.num_parts - 1)  # Это последний участок в геометрии клапана

        # Логика определения p_end_mpa и типа среды (пар/воздух)
        # Эта логика должна точно воспроизводить оригинальные calculate_areaX

        current_h: float
        current_v: float
        current_t: float
        current_dyn_vis: float
        medium_is_air: bool = False  # Флаг, что считаем для воздуха

        if part_idx == 0:
            # Участок 1: Всегда пар, выход на P_parts_in_mpa[1] (давление деаэратора или следующего участка)
            if self.num_parts < 2:  # Должно быть обработано в __init__, но для безопасности
                raise CalculationError("Участок 1 требует наличия участка 2 для определения P_end.")
            p_end_mpa = self.P_parts_in_mpa[1]  # Давление на выходе из 1-го участка = давление на входе во 2-й.

            current_h = self.h_steam_initial_kj_kg
            current_v = ph2v(p_start_mpa, current_h)
            current_t = ph2t(p_start_mpa, current_h)
            current_dyn_vis = ph(p_start_mpa, current_h, SteamProperty.DYNAMIC_VISCOSITY.value)
        else:
            # Участки 2, 3, 4, 5...
            # Давление на выходе - это соответствующее давление отсоса p_ejector.
            # p_ejectors_mpa[0] для part_idx=1 (участок 2)
            # p_ejectors_mpa[1] для part_idx=2 (участок 3) и т.д.
            if part_idx - 1 >= len(self.P_ejectors_mpa):
                raise CalculationError(f"Не найдено давление отсоса для участка {part_idx + 1}. "
                                       f"Индекс P_ejectors_mpa: {part_idx - 1}, длина списка: {len(self.P_ejectors_mpa)}")
            p_end_mpa = self.P_ejectors_mpa[part_idx - 1]

            if is_last_physical_segment:
                # Это последний участок, он всегда работает на воздухе по логике оригинала
                # (например, calculate_area2, если count_parts=2; calculate_area3, если count_parts=3)
                medium_is_air = True
                p_start_mpa = STANDARD_ATMOSPHERIC_PRESSURE_MPA  # Для последнего участка (воздух) вход - атмосфера

                current_h = self.h_air
                current_t = self.t_air_c
                current_v = air_calc(current_t, AirProperty.SPECIFIC_VOLUME.value)
                current_dyn_vis = air_calc(current_t, AirProperty.DYNAMIC_VISCOSITY.value)
            else:
                # Промежуточный участок (не первый и не последний физический), работает на паре
                # Входное давление p_start_mpa уже установлено (self.P_parts_in_mpa[part_idx])
                # Энтальпия для этих участков в оригинале бралась как self.enthalpy_steam (т.е. начальная)
                # Это означает, что дросселирование до этого участка изоэнтальпийное.
                current_h = self.h_steam_initial_kj_kg
                current_v = ph(p_start_mpa, current_h, SteamProperty.SPECIFIC_VOLUME.value)
                current_t = ph(p_start_mpa, current_h, SteamProperty.TEMPERATURE.value)
                current_dyn_vis = ph(p_start_mpa, current_h, SteamProperty.DYNAMIC_VISCOSITY.value)

        # Запись свойств на ВХОДЕ текущего участка (кроме G, который является расходом ЧЕРЕЗ участок)
        self.h_parts_kj_kg[part_idx] = current_h
        self.t_parts_c[part_idx] = current_t
        self.v_parts_m3_kg[part_idx] = current_v
        self.dyn_vis_parts_pa_s[part_idx] = current_dyn_vis
        # P_parts_in_mpa[part_idx] уже хранит входное давление

        # Расчет массового расхода G через этот участок
        g_calculated = ValveCalculator._part_props_detection(
            p_start_mpa=p_start_mpa,
            p_end_mpa=p_end_mpa,
            spec_volume_m3_kg=current_v,
            dyn_vis_pa_s=current_dyn_vis,
            len_part_m=self.len_parts_m[part_idx],
            delta_clearance_m=self.delta_clearance_m,
            flow_area_m2=self.S_flow_area_m2,
            ksi_coeff=self.ksi,
            is_last_part_of_flow_path=medium_is_air  # Флаг для _g_find, если это последний воздушный участок
        )
        self.g_parts_kg_h[part_idx] = g_calculated

        logger.info(
            f"Участок {part_idx + 1}: G={g_calculated:.3f} кг/ч, T_in={current_t:.2f}°C, H_in={current_h:.2f} кДж/кг, "
            f"P_in={p_start_mpa:.3f}МПа, P_out={p_end_mpa:.3f}МПа, Среда={'Воздух' if medium_is_air else 'Пар'}")

    def _calculate_deaerator_outputs(self) -> Tuple[float, float, float, float]:
        """Рассчитывает параметры отсоса в деаэратор."""
        logger.info("Расчет параметров для деаэратора...")

        if self.num_parts <= 2:  # Изменено с < 2 на <= 2
            # Если участков 2 или меньше, по вашей логике, отбора в деаэратор нет,
            # или он обрабатывается как часть эжекторной системы.
            logger.info(f"Количество участков ({self.num_parts}) <= 2. "
                        "Отбор в деаэратор не рассчитывается или обрабатывается логикой эжектора. Возврат нулевых значений.")
            return 0.0, 0.0, 0.0, 0.0  # G, T, H, P

        # Логика для num_parts > 2 (т.е. 3, 4, 5...)
        # Давление деаэратора - это P_parts_in_mpa[1] (давление на выходе из 1-го участка)
        p_deaerator = self.p_deaerator_mpa

        # Энтальпия потока в деаэратор - это энтальпия на выходе из 1-го участка.
        # Процесс в уплотнении - дросселирование, энтальпия сохраняется.
        # h_out_part1 = h_in_part1 = h_parts_kj_kg[0] (энтальпия пара на входе в 1-й участок)
        h_deaerator = self.h_parts_kj_kg[0]

        try:
            t_deaerator = ph(p_deaerator, h_deaerator, SteamProperty.TEMPERATURE.value)
        except Exception as e:
            logger.warning(
                f"Не удалось рассчитать температуру для деаэратора (P={p_deaerator}, H={h_deaerator}): {e}. Установлено в 0.")
            t_deaerator = 0.0

        g_deaerator_kg_h: float = 0.0

        # Расход в деаэратор = (расход через 1-й участок) МИНУС (расходы, ушедшие в эжекторы с промежуточных паровых участков)
        # Промежуточные паровые участки - это участки с индексами от 1 до num_parts - 2 (т.е. второй участок до предпоследнего).
        # Последний участок (num_parts - 1) обычно воздушный и его расход не вычитается из деаэраторного потока.

        g_to_intermediate_ejectors = 0.0
        if self.num_parts > 2:  # Есть хотя бы один промежуточный участок (part_idx=1)
            # Суммируем расходы через участки, которые являются паровыми и не последними.
            # Индексы этих участков: 1, 2, ..., self.num_parts - 2
            # self.g_parts_kg_h[1] : расход через 2-й участок
            # self.g_parts_kg_h[self.num_parts - 2] : расход через предпоследний участок
            g_to_intermediate_ejectors = sum(self.g_parts_kg_h[i] for i in range(1, self.num_parts - 1)
                                             if self.h_parts_kj_kg[i] != self.h_air)  # Учитываем только паровые потоки

        g_deaerator_kg_h = (self.g_parts_kg_h[0] - g_to_intermediate_ejectors) * self.num_valves
        g_deaerator_kg_h = max(0.0, g_deaerator_kg_h)  # Расход не может быть отрицательным

        logger.info(f"Параметры для деаэратора: G={g_deaerator_kg_h:.3f} кг/ч, T={t_deaerator:.2f}°C, "
                    f"H={h_deaerator:.2f} кДж/кг, P={p_deaerator:.3f} МПа")
        return g_deaerator_kg_h, t_deaerator, h_deaerator, p_deaerator

    def _calculate_ejector_outputs(self) -> List[EjectorProperties]:
        """Рассчитывает параметры отсоса в эжекторы."""
        logger.info("Расчет параметров для эжекторов...")
        ejector_props_list: List[EjectorProperties] = []

        if self.num_parts < 2:
            logger.warning("Недостаточно участков для расчета параметров эжекторов (num_parts < 2).")
            return []

        # Количество эжекторов равно количеству P_ejectors_mpa, что равно num_parts - 1
        num_ejectors = self.num_parts - 1

        # Логика из оригинального ejector_options очень специфична для каждого count_parts.
        # Попытаемся ее воспроизвести.
        # g[i] = self.g_parts_kg_h[i], h[i] = self.h_parts_kj_kg[i]
        # C = self.num_valves
        # psuc[j] = self.P_ejectors_mpa[j]

        g = self.g_parts_kg_h
        h_in = self.h_parts_kj_kg  # Энтальпии на входе каждого участка
        C = self.num_valves
        psuc = self.P_ejectors_mpa

        # Общая функция для смешения энтальпий
        def mix_enthalpy(g1, h1, g2, h2) -> float:
            if (g1 + g2) == 0: return (h1 + h2) / 2  # Простое среднее, если нет потоков (маловероятно)
            return (h1 * g1 + h2 * g2) / (g1 + g2)

        if self.num_parts == 2:  # 1 эжектор (psuc[0])
            # g_ej[0] = (g[0] + g[1]) * C. h_ej[0] = mix(h[0],g[0], h[1],g[1]). p_ej[0] = psuc[0].
            # Здесь g[0] - пар, g[1] - воздух. h[0] - энтальпия пара, h[1] - энтальпия воздуха.
            ge = (g[0] + g[1]) * C
            he = mix_enthalpy(g[0], h_in[0], g[1], h_in[1])
            pe = psuc[0]
            te = ph(pe, he, SteamProperty.TEMPERATURE.value)  # ph используется, т.к. смесь может быть влажным паром
            ejector_props_list.append(EjectorProperties(g=ge, t=te, h=he, p=pe))

        elif self.num_parts == 3:  # 1 эжектор (psuc[0])
            # g_ej[0] = (g[1] + g[2]) * C. h_ej[0] = mix(h[1],g[1], h[2],g[2]). p_ej[0] = psuc[0].
            # g[1] - пар, g[2] - воздух. h[1] - энтальпия пара, h[2] - энтальпия воздуха.
            ge = (g[1] + g[2]) * C
            he = mix_enthalpy(g[1], h_in[1], g[2], h_in[2])
            pe = psuc[0]  # Давление первого эжектора (выход из участка 2)
            te = ph(pe, he, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge, t=te, h=he, p=pe))

        elif self.num_parts == 4:  # 2 эжектора (psuc[0], psuc[1])
            # Эжектор 1 (давление psuc[0], связан с выходом из участка 2)
            # Оригинал: g_ejectors[0] = abs(self.g_parts[3] - self.g_parts[2] - self.g_parts[1]) * self.count_valves
            # Это очень странная формула. g[3] - воздух, g[2] - пар, g[1] - пар.
            # Предположим, что это ошибка в оригинале, и каждый эжектор собирает "свой" поток.
            # Эжектор 1 (psuc[0]): собирает утечку g[1] (пар)
            # Эжектор 2 (psuc[1]): собирает утечку g[2] (пар) + g[3] (воздух) - это не совпадает с оригиналом.

            # Воспроизводим оригинал максимально близко:
            # Первый отсос (в эжектор с давлением psuc[0])
            # g_ejectors[0] = abs(self.g_parts[3] - self.g_parts[2] - self.g_parts[1]) * self.count_valves
            # h_ejectors[0] = self.h_parts[1]
            ge1 = abs(g[3] - g[2] - g[1]) * C  # Оригинальная формула выглядит нелогично с точки зрения баланса масс.
            # Если g[i] - это расход *через* участок i.
            # Возможно, g[i] в оригинале имело другой смысл для этих формул.
            # Уточнение: в оригинале calculate_area2, если count_parts > 2, то g_parts[1] считается для пара.
            # Если он последний (count_parts = 2), то g_parts[1] для воздуха.
            # Мой _calculate_single_part_properties это учитывает.
            # h_in[1] - энтальпия пара на входе в участок 2.
            # ge1 = g[1] * C # Альтернативная, более логичная гипотеза: эжектор 1 забирает поток g[1]
            he1 = h_in[1]  # Энтальпия пара
            pe1 = psuc[0]
            te1 = ph(pe1, he1, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge1, t=te1, h=he1, p=pe1))
            logger.warning(
                "Логика расчета G для первого эжектора при num_parts=4 взята из оригинала и может требовать проверки.")

            # Второй отсос (в эжектор с давлением psuc[1])
            # g_ejectors[1] = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            # h_ejectors[1] = (self.h_parts[3] * self.g_parts[3] + self.h_parts[2] * self.g_parts[2]) / (self.g_parts[3] + self.g_parts[2])
            ge2 = abs(g[2] - g[3]) * C
            # ge2 = (g[2] + g[3]) * C # Альтернативная гипотеза: эжектор 2 забирает сумму потоков g[2](пар) и g[3](воздух)
            he2 = mix_enthalpy(g[3], h_in[3], g[2], h_in[2])  # h_in[2]-пар, h_in[3]-воздух
            pe2 = psuc[1]
            te2 = ph(pe2, he2, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge2, t=te2, h=he2, p=pe2))
            logger.warning(
                "Логика расчета G для второго эжектора при num_parts=4 взята из оригинала и может требовать проверки.")

        elif self.num_parts == 5:  # 3 эжектора (psuc[0], psuc[1], psuc[2])
            # Первый отсос (psuc[0])
            # g_ejectors[0] = abs(self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * self.count_valves
            # h_ejectors[0] = self.h_parts[1]
            ge1 = abs(g[1] - g[2] - g[3]) * C  # g[1],g[2],g[3] - пар
            # ge1 = g[1] * C # Альтернатива
            he1 = h_in[1]  # Энтальпия пара
            pe1 = psuc[0]
            te1 = ph(pe1, he1, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge1, t=te1, h=he1, p=pe1))
            logger.warning(
                "Логика расчета G для первого эжектора при num_parts=5 взята из оригинала и может требовать проверки.")

            # Второй отсос (psuc[1])
            # g_ejectors[1] = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            # h_ejectors[1] = self.h_parts[2]
            ge2 = abs(g[2] - g[3]) * C  # g[2],g[3] - пар
            # ge2 = g[2] * C # Альтернатива
            he2 = h_in[2]  # Энтальпия пара
            pe2 = psuc[1]
            te2 = ph(pe2, he2, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge2, t=te2, h=he2, p=pe2))
            logger.warning(
                "Логика расчета G для второго эжектора при num_parts=5 взята из оригинала и может требовать проверки.")

            # Третий отсос (psuc[2])
            # g_ejectors[2] = (self.g_parts[4] + self.g_parts[3]) * self.count_valves
            # h_ejectors[2] = (self.h_parts[4] * self.g_parts[4] + self.h_parts[3] * self.g_parts[3]) / (self.g_parts[4] + self.g_parts[3])
            ge3 = (g[4] + g[3]) * C  # g[4]-воздух, g[3]-пар
            he3 = mix_enthalpy(g[4], h_in[4], g[3], h_in[3])
            pe3 = psuc[2]
            te3 = ph(pe3, he3, SteamProperty.TEMPERATURE.value)
            ejector_props_list.append(EjectorProperties(g=ge3, t=te3, h=he3, p=pe3))

        else:  # num_parts > 5 или num_parts < 2
            if self.num_parts > 5:
                logger.error(
                    f"Логика расчета эжекторов для {self.num_parts} участков не определена в оригинале. Возвращен пустой список.")
            # Для num_parts < 2 уже была бы проверка выше.
            return []

        for i, props in enumerate(ejector_props_list):
            logger.info(f"Эжектор {i + 1}: G={props.g:.3f} кг/ч, T={props.t:.2f}°C, "
                        f"H={props.h:.2f} кДж/кг, P={props.p:.3f} МПа")
        return ejector_props_list

    def perform_calculations(self) -> CalculationResult:
        """Выполняет все расчеты и возвращает результаты."""
        logger.info("Начало выполнения всех расчетов...")
        try:
            # Расчет свойств для каждого участка
            for i in range(self.num_parts):
                self._calculate_single_part_properties(i)

            # Вычисление параметров отсоса в деаэратор
            g_deaerator, t_deaerator, h_deaerator, p_deaerator = self._calculate_deaerator_outputs()

            # Вычисление параметров отсоса в эжекторы (возвращает List[EjectorProperties])
            ejector_outputs_objects = self._calculate_ejector_outputs()

            # Преобразование List[EjectorProperties] в List[Dict[str, float]]
            ejector_outputs_dicts = [props.model_dump() for props in ejector_outputs_objects]

            # Давления на ВХОДЕ участков для результата
            result_pi_in = []
            for i in range(self.num_parts):
                if i == 0:  # Первый паровой участок
                    result_pi_in.append(self.P_parts_in_mpa[0])
                elif (i == self.num_parts - 1) and self.h_parts_kj_kg[
                    i] == self.h_air:  # Последний участок, если он воздушный
                    # Входное давление для последнего (воздушного) участка - атмосферное
                    result_pi_in.append(STANDARD_ATMOSPHERIC_PRESSURE_MPA)
                else:  # Промежуточные паровые участки или последний паровой (если нет воздушного)
                    result_pi_in.append(self.P_parts_in_mpa[i])

            result = CalculationResult(
                Gi=self.g_parts_kg_h,
                Pi_in=result_pi_in,
                Ti=self.t_parts_c,
                Hi=self.h_parts_kj_kg,
                deaerator_props=[g_deaerator, t_deaerator, h_deaerator, p_deaerator],
                ejector_props=ejector_outputs_dicts
            )
            logger.info("Все расчеты успешно завершены.")
            return result

        except CalculationError as ce:
            logger.error(f"Ошибка расчета: {ce.message}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при выполнении расчетов: {str(e)}", exc_info=True)
            raise CalculationError(f"Непредвиденная ошибка в расчетах: {str(e)}")