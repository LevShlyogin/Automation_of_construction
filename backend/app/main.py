import sentry_sdk
from docutils.nodes import status
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
from typing import List
from . import models, schemas, crud
from .database import engine
from .utils import ValveCalculator, CalculationError
from .dependencies import get_db
from fastapi import FastAPI

app = FastAPI(title="Valve Calculation API")


@app.get("/turbines/test/")
def test_turbine_endpoint():
    return {"message": "Тестовый эндпоинт для турбин работает!"}


@app.get("/turbines/", response_model=List[schemas.TurbineInfo])
def get_all_turbines(db: Session = Depends(get_db)):
    turbines = db.query(models.Turbine).all()
    turbine_infos = [
        schemas.TurbineInfo(
            id=turbine.id,
            turbin_name=turbine.turbin_name
        ) for turbine in turbines
    ]
    return turbine_infos


@app.get("/turbines/{turbine_name}/valves/", response_model=schemas.TurbineValves)
def get_valves_by_turbine_endpoint(turbine_name: str, db: Session = Depends(get_db)):
    turbine_valves = crud.get_valves_by_turbine(db, turbin_name=turbine_name)
    if turbine_valves is None:
        raise HTTPException(status_code=404, detail="Турбина не найдена.")
    return turbine_valves


@app.post("/calculate", response_model=schemas.CalculationResultDB)
def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):

    # Выбор клапана по ID или по чертежу
    if params.valve_id:
        valve_info = crud.get_valve_by_id(db, valve_id=params.valve_id)
        if valve_info is None:
            raise HTTPException(status_code=404, detail="Клапан не найден по указанному ID.")
    elif params.valve_drawing:
        valve_info = crud.get_valve_by_drawing(db, valve_drawing=params.valve_drawing)
        if valve_info is None:
            raise HTTPException(status_code=404, detail="Клапан не найден по указанному чертежу.")
    else:
        raise HTTPException(status_code=400, detail="Необходимо указать valve_id или valve_drawing.")

    valve_drawing = valve_info.valve_drawing

    # Проверка на существующие результаты для данного чертежа
    existing_results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_drawing)
    if existing_results and len(existing_results) > 0:
        latest_result = existing_results[0]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Для данного чертежа клапана уже существуют сохранённые результаты. Вы можете просмотреть их.",
                "latest_result": latest_result.results,
                "date": latest_result.date
            }
        )

    try:
        # Выполнение расчётов
        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()
    except CalculationError as ce:
        raise HTTPException(status_code=400, detail=ce.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при выполнении расчётов.")

    # Сохранение результатов в базе данных
    new_result = crud.create_calculation_result(
        db=db,
        valve_drawing=valve_drawing,
        parameters=params,
        results=calculation_result
    )

    # Преобразование словаря в объект схемы
    return schemas.CalculationResultDB(
        id=new_result.id,
        date=new_result.date,
        valve_drawing=new_result.valve_drawing,
        parameters=params,
        results=calculation_result
    )


@app.get("/valves/{valve_drawing}/results/", response_model=List[schemas.CalculationResultDB])
def get_calculation_results(valve_drawing: str, db: Session = Depends(get_db)):
    """
    Получает все результаты расчётов для заданного чертежа клапана.
    """
    results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_drawing)
    if not results:
        raise HTTPException(status_code=404, detail="Расчёты для данного чертежа клапана не найдены.")

    # Преобразование результатов в Pydantic схемы
    calculation_results = [
        schemas.CalculationResultDB(
            id=result.id,
            date=result.date,
            valve_drawing=result.valve_drawing,
            parameters=result.parameters,
            results=result.results
        ) for result in results
    ]

    return calculation_results