import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from backend.app.core.config import settings


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logging.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


from math import sqrt, pi
from typing import Tuple, List
import logging
from backend.app.schemas import CalculationParams, ValveInfo

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

        # Извлечение значений давления
        self.p_suctions = self.params.p_ejector if self.params.p_ejector else []
        self.P_values = self.params.p_values
        if len(self.P_values) != 5:
            raise ValueError("Должно быть пять значений давления в p_values.")
        self.P1, self.P2, self.P3, self.P4, self.P5 = self.P_values
        self.p_deaerator = self.P2

        # Заполнение длиной участков, заполняя недостающие нулями
        self.len_parts_extended = self.len_parts + [0.0] * (5 - len(self.len_parts))
        self.len_part1, self.len_part2, self.len_part3, self.len_part4, self.len_part5 = self.len_parts_extended[:5]

        # Расчет коэффициента пропорциональности и других параметров
        self.proportional_coef = self.radius_rounding / (self.delta_clearance * 2)
        self.S = self.delta_clearance * pi * self.diameter_stock
        self.enthalpy_steam = pt2h(self.P1, self.temperature_start_DB)
        self.KSI = ksi_calc(self.proportional_coef)

        # Инициализация всех G, T и H параметров
        self.G_part1 = self.G_part2 = self.G_part3 = self.G_part4 = self.G_part5 = 0.0
        self.t_part1 = self.t_part2 = self.t_part3 = self.t_part4 = self.t_part5 = 0.0
        self.h_part1 = self.h_part2 = self.h_part3 = self.h_part4 = self.h_part5 = 0.0

    def perform_calculations(self) -> dict:
        """Выполняет все расчеты и возвращает результаты."""
        try:
            # Расчеты для каждого участка
            self.calculate_area1()
            self.calculate_area2()
            self.calculate_area3()
            self.calculate_area4()
            self.calculate_area5()

            # Вычисление параметров отсоса в деаэратор и эжектор
            g_deaerator, t_deaerator, p_deaerator_final, h_deaerator = self.deaerator_options(
                self.p_deaerator, self.count_parts, self.count_valves, self.h_part2,
                self.G_part1, self.G_part2, self.G_part3, self.G_part4
            )
            g_ejector, t_ejector, p_ejector_final, h_ejector = self.ejector_options(
                self.get_p_ejector_final(), self.count_parts, self.count_valves,
                self.G_part2, self.h_part2, self.G_part3, self.h_part3,
                self.G_part4, self.h_part4, self.G_part5, self.h_part5
            )

            # Подготовка результатов
            result = {
                "Gi": [self.G_part1, self.G_part2, self.G_part3, self.G_part4, self.G_part5],
                "Pi_in": [self.P1, self.P2, self.P3, self.P4, self.P5],
                "Ti": [self.t_part1, self.t_part2, self.t_part3, self.t_part4, self.t_part5],
                "Hi": [self.h_part1, self.h_part2, self.h_part3, self.h_part4, self.h_part5],
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
        if self.len_part1 > 0:
            if self.len_part2 > 0:
                self.h_part1 = self.enthalpy_steam
                self.v_part1 = ph2v(self.P1, self.h_part1)
                self.t_part1 = ph2t(self.P1, self.h_part1)
                self.din_vis_part1 = ph(self.P1, self.h_part1, 24)
                self.G_part1 = part_props_detection(
                    self.P1, self.P2, self.v_part1, self.din_vis_part1,
                    self.len_part1, self.delta_clearance, self.S, self.KSI
                )

    def calculate_area2(self):
        """Выполняет расчеты для участка 2."""
        if self.len_part2 > 0:
            if self.len_part3 > 0:
                # Если есть ввод P_ejector, используем его, иначе используем значение по умолчанию
                if len(self.p_suctions) > 0:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[0])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                self.h_part2 = self.enthalpy_steam
                self.v_part2 = ph(self.P2, self.h_part2, 3)
                self.t_part2 = ph(self.P2, self.h_part2, 1)
                self.din_vis_part2 = ph(self.P2, self.h_part2, 24)
                self.G_part2 = part_props_detection(
                    self.P2, self.p_ejector, self.v_part2, self.din_vis_part2,
                    self.len_part2, self.delta_clearance, self.S, self.KSI
                )
            else:
                # Если len_part3 == 0
                if len(self.p_suctions) > 0:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[0])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                # Recalculate properties for part 1
                self.h_part1 = self.enthalpy_steam
                self.v_part1 = ph2v(self.P1, self.h_part1)
                self.t_part1 = ph2t(self.P1, self.h_part1)
                self.din_vis_part1 = ph(self.P1, self.h_part1, 24)
                self.G_part1 = part_props_detection(
                    self.P1, self.p_ejector, self.v_part1, self.din_vis_part1,
                    self.len_part1, self.delta_clearance, self.S, self.KSI
                )

                # Calculate properties for part 2
                self.h_part2 = self.h_air
                self.t_part2 = self.t_air
                self.v_part2 = air_calc(self.t_part2, 1)
                self.din_vis_part2 = air_calc(self.t_part2, 2)
                self.G_part2 = part_props_detection(
                    0.1013, self.p_ejector, self.v_part2, self.din_vis_part2,
                    self.len_part2, self.delta_clearance, self.S, self.KSI, last_part=True
                )

    def calculate_area3(self):
        """Выполняет расчеты для участка 3."""
        if self.len_part3 > 0:
            if self.len_part4 > 0:
                if len(self.p_suctions) > 1:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[1])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                self.h_part3 = self.enthalpy_steam
                self.v_part3 = ph(self.P3, self.h_part3, 3)
                self.t_part3 = ph(self.P3, self.h_part3, 1)
                self.din_vis_part3 = ph(self.P3, self.h_part3, 24)
                self.G_part3 = part_props_detection(
                    self.P3, self.p_ejector, self.v_part3, self.din_vis_part3,
                    self.len_part3, self.delta_clearance, self.S, self.KSI
                )
            else:
                # Если len_part4 == 0
                if len(self.p_suctions) > 1:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[1])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                self.h_part3 = self.h_air
                self.t_part3 = self.t_air
                self.v_part3 = air_calc(self.t_part3, 1)
                self.din_vis_part3 = air_calc(self.t_part3, 2)
                self.G_part3 = part_props_detection(
                    0.1013, self.p_ejector, self.v_part3, self.din_vis_part3,
                    self.len_part3, self.delta_clearance, self.S, self.KSI, last_part=True
                )

    def calculate_area4(self):
        """Выполняет расчеты для участка 4."""
        if self.len_part4 > 0:
            if self.len_part5 > 0:
                if len(self.p_suctions) > 2:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[2])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                self.h_part4 = self.enthalpy_steam
                self.v_part4 = ph(self.P4, self.h_part4, 3)
                self.t_part4 = ph(self.P4, self.h_part4, 1)
                self.din_vis_part4 = ph(self.P4, self.h_part4, 24)
                self.G_part4 = part_props_detection(
                    self.P4, self.p_ejector, self.v_part4, self.din_vis_part4,
                    self.len_part4, self.delta_clearance, self.S, self.KSI
                )
            else:
                # Если len_part5 == 0
                if len(self.p_suctions) > 2:
                    self.p_ejector = convert_pressure_to_mpa(self.p_suctions[2])
                else:
                    self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

                self.h_part4 = self.h_air
                self.t_part4 = self.t_air
                self.v_part4 = air_calc(self.t_part4, 1)
                self.din_vis_part4 = air_calc(self.t_part4, 2)
                self.G_part4 = part_props_detection(
                    0.1013, self.p_ejector, self.v_part4, self.din_vis_part4,
                    self.len_part4, self.delta_clearance, self.S, self.KSI, last_part=True
                )

    def calculate_area5(self):
        """Выполняет расчеты для участка 5."""
        if self.len_part5 > 0:
            if len(self.p_suctions) > 3:
                self.p_ejector = convert_pressure_to_mpa(self.p_suctions[3])
            else:
                self.p_ejector = convert_pressure_to_mpa(self.params.p_ejector_default, unit=5)

            self.h_part5 = self.h_air
            self.t_part5 = self.t_air
            self.v_part5 = air_calc(self.t_part5, 1)
            self.din_vis_part5 = air_calc(self.t_part5, 2)
            self.G_part5 = part_props_detection(
                0.1013, self.p_ejector, self.v_part5, self.din_vis_part5,
                self.len_part5, self.delta_clearance, self.S, self.KSI, last_part=True
            )

    def deaerator_options(self, p_deaerator: float, count_parts: int, count_valves: int,
                          h_part2: float, G_part1: float, G_part2: float,
                          G_part3: float, G_part4: float) -> Tuple[float, float, float, float]:
        """Рассчитывает параметры отсоса в деаэратор."""
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
            handle_error("Неверное количество секций клапана.")
        return g_deaerator, t_deaerator, p_deaerator, h_deaerator

    def ejector_options(self, p_ejector: float, count_parts: int, count_valves: int,
                        G_part2: float, h_part2: float, G_part3: float, h_part3: float,
                        G_part4: float = 0.0, h_part4: float = 0.0, G_part5: float = 0.0,
                        h_part5: float = 0.0) -> Tuple[float, float, float, float]:
        """Рассчитывает параметры отсоса в эжектор уплотнений."""
        if count_parts == 2:
            g_ejector = G_part2 * count_valves
            h_ejector = h_part2
            t_ejector = ph(p_ejector, h_ejector, 1)
        elif count_parts == 3:
            g_ejector = (G_part2 + G_part3) * count_valves
            h_ejector = (h_part2 * G_part2 + h_part3 * G_part3) / (G_part2 + G_part3)
            t_ejector = ph(p_ejector, h_ejector, 1)
        elif count_parts == 4:
            g_first_suction = (G_part2 - G_part3 - G_part4) * count_valves
            g_second_suction = abs(G_part3 - G_part4) * count_valves
            h_second_suction = (h_part4 * G_part4 + h_part3 * G_part3) / (G_part4 + G_part3)
            g_ejector = g_first_suction + g_second_suction
            h_ejector = (g_second_suction * h_second_suction + g_first_suction * h_part2) / (
                        g_second_suction + g_first_suction)
            t_ejector = ph(p_ejector, h_ejector, 1)
        elif count_parts == 5:
            g_first_suction = G_part2 - G_part3 - G_part4
            g_second_suction = abs(G_part3 - G_part4)
            g_third_suction = G_part4 + G_part5
            h_third_suction = (h_part5 * G_part5 + h_part4 * G_part4) / (G_part5 + G_part4)
            g_ejector = (g_first_suction + g_second_suction + g_third_suction) * count_valves
            h_ejector = ((g_third_suction * h_third_suction + g_second_suction * h_part2 +
                          g_first_suction * h_part2) / (g_third_suction + g_second_suction + g_first_suction))
            t_ejector = ph(p_ejector, h_ejector, 1)
        else:
            handle_error("Неверное количество секций клапана.")
        return g_ejector, t_ejector, p_ejector, h_ejector

    def get_p_ejector_final(self) -> float:
        """Получает окончательное значение давления эжектора."""
        # Здесь можно определить логику получения конечного значения p_ejector
        return self.p_ejector  # Пример; возможно, нужна дополнительная логика
