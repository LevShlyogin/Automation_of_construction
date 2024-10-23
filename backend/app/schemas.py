from typing import List, Optional, Dict

from pydantic import BaseModel
from datetime import datetime

class TurbineInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ValveInfo(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    diameter: Optional[float] = None
    clearance: Optional[float] = None
    count_parts: Optional[int] = None
    section_lengths: List[Optional[float]]  # Список длин частей
    round_radius: Optional[float] = None
    turbine: Optional[TurbineInfo] = None  # Включение информации о турбине

    class Config:
        from_attributes = True


class CalculationParams(BaseModel):
    turbine_name: Optional[str] = None  # Сделаем необязательным
    valve_drawing: Optional[str] = None  # Добавим возможность ввода чертежа клапана
    valve_id: Optional[int] = None  # ID клапана (если введено)
    temperature_start: float
    t_air: float
    count_valves: int
    p_ejector: List[float]  # Параметр для давления в эжекторе
    p_values: List[float]  # Список давлений P1-P5



class CalculationResult(BaseModel):
    Gi: List[float]
    Pi_in: List[float]
    Ti: List[float]
    Hi: List[float]
    deaerator_props: List[float]
    ejector_props: List[Dict[str, float]]


class TurbineValves(BaseModel):
    count: int
    valves: List[ValveInfo]

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    error: bool
    message: str
    detail: Optional[str] = None


class CalculationResultDB(BaseModel):
    id: int
    date: datetime
    valve_drawing: str
    parameters: CalculationParams
    results: CalculationResult

    class Config:
        from_attributes = True