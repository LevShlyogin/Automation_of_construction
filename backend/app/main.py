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
from typing import Optional, List
from . import models, schemas, crud
from .database import engine
from .utils import ValveCalculator, CalculationError
from .dependencies import get_db
from fastapi import FastAPI

# Создание всех таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Valve Calculation API")


@app.post("/calculate", response_model=schemas.CalculationResultDB)
def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
    # Логика выбора клапана остается прежней

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

    valve_drawing = valve_info.valve_drawing

    # Проверяем наличие уже существующих результатов для данного чертежа клапана
    existing_results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_drawing)
    if existing_results and len(existing_results) > 0:
        # Возвращаем информацию о существующих результатах и сообщаем пользователю
        latest_result = existing_results[0]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # Конфликт, так как данные уже существуют
            detail={
                "message": "Для данного чертежа клапана уже существуют сохранённые результаты. Вы можете просмотреть их.",
                "latest_result": latest_result.results,
                "date": latest_result.date
            }
        )

    try:
        # Выполнение расчетов
        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()
    except CalculationError as ce:
        raise HTTPException(status_code=400, detail=ce.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при выполнении расчетов.")

    # Сохранение результатов в таблице "Results"
    new_result = crud.create_calculation_result(db=db,
                                                valve_drawing=valve_drawing,
                                                parameters=params,
                                                results=calculation_result)

    # Возвращение нового результата вместе с датой
    return schemas.CalculationResultDB(
        id=new_result.id,
        date=new_result.date,
        valve_drawing=new_result.valve_drawing,
        parameters=params,
        results=calculation_result
    )


@app.get("/results/{valve_drawing}", response_model=List[schemas.CalculationResultDB])
def get_results(valve_drawing: str, db: Session = Depends(get_db)):
    results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_drawing)
    if not results:
        raise HTTPException(status_code=404, detail="Результаты для данного чертежа не найдены.")

    # Преобразуем SQLAlchemy модели в Pydantic схемы
    return [
        schemas.CalculationResultDB(
            id=result.id,
            date=result.date,
            valve_drawing=result.valve_drawing,
            parameters=schemas.CalculationParams(**result.parameters),
            results=schemas.CalculationResult(**result.results)
        )
        for result in results
    ]