from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.schemas import CalculationParams, CalculationResultDB
from backend.app.dependencies import get_db
from backend.app.crud import create_calculation_result, get_valve_by_name
from backend.app.services.valve_calc import ValveCalculator, CalculationError
from backend.app.tasks import calc_rod

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.post("/", response_model=CalculationResultDB, summary="Sync расчёт")
async def calculate(params: CalculationParams, db: Session = Depends(get_db)):
    try:
        valve = get_valve_by_name(db, params.valve_drawing)
        if not valve:
            raise HTTPException(status_code=404, detail=f"Valve {params.valve_drawing} not found")
        vc = ValveCalculator(params, valve)
        res_dict = vc.perform_calculations()
        db_obj = create_calculation_result(
            db=db,
            parameters=params,
            results=res_dict,
            valve_id=valve.id,
            user_name="system",
        )
        db.commit()
        return db_obj
    except CalculationError as ce:
        raise HTTPException(status_code=400, detail=ce.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/async", status_code=202, summary="Async расчёт (Celery)")
async def calculate_async(params: CalculationParams):
    job = calc_rod.apply_async(kwargs={
        "payload": {
            "valve_drawing": params.valve_drawing,
            "params": params.model_dump(),
        }
    })
    return {"job_id": job.id} 