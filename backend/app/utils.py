import logging
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


from math import pi
from typing import List, Dict, Optional
from .schemas import CalculationParams, CalculationResult, ValveInfo, TurbineInfo
from . import database
from .models import Valve, Turbine
from seuif97 import *  # Убедитесь, что эти библиотеки установлены и работают корректно
from WSAProperties import air_calc, ksi_calc, lambda_calc  # Также установите эти зависимости


def perform_all_calculations(params: CalculationParams, valve_data: Dict) -> CalculationResult:
    """
    Выполняет все необходимые расчёты на основе предоставленных параметров и данных о клапане.

    Args:
        params (CalculationParams): Параметры расчёта.
        valve_data (Dict): Данные о клапане.

    Returns:
        CalculationResult: Результаты расчётов.
    """
    try:
        # Извлечение необходимых данных из valve_data
        radius_rounding_DB = valve_data.get("rounding_radius")
        delta_clearance_DB = valve_data.get("calculated_gap")
        diameter_stock_DB = valve_data.get("rod_diameter")
        section_lengths_DB = valve_data.get("section_lengths", [])
        enthalpy_steam = pt2h(params.p_values[0], params.temperature_start)  # Пример использования seuif97

        # Конвертация данных
        radius_rounding = convert_to_meters(radius_rounding_DB, "радиусе скругления")
        delta_clearance = convert_to_meters(delta_clearance_DB, "зазоре")
        diameter_stock = convert_to_meters(diameter_stock_DB, "диаметре штока")
        len_parts = [convert_to_meters(length, f"участке {i + 1}") for i, length in enumerate(section_lengths_DB) if
                     length is not None]

        # Подсчет количества непустых участков
        count_parts = len(len_parts)

        # Конвертация давлений (предполагаем, что p_values содержит P1-P5)
        P_values = convert_pressures(params.p_values)
        P1, P2, P3, P4, P5 = P_values
        p_deaerator = P2

        # Конвертация давления для эжектора, если необходимо
        p_ejector = params.p_ejector if params.p_ejector is not None else P5  # Если p_ejector не предоставлено, берем P5

        # Конвертация коэффициента пропорциональности и площади зазора
        proportional_coef = radius_rounding / (delta_clearance * 2)  # Коэффициент пропорциональности
        S = delta_clearance * pi * diameter_stock  # Площадь зазора

        # Расчет коэффициента KSI
        KSI = ksi_calc(proportional_coef)

        # Инициализация переменных для расчетов
        Gi = [0.0] * 5
        Pi_in = [P1, P2, P3, P4, P5]
        Ti = [0.0] * 5
        Hi = [0.0] * 5

        # **Пример бизнес-логики расчётов**
        # Здесь вы должны реализовать всю вашу логику расчётов, исходя из вашего консольного приложения.
        # Для демонстрации, я добавлю примерные расчёты. Замените их на ваши реальные расчёты.

        # Пример расчёта Gi
        Gi = [calculate_Gi(part_length, proportional_coef, KSI, P, S) for part_length, P in zip(len_parts, P_values)]

        # Пример расчёта Ti и Hi
        Ti = [calculate_Ti(P) for P in Pi_in]
        Hi = [calculate_Hi(T) for T in Ti]

        # Пример расчёта deaerator_props и ejector_props
        deaerator_props = calculate_deaerator(p_deaerator, len_parts, Gi, params.count_valves)
        ejector_props = calculate_ejector(p_ejector, len_parts, Gi, params.count_valves)

        # Создание объекта CalculationResult
        calculation_result = CalculationResult(
            Gi=Gi,
            Pi_in=Pi_in,
            Ti=Ti,
            Hi=Hi,
            deaerator_props=deaerator_props,
            ejector_props=ejector_props
        )

        return calculation_result

    except IndexError as ie:
        raise ValueError(f"Некорректные данные в чертежах: {ie}")
    except Exception as e:
        raise e


def convert_to_meters(value: Optional[float], description: str) -> float:
    """
    Конвертирует значение в метры.

    Args:
        value (Optional[float]): Значение для конвертации.
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


def convert_pressures(p_values: List[float]) -> List[float]:
    """
    Конвертирует список давлений в МПа.

    Args:
        p_values (List[float]): Список давлений (P1-P5).

    Returns:
        List[float]: Список давлений в МПа.
    """
    conversion_factors = {
        1: 1e-6,  # Паскаль в МПа
        2: 1e-3,  # кПа в МПа
        3: 0.0980665,  # кгс/см² в МПа
        4: 0.101325,  # техническая атмосфера в МПа
        5: 0.1,  # бар в МПа
        6: 0.101325  # физическая атмосфера в МПа
    }
    # Для примера, считаем все давления в барах (единица 5)
    conversion_unit = 5  # Бар
    return [p * conversion_factors[conversion_unit] for p in p_values]


# **Примеры реализаций функций расчётов**
# Замените их на ваши реальные вычисления.

def calculate_Gi(part_length: float, proportional_coef: float, KSI: float, P: float, S: float) -> float:
    # Примерное вычисление Gi
    # Замените на вашу формулу расчёта G
    G = proportional_coef * KSI * P * part_length * S
    return G


def calculate_Ti(P: float) -> float:
    # Примерное вычисление Ti на основе давления
    # Замените на вашу формулу
    T = P * 10  # Например
    return T


def calculate_Hi(T: float) -> float:
    # Примерное вычисление Hi на основе температуры
    # Замените на вашу формулу
    H = T * 1.5  # Например
    return H


def calculate_deaerator(p_deaerator: float, len_parts: List[float], Gi: List[float], count_valves: int) -> List[float]:
    # Пример расчёта параметров деаэратора
    # Замените на вашу логику
    g_deaerator = sum(Gi) * count_valves * 0.1
    t_deaerator = sum(len_parts) * 0.05
    h_deaerator = p_deaerator * 0.01
    return [g_deaerator, t_deaerator, p_deaerator, h_deaerator]


def calculate_ejector(p_ejector: float, len_parts: List[float], Gi: List[float], count_valves: int) -> List[float]:
    # Пример расчёта параметров эжектора
    # Замените на вашу логику
    g_ejector = sum(Gi) * count_valves * 0.2
    t_ejector = sum(len_parts) * 0.06
    h_ejector = p_ejector * 0.02
    return [g_ejector, t_ejector, p_ejector, h_ejector]