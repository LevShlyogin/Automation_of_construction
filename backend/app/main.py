import json

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

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

origins = [
    "http://localhost:3001",  # Добавьте адрес вашего фронтенда
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# main.py
from fastapi import Depends, HTTPException, Response, status
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
@app.get("/turbines/", response_model=List[schemas.TurbineInfo], summary="Получить все турбины")
async def get_all_turbines(db: Session = Depends(get_db)):
    """
    Получить список всех турбин.

    :param db: Сессия базы данных
    :return: Список всех турбин
    """
    try:
        turbines = db.query(models.Turbine).all()
        turbine_infos = [
            schemas.TurbineInfo(
                id=turbine.id,
                name=turbine.name
            ) for turbine in turbines
        ]
        return turbine_infos
    except Exception as e:
        logger.error(f"Ошибка при получении всех турбин: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить турбины: {e}")


@app.get("/turbines/{turbine_name}/valves/", response_model=schemas.TurbineValves, summary="Получить клапаны по имени турбины")
async def get_valves_by_turbine(turbine_name: str, db: Session = Depends(get_db)):
    """
    Получить список клапанов для заданной турбины.

    :param turbine_name: Имя турбины
    :param db: Сессия базы данных
    :return: Список клапанов турбины
    """
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.post("/turbines", response_model=schemas.TurbineInfo, status_code=status.HTTP_201_CREATED, summary="Создать турбину")
async def create_turbine(turbine: schemas.TurbineInfo, db: Session = Depends(get_db)):
    """
    Создать новую турбину.

    :param turbine: Данные о турбине
    :param db: Сессия базы данных
    :return: Созданная турбина
    """
    try:
        db_turbine = models.Turbine(name=turbine.name)
        db.add(db_turbine)
        db.commit()
        db.refresh(db_turbine)
        return db_turbine, {"message": f"Турбина '{turbine.name}' успешно создана"}
    except Exception as e:
        logger.error(f"Ошибка при создании турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось создать турбину: {e}")


@app.delete("/turbines/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину")
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    """
    Удалить турбину по ID.

    :param turbine_id: ID турбины
    :param db: Сессия базы данных
    :return: HTTP статус
    """
    try:
        db_turbine = db.query(models.Turbine).filter(models.Turbine.id == turbine_id).first()
        if db_turbine is None:
            raise HTTPException(status_code=404, detail="Турбина не найдена")
        db.delete(db_turbine)
        db.commit()
        return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
    except Exception as e:
        logger.error(f"Ошибка при удалении турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить турбину: {e}")



@app.get("/valves/{valve_name}/turbine", response_model=schemas.TurbineInfo, summary="Получить турбину по имени клапана")
async def get_turbine_by_valve_name(valve_name: str, db: Session = Depends(get_db)):
    """
    Получить турбину по имени клапана.

    :param valve_name: Имя клапана
    :param db: Сессия базы данных
    :return: Турбина
    """
    try:
        valve = db.query(models.Valve).filter(models.Valve.name == valve_name).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Клапан с именем '{valve_name}' не найден")

        turbine = db.query(models.Turbine).filter(models.Turbine.id == valve.turbine_id).first()
        if not turbine:
            raise HTTPException(status_code=404, detail=f"Турбина для клапана '{valve_name}' не найдена")

        return schemas.TurbineInfo.model_validate(turbine)
    except Exception as e:
        logger.error(f"Ошибка при получении турбины для клапана {valve_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")


# Клапаны
@app.get("/valves", response_model=List[schemas.ValveInfo], summary="Получить все клапаны")
async def get_valves(db: Session = Depends(get_db)):
    """
    Получить список всех клапанов.

    :param db: Сессия базы данных
    :return: Список всех клапанов
    """
    try:
        valves = db.query(models.Valve).all()

        # Проверяем, что все клапаны имеют корректное имя.
        for valve in valves:
            if valve.name is None:
                valve.name = "Unknown"  # Или какое-то другое значение по умолчанию

        return valves
    except Exception as e:
        logger.error(f"Ошибка при получении всех клапанов: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")


@app.post("/valves/", response_model=schemas.ValveCreate, status_code=status.HTTP_201_CREATED, summary="Создать клапан")
async def create_valve(valve: schemas.ValveCreate, db: Session = Depends(get_db)):
    """
    Создать новый клапан.

    :param valve: Данные о клапане
    :param db: Сессия базы данных
    :return: Сообщение об успешном создании клапана
    """
    try:
        # Проверяем, что клапан с таким именем еще не существует
        existing_valve = db.query(models.Valve).filter(models.Valve.name == valve.name).first()
        if existing_valve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Клапан с таким именем уже существует.")

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

        return new_valve, {"message": f"Клапан '{valve.name}' успешно создан"}
    except Exception as e:
        logger.error(f"Ошибка при создании клапана: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось создать клапан: {e}")


@app.put("/valves/{valve_id}", response_model=schemas.ValveInfo, summary="Обновить клапан")
async def update_valve(valve_id: int, valve: schemas.ValveInfo, db: Session = Depends(get_db)):
    """
    Обновить данные о клапане.

    :param valve_id: ID клапана
    :param valve: Обновленные данные о клапане
    :param db: Сессия базы данных
    :return: Сообщение об успешном обновлении клапана
    """
    try:
        db_valve = db.query(models.Valve).filter(models.Valve.id == valve_id).first()
        if db_valve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан не найден")
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
        return db_valve, {"message": f"Клапан '{db_valve.name}' успешно обновлен", "valve": db_valve}
    except Exception as e:
        logger.error(f"Ошибка при обновлении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось обновить клапан: {e}")


@app.delete("/valves/{valve_id}", response_model=dict, summary="Удалить клапан")
async def delete_valve(valve_id: int, db: Session = Depends(get_db)):
    """
    Удалить клапан по ID.

    :param valve_id: ID клапана
    :param db: Сессия базы данных
    :return: Сообщение об успешном удалении клапана
    """
    try:
        # Найдите клапан с заданным ID
        valve = db.query(models.Valve).filter(models.Valve.id == valve_id).first()

        # Если клапан не найден, верните ошибку
        if valve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан не найден")
        # Удалите клапан из базы данных
        db.delete(valve)
        db.commit()
        return {"message": f"Клапан '{valve.name}' успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось удалить клапан: {e}")


# Вычисления
@app.post("/calculate", response_model=schemas.CalculationResultDB, summary="Выполнить расчет")
async def calculate(params: schemas.CalculationParams, db: Session = Depends(get_db)):
    """
    Выполнить расчет на основе параметров.

    :param params: Параметры расчета
    :param db: Сессия базы данных
    :return: Результаты расчета
    """
    # Комментим на время для проверки работ расчётов
    # valve_info = params.valve_info  # Используем данные о клапане, переданные с фронтенда
    try:
        # Получение данных о клапане из базы данных по имени
        valve = db.query(models.Valve).filter(models.Valve.name == params.valve_drawing).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Клапан с именем '{params.valve_drawing}' не найден")

        # Преобразование данных о клапане в ValveInfo
        valve_info = schemas.ValveInfo.model_validate(valve)

        # Выполнение расчётов
        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()

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
    except CalculationError as ce:
        logger.error(f"Ошибка при выполнении расчётов: {ce.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ce.message)
    except Exception as e:
        logger.error(f"Ошибка при выполнении расчётов: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось выполнить расчёты: {e}")


# Результаты
@app.get("/valves/{valve_name}/results/", response_model=List[schemas.CalculationResultDB])
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    """
    Получить список результатов расчётов для заданного клапана.

    :param valve_name: Имя клапана
    :param db: Сессия базы данных
    :return: Список результатов расчётов
    """
    try:
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
    except Exception as e:
        logger.error(f"Ошибка при получении результатов расчётов для клапана {valve_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить результаты расчётов: {e}")


@app.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить результат расчёта")
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """
    Удалить результат расчёта по ID.

    :param result_id: ID результата расчёта
    :param db: Сессия базы данных
    :return: HTTP статус
    """
    try:
        result = db.query(models.CalculationResultDB).filter(models.CalculationResultDB.id == result_id).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Результат расчёта не найден")
        db.delete(result)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT), {"message": f"Результат расчёта успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении результата расчёта {result_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить результат расчёта: {e}")
