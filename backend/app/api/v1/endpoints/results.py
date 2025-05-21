from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.schemas import CalculationResultDB
from backend.app.dependencies import get_db
from backend.app.crud import get_results_by_valve_drawing
import logging

router = APIRouter(prefix="/results", tags=["results"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/{valve_name}/", response_model=List[CalculationResultDB], summary="Получить результаты расчётов")
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    try:
        results = get_results_by_valve_drawing(db, valve_name)
        return results
    except Exception as e:
        logger.error(f"Ошибка при получении результатов расчёта: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось получить результаты: {e}")

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить результат расчёта")
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    try:
        result = db.query(CalculationResultDB).filter(CalculationResultDB.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Результат не найден")
        db.delete(result)
        db.commit()
        return {"message": "Результат успешно удалён"}
    except Exception as e:
        logger.error(f"Ошибка при удалении результата: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось удалить результат: {e}") 