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

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas, crud
from .database import SessionLocal, engine
from .utils import perform_all_calculations

# Создание всех таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Valve Calculation API")


# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/turbines/{turbin_name}/valves", response_model=schemas.TurbineValves)
def read_valves_by_turbine(turbin_name: str, db: Session = Depends(get_db)):
    turbine_valves = crud.get_valves_by_turbine(db, turbin_name=turbin_name)
    if not turbine_valves or turbine_valves.count == 0:
        raise HTTPException(status_code=404, detail="Турбина или связанные клапаны не найдены.")
    return turbine_valves


@app.get("/valves/drawing/{valve_drawing}", response_model=schemas.ValveInfo)
def read_valve_by_drawing(valve_drawing: str, db: Session = Depends(get_db)):
    valve_info = crud.get_valve_by_drawing(db, valve_drawing=valve_drawing)
    if valve_info is None:
        raise HTTPException(status_code=404, detail="Клапан с указанным чертежом не найден.")
    return valve_info


@app.get("/valves/{valve_id}", response_model=schemas.ValveInfo)
def read_valve_by_id(valve_id: int, db: Session = Depends(get_db)):
    valve_info = crud.get_valve_by_id(db, valve_id=valve_id)
    if valve_info is None:
        raise HTTPException(status_code=404, detail="Клапан не найден.")
    return valve_info


@app.post("/calculate", response_model=schemas.CalculationResult)
def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
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
        # Для примера выбираем первый клапан (можете добавить логику выбора)
        valve_info = turbine_valves.valves[0]
    else:
        raise HTTPException(status_code=400, detail="Необходимо указать valve_id, valve_drawing или turbine_name.")

    # Выполнение расчётов
    try:
        calculation_result = perform_all_calculations(params, valve_info.dict())
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при выполнении расчетов.")

    return calculation_result