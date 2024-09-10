from fastapi import APIRouter, HTTPException
from backend.models.turbine import TurbineParameters
from backend.services.calculations import calculate_efficiency

router = APIRouter()

@router.post("/calculate/")
def calculate_turbine_properties(parameters: TurbineParameters):
    try:
        efficiency = calculate_efficiency(parameters)
        return {"efficiency": efficiency}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Flow rate must not be zero.")