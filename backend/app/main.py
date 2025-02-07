import json
import sentry_sdk
import logging

from fastapi import FastAPI, Depends, HTTPException, Response, status, APIRouter
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.config import settings
from backend.app.models import Turbine, Valve, CalculationResultDB  # Предполагая, что эти модели определены
from backend.app.schemas import (
    TurbineInfo,
    ValveInfo,
    ValveCreate,
    TurbineValves,
    CalculationParams,
    CalculationResultDB as CalculationResultDBSchema,
)  # Предполагая, что эти схемы определены
from backend.app.dependencies import get_db  # Зависимость для получения сессии БД
from backend.app.utils import ValveCalculator, CalculationError
from backend.app.crud import create_calculation_result, get_results_by_valve_drawing, \
    get_valves_by_turbine  # CRUD функции

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


# Инициализация Sentry, если требуется
if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# Создаем экземпляр приложения FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Укажите адрес вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем экземпляр APIRouter
api_router = APIRouter()


# ------ Маршруты для турбин ------

@api_router.get("/turbines/", response_model=List[TurbineInfo], summary="Получить все турбины", tags=["turbines"])
async def get_all_turbines(db: Session = Depends(get_db)):
    """
    Получить список всех турбин.
    """
    try:
        turbines = db.query(Turbine).all()
        turbine_infos = [TurbineInfo(id=turbine.id, name=turbine.name) for turbine in turbines]
        return turbine_infos
    except Exception as e:
        logger.error(f"Ошибка при получении всех турбин: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить турбины: {e}")


@api_router.get("/turbines/{turbine_name}/valves/", response_model=TurbineValves,
                summary="Получить клапаны по имени турбины", tags=["turbines"])
async def get_valves_by_turbine_endpoint(turbine_name: str, db: Session = Depends(get_db)):
    """
    Получить список клапанов для заданной турбины.
    """
    try:
        turbine_valves = get_valves_by_turbine(db, turbine_name=turbine_name)
        if turbine_valves is None:
            raise HTTPException(status_code=404,
                                detail=f"Турбина с именем '{turbine_name}' не найдена или у неё нет клапанов")
        return turbine_valves
    except Exception as e:
        logger.error(f"Ошибка при получении клапанов для турбины {turbine_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")


@api_router.post("/turbines", response_model=TurbineInfo, status_code=status.HTTP_201_CREATED,
                 summary="Создать турбину", tags=["turbines"])
async def create_turbine(turbine: TurbineInfo, db: Session = Depends(get_db)):
    """
    Создать новую турбину.
    """
    try:
        db_turbine = Turbine(name=turbine.name)
        db.add(db_turbine)
        db.commit()
        db.refresh(db_turbine)
        return db_turbine
    except Exception as e:
        logger.error(f"Ошибка при создании турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось создать турбину: {e}")


@api_router.delete("/turbines/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину",
                   tags=["turbines"])
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    """
    Удалить турбину по ID.
    """
    try:
        db_turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
        if db_turbine is None:
            raise HTTPException(status_code=404, detail="Турбина не найдена")
        db.delete(db_turbine)
        db.commit()
        return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
    except Exception as e:
        logger.error(f"Ошибка при удалении турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить турбину: {e}")


# ------ Маршруты для клапанов ------

@api_router.get("/valves", response_model=List[ValveInfo], summary="Получить все клапаны", tags=["valves"])
async def get_valves(db: Session = Depends(get_db)):
    """
    Получить список всех клапанов.
    """
    try:
        valves = db.query(Valve).all()
        for valve in valves:
            if valve.name is None:
                valve.name = "Unknown"  # Или другое значение по умолчанию
        return valves
    except Exception as e:
        logger.error(f"Ошибка при получении всех клапанов: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")


@api_router.post("/valves/", response_model=ValveInfo, status_code=status.HTTP_201_CREATED, summary="Создать клапан",
                 tags=["valves"])
async def create_valve(valve: ValveCreate, db: Session = Depends(get_db)):
    """
    Создать новый клапан.
    """
    try:
        existing_valve = db.query(Valve).filter(Valve.name == valve.name).first()
        if existing_valve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Клапан с таким именем уже существует.")

        new_valve = Valve(
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
    except Exception as e:
        logger.error(f"Ошибка при создании клапана: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось создать клапан: {e}")


@api_router.put("/valves/{valve_id}", response_model=ValveInfo, summary="Обновить клапан", tags=["valves"])
async def update_valve(valve_id: int, valve: ValveInfo, db: Session = Depends(get_db)):
    """
    Обновить данные о клапане.
    """
    try:
        db_valve = db.query(Valve).filter(Valve.id == valve_id).first()
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
        return db_valve
    except Exception as e:
        logger.error(f"Ошибка при обновлении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось обновить клапан: {e}")


@api_router.delete("/valves/{valve_id}", response_model=dict, summary="Удалить клапан", tags=["valves"])
async def delete_valve(valve_id: int, db: Session = Depends(get_db)):
    """
    Удалить клапан по ID.
    """
    try:
        valve = db.query(Valve).filter(Valve.id == valve_id).first()
        if valve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан не найден")
        db.delete(valve)
        db.commit()
        return {"message": f"Клапан '{valve.name}' успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось удалить клапан: {e}")


@api_router.get("/valves/{valve_name}/turbine", response_model=TurbineInfo, summary="Получить турбину по имени клапана",
                tags=["valves"])
async def get_turbine_by_valve_name(valve_name: str, db: Session = Depends(get_db)):
    """
    Получить турбину по имени клапана.
    """
    try:
        valve = db.query(Valve).filter(Valve.name == valve_name).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Клапан с именем '{valve_name}' не найден")

        turbine = db.query(Turbine).filter(Turbine.id == valve.turbine_id).first()
        if not turbine:
            raise HTTPException(status_code=404, detail=f"Турбина для клапана '{valve_name}' не найдена")

        return TurbineInfo.model_validate(turbine)
    except Exception as e:
        logger.error(f"Ошибка при получении турбины для клапана {valve_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")


# ------ Маршруты для вычислений ------

@api_router.post("/calculate", response_model=CalculationResultDBSchema, summary="Выполнить расчет",
                 tags=["calculations"])
async def calculate(params: CalculationParams, db: Session = Depends(get_db)):
    """
    Выполнить расчет на основе параметров.
    """
    try:
        valve = db.query(Valve).filter(Valve.name == params.valve_drawing).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Клапан с именем '{params.valve_drawing}' не найден")

        valve_info = ValveInfo.model_validate(valve)

        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()

        new_result = create_calculation_result(
            db=db,
            parameters=params,
            results=calculation_result,
            valve_id=valve.id
        )

        return CalculationResultDBSchema(
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


# ------ Маршруты для результатов ------

@api_router.get("/valves/{valve_name}/results/", response_model=List[CalculationResultDBSchema],
                summary="Получить результаты расчётов", tags=["results"])
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    """
    Получить список результатов расчётов для заданного клапана.
    """
    try:
        db_results = get_results_by_valve_drawing(db, valve_drawing=valve_name)

        if not db_results:
            return []

        calculation_results = []
        for result in db_results:
            input_data = result.input_data
            output_data = result.output_data

            # Проверяем, если input_data или output_data - строка, конвертируем её в dict
            if isinstance(input_data, str):
                input_data = json.loads(input_data)
            if isinstance(output_data, str):
                output_data = json.loads(output_data)

            calculation_results.append(
                CalculationResultDBSchema(
                    id=result.id,
                    user_name=result.user_name,
                    stock_name=result.stock_name,
                    turbine_name=result.turbine_name,
                    calc_timestamp=result.calc_timestamp,
                    input_data=input_data,
                    output_data=output_data,
                )
            )

        return calculation_results

    except Exception as e:
        logger.error(f"Ошибка при получении результатов расчётов для клапана {valve_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить результаты расчётов: {e}",
        )


@api_router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить результат расчёта",
                   tags=["results"])
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """
    Удалить результат расчёта по ID.
    """
    try:
        result = db.query(CalculationResultDB).filter(CalculationResultDB.id == result_id).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Результат расчёта не найден")
        db.delete(result)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Ошибка при удалении результата расчёта {result_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить результат расчёта: {e}")


# Подключаем маршруты к приложению
app.include_router(api_router, prefix=settings.API_V1_STR)
