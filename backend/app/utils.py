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


from math import *
from seuif97 import *  # Убедитесь, что эти библиотеки доступны в вашем окружении
from WSAProperties import air_calc, ksi_calc, lambda_calc  # Убедитесь, что эти модули доступны
from typing import Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalculationError(Exception):
    """Кастомное исключение для ошибок расчетов."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def handle_error(error_text: str):
    """
    Обрабатывает ошибки, выбрасывая исключение.

    Args:
        error_text (str): Текст ошибки.

    Raises:
        CalculationError: Если возникает ошибка.
    """
    if "Нет данных о" in error_text:
        raise CalculationError(error_text)
    else:
        raise CalculationError(error_text)

def convert_to_meters(value: float, description: str) -> float:
    """
    Конвертирует значение в метры.

    Args:
        value (float): Значение для конвертации.
        description (str): Описание значения для ошибок.

    Returns:
        float: Значение в метрах.

    Raises:
        ValueError: Если значение отсутствует.
    """
    if value is not None:
        return float(value) / 1000
    else:
        raise ValueError(f"Нет данных о {description}")

def calculate_enthalpy_for_air(t_air: float) -> float:
    """
    Рассчитывает энтальпию для воздуха на основе температуры.

    Args:
        t_air (float): Температура воздуха (в градусах Цельсия).

    Returns:
        float: Энтальпия воздуха.
    """
    return t_air * 1.006  # Энтальпия воздуха (кДж/кг)

def convert_pressure_to_mpa(pressure, unit=5):
    """
    Преобразует давление в МПа из различных единиц измерения.

    Args:
        pressure (float): Значение давления.
        unit (int): Единица измерения (по умолчанию бар = 5).

    Returns:
        float: Давление в МПа.
    """
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

# Вспомогательная функция для нахождения G пара или воздуха для последней части
def G_find(last_part, ALFA, P_first, P_second, v, S):
    """
    Вычисляет значение G в зависимости от типа среды (пар или воздух)
    и входных параметров.

    Args:
        last_part (bool): Флаг, указывающий, является ли текущий участок последним.
        ALFA (float): Коэффициент, зависящий от числа Рейнольдса и геометрии.
        P_first (float): Давление в начале участка (в Паскалях).
        P_second (float): Давление в конце участка (в Паскалях).
        v (float): Скорость потока (в м/с).
        S (float): Площадь зазора.

    Returns:
        float: Значение G.
    """

    G = ALFA * S * math.sqrt((P_first ** 2 - P_second ** 2) / (P_first * v)) * 3.6
    if last_part:
        G = max(0.001, G)  # Для последнего участка G не может быть меньше 0.001
    return G

# Функция для определения параметров участка
def part_props_detection(P_first, P_second, v, din_vis, len_part, delta_clearance, S, KSI, last_part=False, W_min=1, W_max=1000):
    """
    Определяет параметры пара/воздуха участка с использованием бинарного поиска.

    Args:
        P_first (float): Давление в начале участка (в бар).
        P_second (float): Давление в конце участка (в бар).
        v (float): Удельный объём (в м^3/кг).
        din_vis (float): Кинематическая вязкость (в м^2/с).
        len_part (float): Длина участка (в м).
        delta_clearance (float): Зазор.
        S (float): Площадь зазора.
        KSI (float): Коэффициент KSI.
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
    kin_vis = v * din_vis  # Кинематическая вязкость

    while W_max - W_min > 0.001:  # Цикл бинарного поиска
        W_mid = (W_min + W_max) / 2  # Вычисление середины диапазона
        Re = (W_mid * 2 * delta_clearance) / kin_vis  # Вычисление числа Рейнольдса
        ALFA = 1 / math.sqrt(1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance)  # Вычисление ALFA
        G = G_find(last_part, ALFA, P_first, P_second, v, S)  # Вычисление G
        delta_speed = W_mid - v * G / (3.6 * S)  # Вычисление разности скоростей

        if delta_speed > 0:
            W_max = W_mid  # Сужение диапазона поиска
        else:
            W_min = W_mid  # Сужение диапазона поиска

    W_result = (W_min + W_max) / 2  # Получение приближенного значения W
    Re = (W_result * 2 * delta_clearance) / kin_vis  # Вычисление числа Рейнольдса
    ALFA = 1 / math.sqrt(1 + KSI + (0.5 * lambda_calc(Re) * len_part) / delta_clearance)  # Вычисление ALFA
    G = G_find(last_part, ALFA, P_first, P_second, v, S)  # Итоговое вычисление G
    return G

# Пример функции для расчёта параметров отсоса в деаэратор
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
        Tuple[float, float, float, float]: Расход, температура, давление и энтальпия в деаэраторе.
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
        raise handle_error("Неверное количество секций клапана.")
    return g_deaerator, t_deaerator, p_deaerator, h_deaerator

def ejector_options(p_ejector: float, count_parts: int, count_valves: int, G_part2: float, h_part2: float,
                    G_part3: float, h_part3: float, G_part4=0.0, h_part4=0.0, G_part5=0.0, h_part5=0.0) -> Tuple[float, float, float, float]:
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
        Tuple[float, float, float, float]: Расход, температура, давление и энтальпия в эжекторе.
    """
    g_ejector, t_ejector, h_ejector = 0.0, 0.0, 0.0
    if count_parts == 2:
        g_ejector = (G_part2 * count_valves)
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
        h_ejector = (g_second_suction * h_second_suction + g_first_suction * h_part2) / (g_second_suction + g_first_suction)
        t_ejector = ph(p_ejector, h_ejector, 1)
    elif count_parts == 5:
        g_first_suction = G_part2 - G_part3 - G_part4
        g_second_suction = abs(G_part3 - G_part4)
        g_third_suction = G_part4 + G_part5
        h_third_suction = (h_part5 * G_part5 + h_part4 * G_part4) / (G_part5 + G_part4)
        g_ejector = (g_first_suction + g_second_suction + g_third_suction) * count_valves
        h_ejector = ((g_third_suction * h_third_suction + g_second_suction * h_part2 + g_first_suction * h_part2)
                     / (g_third_suction + g_second_suction + g_first_suction))
        t_ejector = ph(p_ejector, h_ejector, 1)
    else:
        raise handle_error("Неверное количество секций клапана.")
    return g_ejector, t_ejector, p_ejector, h_ejector

def perform_all_calculations(params, valve_info):
    try:
        # Извлечение необходимых данных из params и valve_info
        temperature_start_DB = params.temperature_start
        t_air = params.t_air
        h_air = calculate_enthalpy_for_air(t_air)
        count_valves = params.count_valves
        radius_rounding_DB = valve_info['rounding_radius']
        delta_clearance_DB = valve_info['calculated_gap']
        diameter_stock_DB = valve_info['rod_diameter']
        len_parts_DB = valve_info['section_lengths']

        # Конвертация измерений в метры
        radius_rounding = convert_to_meters(radius_rounding_DB, "радиус скругления")
        delta_clearance = convert_to_meters(delta_clearance_DB, "зазор")
        diameter_stock = convert_to_meters(diameter_stock_DB, "диаметр штока")
        len_parts = [convert_to_meters(length, f"участок {i+1}") for i, length in enumerate(len_parts_DB) if length is not None]

        # Подсчет количества непустых участков
        count_parts = len(len_parts)

        # Извлечение значений давления
        P_values = params.p_values
        P1, P2, P3, P4, P5 = P_values
        p_deaerator = P2

        # Извлечение длины участков
        len_part1, len_part2, len_part3, len_part4, len_part5 = len_parts + [0] * (5 - len(len_parts))  # Заполняем нулями

        # Расчет коэффициента пропорциональности
        proportional_coef = radius_rounding / (delta_clearance * 2)
        S = delta_clearance * pi * diameter_stock
        enthalpy_steam = pt2h(P1, temperature_start_DB)
        KSI = ksi_calc(proportional_coef)

        # Инициализация переменных
        G_part1 = G_part2 = G_part3 = G_part4 = G_part5 = 0.0
        t_part1 = t_part2 = t_part3 = t_part4 = t_part5 = 0.0
        h_part1 = h_part2 = h_part3 = h_part4 = h_part5 = 0.0

        # Расчеты для каждого участка
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

            # Вычисление параметров отсоса в деаэратор и эжектор
            g_deaerator, t_deaerator, p_deaerator, h_deaerator = deaerator_options(
                p_deaerator, count_parts, count_valves, h_part2, G_part1, G_part2, G_part3, G_part4
            )
            g_ejector, t_ejector, p_ejector, h_ejector = ejector_options(
                p_ejector, count_parts, count_valves, G_part2, h_part2, G_part3, h_part3, G_part4, h_part4, G_part5,
                h_part5
            )

            # Подготовка результатов
            result = {
                "Gi": [G_part1, G_part2, G_part3, G_part4, G_part5],
                "Pi_in": [P1, P2, P3, P4, P5],
                "Ti": [t_part1, t_part2, t_part3, t_part4, t_part5],
                "Hi": [h_part1, h_part2, h_part3, h_part4, h_part5],
                "deaerator_props": [g_deaerator, t_deaerator, p_deaerator, h_deaerator],
                "ejector_props": [g_ejector, t_ejector, p_ejector, h_ejector]
        }
        return result

    except Exception as e:
        raise ValueError(f"Ошибка в расчётах: {str(e)}")