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
from typing import List
from backend.app import models, schemas, crud
from backend.app.utils import ValveCalculator, CalculationError
from backend.app.dependencies import get_db
from fastapi import FastAPI

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Valve Calculation API")


@app.get("/turbines/", response_model=List[schemas.TurbineInfo])
async def get_all_turbines(db: Session = Depends(get_db)):
    turbines = db.query(models.Turbine).all()
    turbine_infos = [
        schemas.TurbineInfo(
            id=turbine.id,
            name=turbine.name
        ) for turbine in turbines
    ]
    return turbine_infos


@app.get("/turbines/{turbine_name}/valves/", response_model=schemas.TurbineValves)
async def get_valves_by_turbine(turbine_name: str, db: Session = Depends(get_db)):
    try:
        turbine_valves = crud.get_valves_by_turbine(db, turbine_name=turbine_name)
        if turbine_valves is None:
            raise HTTPException(
                status_code=404,
                detail=f"Турбина с именем {turbine_name} не найдена или у неё нет клапанов"
            )
        return turbine_valves
    except Exception as e:
        logger.error(f"Error getting valves for turbine {turbine_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post("/calculate", response_model=schemas.CalculationResultDB)
async def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
    valve_info = params.valve_info  # Используем данные о клапане, переданные с фронтенда

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
        valve_drawing=valve_info.name,  # Используем переданные данные о клапане
        parameters=params,
        results=calculation_result
    )

    # Возвращаем результат
    return schemas.CalculationResultDB(
        id=new_result.id,
        date=new_result.date,
        valve_drawing=valve_info.name,  # Используем переданные данные о клапане
        parameters=params,
        results=calculation_result
    )


@app.get("/valves/{valve_name}/results/", response_model=List[schemas.CalculationResultDB])
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    """
    Получает все результаты расчётов для заданного клапана по его имени.
    """
    results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_name)

    if not results:
        return []  # Возвращаем пустой список, если результаты не найдены

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