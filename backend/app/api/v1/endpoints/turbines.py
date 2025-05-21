from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.models import Turbine
from backend.app.schemas import TurbineInfo, TurbineValves
from backend.app.dependencies import get_db
from backend.app.crud import get_valves_by_turbine
import logging

router = APIRouter(prefix="/turbines", tags=["turbines"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[TurbineInfo], summary="Получить все турбины")
async def get_all_turbines(db: Session = Depends(get_db)):
    try:
        turbines = db.query(Turbine).all()
        turbine_infos = [TurbineInfo(id=turbine.id, name=turbine.name) for turbine in turbines]
        return turbine_infos
    except Exception as e:
        logger.error(f"Ошибка при получении всех турбин: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось получить турбины: {e}")

@router.get("/{turbine_name}/valves/", response_model=TurbineValves, summary="Получить клапаны по имени турбины")
async def get_valves_by_turbine_endpoint(turbine_name: str, db: Session = Depends(get_db)):
    try:
        turbine_valves = get_valves_by_turbine(db, turbine_name=turbine_name)
        if turbine_valves is None:
            raise HTTPException(status_code=404, detail=f"Турбина с именем '{turbine_name}' не найдена или у неё нет клапанов")
        return turbine_valves
    except Exception as e:
        logger.error(f"Ошибка при получении клапанов для турбины {turbine_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")

@router.post("", response_model=TurbineInfo, status_code=status.HTTP_201_CREATED, summary="Создать турбину")
async def create_turbine(turbine: TurbineInfo, db: Session = Depends(get_db)):
    try:
        db_turbine = Turbine(name=turbine.name)
        db.add(db_turbine)
        db.commit()
        db.refresh(db_turbine)
        return db_turbine
    except Exception as e:
        logger.error(f"Ошибка при создании турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось создать турбину: {e}")

@router.delete("/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину")
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    try:
        db_turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
        if db_turbine is None:
            raise HTTPException(status_code=404, detail="Турбина не найдена")
        db.delete(db_turbine)
        db.commit()
        return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
    except Exception as e:
        logger.error(f"Ошибка при удалении турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось удалить турбину: {e}") 