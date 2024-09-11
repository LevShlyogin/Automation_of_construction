from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from CalculationValveRods.Stocks.StockRazchetsKlapans import *

router = APIRouter()

@router.get("/turbine/{turbine_id}")
async def get_turbine(turbine_id: int):
    # db: Session = Depends(get_db)
    # turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
    # if not turbine:
    #     raise HTTPException(status_code=404, detail="Турбина не найдена")
    # return turbine
    return "TURBINE_TEMPLATE_ACCEPT"

@router.get("/turbine/{turbine_id}/shaft/{shaft_id}")
async def get_shaft(turbine_id: int, shaft_id: int):
    # db: Session = Depends(get_db)
    # shaft = db.query(Shaft).filter(Shaft.id == shaft_id, Shaft.turbine_id == turbine_id).first()
    # if not shaft:
    #     raise HTTPException(status_code=404, detail="Шток не найден")
    # return shaft
    return "STOCK_TEMPLATE_ACCEPT"


class TurbineUpdate(BaseModel):
    power: float | None = None
    efficiency: float | None = None
    # другие параметры...


@router.post("/turbine/{turbine_id}/input")
async def update_turbine_data(turbine_id: int, data: TurbineUpdate):
    # db: Session = Depends(get_db)
    # turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
    # if not turbine:
    #     raise HTTPException(status_code=404, detail="Турбина не найдена")
    #
    # if data.power:
    #     turbine.power = data.power
    # if data.efficiency:
    #     turbine.efficiency = data.efficiency
    # # обновить другие поля...
    #
    # db.commit()
    # return turbine
    return "DATA_TURBINE_INPUT_ACCEPT"


@router.post("/turbine/{turbine_id}/calculate")
async def calculate_turbine(turbine_id: int):
    # db: Session = Depends(get_db)
    # turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
    # if not turbine:
    #     raise HTTPException(status_code=404, detail="Турбина не найдена")
    #
    # # Пример вызова функции расчета
    # results = calculate_turbine_params(turbine)
    return "ACCEPT_CALCULATE_TURBINE_PARAMS"

    # return {
    #     "Gi": results.Gi,
    #     "Pi_in": results.Pi_in,
    #     "Ti": results.Ti,
    #     "Hi": results.Hi,
    #     "deaerator_props": results.deaerator_props,
    #     "ejector_props": results.ejector_props
    # }