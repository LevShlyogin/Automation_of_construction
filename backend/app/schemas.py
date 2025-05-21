from typing import List, Optional, Dict, Any

from pydantic import BaseModel, computed_field
from datetime import datetime

class TurbineInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ValveInfo(BaseModel):
    id: Optional[int] = None  # Сделать опциональным
    name: Optional[str] = None
    type: Optional[str] = None
    diameter: Optional[float] = None
    clearance: Optional[float] = None
    count_parts: Optional[int] = None
    len_part1: Optional[float] = None
    len_part2: Optional[float] = None
    len_part3: Optional[float] = None
    len_part4: Optional[float] = None
    len_part5: Optional[float] = None
    round_radius: Optional[float] = None

    @computed_field
    @property
    def section_lengths(self) -> List[Optional[float]]:
        return [
            self.len_part1,
            self.len_part2,
            self.len_part3,
            self.len_part4,
            self.len_part5
        ]

    class Config:
        from_attributes = True


class ValveCreate(BaseModel):
    name: str
    type: Optional[str]
    diameter: Optional[float]
    clearance: Optional[float]
    count_parts: Optional[int]
    len_part1: Optional[float]
    len_part2: Optional[float]
    len_part3: Optional[float]
    len_part4: Optional[float]
    len_part5: Optional[float]
    round_radius: Optional[float]
    turbine_id: Optional[int]


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
    user_name: Optional[str] = None
    stock_name: str
    turbine_name: str
    calc_timestamp: datetime
    input_data: dict[str, Any]  # Замените JSON на Dict[str, Any]
    output_data: dict[str, Any]

    class Config:
            from_attributes = True