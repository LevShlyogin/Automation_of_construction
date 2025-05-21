import json, logging
from sqlalchemy.orm import Session
from backend.app.celery_app import celery_app
from backend.app import crud, schemas, deps
from backend.app.services.valve_calc import ValveCalculator, CalculationError

log = logging.getLogger(__name__)

@celery_app.task(name="backend.app.tasks.calc_rod", bind=True, acks_late=True)
def calc_rod(self, payload: dict) -> dict:
    """
    Асинхронный расчёт штока клапана.
    payload:
      valve_drawing: str
      params: {...}  # CalculationParams json
      user_name: str
    """
    db: Session = deps.SessionLocal()
    try:
        params = schemas.CalculationParams.model_validate(payload["params"])
        valve   = crud.get_valve_by_name(db, params.valve_drawing)
        if not valve:
            raise ValueError(f"Valve {params.valve_drawing} not found")

        vc = ValveCalculator(params, schemas.ValveInfo.model_validate(valve))
        res_dict = vc.perform_calculations()

        db_obj = crud.create_calculation_result(
            db=db,
            parameters=params,
            results=res_dict,
            valve_id=valve.id,
            user_name=payload.get("user_name", "system"),
        )
        db.commit()

        # можно сюда же грузить CSV/PDF в MinIO, возвращая URL
        return {
            "status": "SUCCEED",
            "result_id": db_obj.id,
            "output": res_dict,
        }

    except CalculationError as ce:
        log.exception("Business error")
        self.update_state(state="FAILURE", meta={"exc": ce.message})
        raise
    except Exception as e:
        log.exception("Unhandled")
        self.update_state(state="FAILURE", meta={"exc": str(e)})
        raise
    finally:
        db.close() 