from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.turbine import TurbineParameters
from backend.services.calculations import calculate_efficiency

router = APIRouter()

# @router.post("/calculate/")
# def calculate_turbine_properties(parameters: TurbineParameters):
#     try:
#         efficiency = calculate_efficiency(parameters)
#         return {"efficiency": efficiency}
#     except ZeroDivisionError:
#         raise HTTPException(status_code=400, detail="Flow rate must not be zero.")

# Тестовый GET эндпоинт
@router.get("/test-get")
def test_get():
    return {"message": "This is a test GET endpoint"}

# Модель для тестового POST эндпоинта
class TestData(BaseModel):
    name: str
    value: int

# Тестовый POST эндпоинт
@router.post("/test-post")
def test_post(data: TestData):
    return {"message": f"Received data with name: {data.name} and value: {data.value}"}