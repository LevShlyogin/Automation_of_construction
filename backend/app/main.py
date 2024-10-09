import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from backend.app.api.main import api_router
from backend.app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# main.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas, crud
from .database import SessionLocal, engine
from .utils import perform_all_calculations, CalculationError
from .dependencies import get_db
from fastapi import FastAPI

# Создание всех таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Valve Calculation API")

@app.post("/calculate", response_model=schemas.CalculationResult)
def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
    # Выбор клапана на основе предоставленных параметров
    valve_info: Optional[schemas.ValveInfo] = None

    if params.valve_id:
        valve_info = crud.get_valve_by_id(db, valve_id=params.valve_id)
        if valve_info is None:
            raise HTTPException(status_code=404, detail="Клапан не найден по указанному ID.")
    elif params.valve_drawing:
        valve_info = crud.get_valve_by_drawing(db, valve_drawing=params.valve_drawing)
        if valve_info is None:
            raise HTTPException(status_code=404, detail="Клапан не найден по указанному чертежу.")
    elif params.turbine_name:
        turbine_valves = crud.get_valves_by_turbine(db, turbin_name=params.turbine_name)
        if not turbine_valves or turbine_valves.count == 0:
            raise HTTPException(status_code=404, detail="Турбина или связанные клапаны не найдены.")
        if params.count_valves > turbine_valves.count:
            raise HTTPException(status_code=400,
                                detail=f"Количество клапанов ({params.count_valves}) превышает доступное ({turbine_valves.count}).")
        # Выбираем первый клапан или добавьте логику выбора
        valve_info = turbine_valves.valves[0]
    else:
        raise HTTPException(status_code=400, detail="Необходимо указать valve_id, valve_drawing или turbine_name.")

    try:
        # Выполнение расчетов
        calculation_result = perform_all_calculations(params, valve_info)
    except CalculationError as ce:
        raise HTTPException(status_code=400, detail=ce.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при выполнении расчетов.")

    # Преобразование результата в Pydantic схему
    return schemas.CalculationResult(**calculation_result)