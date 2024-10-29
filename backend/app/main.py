import json

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from backend.app.crud import create_calculation_result
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
from fastapi import Depends, HTTPException, Response
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


# Для турбины
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


@app.post("/turbines", response_model=schemas.TurbineInfo)
async def create_turbine(turbine: schemas.TurbineInfo, db: Session = Depends(get_db)):
    db_turbine = models.Turbine(name=turbine.name)
    db.add(db_turbine)
    db.commit()
    db.refresh(db_turbine)
    return db_turbine


@app.delete("/turbines/{turbine_id}", status_code=204)
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    db_turbine = db.query(models.Turbine).filter(models.Turbine.id == turbine_id).first()
    if db_turbine is None:
        raise HTTPException(status_code=404, detail="Turbine not found")
    db.delete(db_turbine)
    db.commit()

@app.get("/valves/{valve_name}/turbine", response_model=schemas.TurbineInfo)
async def get_turbine_by_valve_name(valve_name: str, db: Session = Depends(get_db)):
    valve = db.query(models.Valve).filter(models.Valve.name == valve_name).first()
    if not valve:
        raise HTTPException(status_code=404, detail=f"Valve with name '{valve_name}' not found")

    turbine = db.query(models.Turbine).filter(models.Turbine.id == valve.turbine_id).first()
    if not turbine:
        raise HTTPException(status_code=404, detail=f"Turbine for valve '{valve_name}' not found")

    return schemas.TurbineInfo.model_validate(turbine)


# Клапаны
@app.get("/valves", response_model=List[schemas.ValveInfo])
async def get_valves(db: Session = Depends(get_db)):
    valves = db.query(models.Valve).all()

    # Проверяем, что все клапаны имеют корректное имя.
    for valve in valves:
        if valve.name is None:
            valve.name = "Unknown"  # Или какое-то другое значение по умолчанию

    return valves


@app.post("/valves/", response_model=schemas.ValveCreate)
async def create_valve(valve: schemas.ValveCreate, db: Session = Depends(get_db)):
    # Проверяем, что клапан с таким именем еще не существует
    existing_valve = db.query(models.Valve).filter(models.Valve.name == valve.name).first()
    if existing_valve:
        raise HTTPException(status_code=400, detail="Valve with this name already exists.")

    new_valve = models.Valve(
        name=valve.name,
        type=valve.type,
        diameter=valve.diameter,
        clearance=valve.clearance,
        count_parts=valve.count_parts,
        len_part1=valve.len_part1,
        len_part2=valve.len_part2,
        len_part3=valve.len_part3,
        len_part4=valve.len_part4,
        len_part5=valve.len_part5,
        round_radius=valve.round_radius,
        turbine_id=valve.turbine_id
    )

    db.add(new_valve)
    db.commit()
    db.refresh(new_valve)

    return new_valve


@app.put("/valves/{valve_id}", response_model=schemas.ValveInfo)
async def update_valve(valve_id: int, valve: schemas.ValveInfo, db: Session = Depends(get_db)):
    db_valve = db.query(models.Valve).filter(models.Valve.id == valve_id).first()
    if db_valve is None:
        raise HTTPException(status_code=404, detail="Valve not found")
    db_valve.name = valve.name
    db_valve.type = valve.type
    db_valve.diameter = valve.diameter
    db_valve.clearance = valve.clearance
    db_valve.count_parts = valve.count_parts
    db_valve.len_part1 = valve.len_part1
    db_valve.len_part2 = valve.len_part2
    db_valve.len_part3 = valve.len_part3
    db_valve.len_part4 = valve.len_part4
    db_valve.len_part5 = valve.len_part5
    db_valve.round_radius = valve.round_radius
    db_valve.turbine_id = valve.turbine_id
    db.commit()
    db.refresh(db_valve)
    return db_valve


@app.delete("/valves/{valve_id}", response_model=dict)
async def delete_valve(valve_id: int, db: Session = Depends(get_db)):
    # Найдите клапан с заданным ID
    valve = db.query(models.Valve).filter(models.Valve.id == valve_id).first()

    # Если клапан не найден, верните ошибку
    if valve is None:
        raise HTTPException(status_code=404, detail="Valve not found")

    # Удалите клапан из базы данных
    db.delete(valve)
    db.commit()

    # Верните сообщение об успешном удалении
    return {"message": "Valve successfully deleted"}


# Вычисления
@app.post("/calculate", response_model=schemas.CalculationResultDB)
async def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
    # Комментим на время для проверки работ расчётов
    # valve_info = params.valve_info  # Используем данные о клапане, переданные с фронтенда

    # Получение данных о клапане из базы данных по имени
    valve = db.query(models.Valve).filter(models.Valve.name == params.valve_drawing).first()
    if not valve:
        raise HTTPException(status_code=404, detail=f"Valve with name '{params.valve_drawing}' not found")

    # Преобразование данных о клапане в ValveInfo
    valve_info = schemas.ValveInfo.model_validate(valve)

    try:
        # Выполнение расчётов
        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()
    except CalculationError as ce:
        raise HTTPException(status_code=400, detail=ce.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при выполнении расчётов: {e}")

    # Сохранение результатов в базе данных
    new_result = create_calculation_result(
        db=db,
        parameters=params,
        results=calculation_result,
        valve_id=valve.id
    )

    # Возвращаем результат
    return schemas.CalculationResultDB(
        id=new_result.id,
        user_name=new_result.user_name,
        stock_name=new_result.stock_name,
        turbine_name=new_result.turbine_name,
        calc_timestamp=new_result.calc_timestamp,
        input_data=json.loads(new_result.input_data),
        output_data=json.loads(new_result.output_data)
    )


# Результаты
@app.get("/valves/{valve_name}/results/", response_model=List[schemas.CalculationResultDB])
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    db_results = crud.get_results_by_valve_drawing(db, valve_drawing=valve_name)

    if not db_results:
        return []

    calculation_results = [
        schemas.CalculationResultDB(
            id=result.id,
            user_name=result.user_name,
            stock_name=result.stock_name,
            turbine_name=result.turbine_name,
            calc_timestamp=result.calc_timestamp,
            input_data=result.input_data,  # Преобразование в Pydantic модель
            output_data=result.output_data # Преобразование в Pydantic модель
        ) for result in db_results
    ]

    return calculation_results


@app.delete("/results/{result_id}", status_code=204)
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(models.CalculationResultDB).filter(models.CalculationResultDB.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Calculation result not found")
    db.delete(result)
    db.commit()
    return Response(status_code=204)
