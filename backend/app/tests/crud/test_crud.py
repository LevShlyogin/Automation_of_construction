# tests/test_crud.py
import pytest
from sqlalchemy.orm import Session
from backend.app import crud, models, schemas
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("UTC"))

# Вспомогательные функции для создания тестовых данных
def create_test_turbine(db: Session, turbin_name: str = "Test Turbine"):
    turbine = models.Turbine(turbin_name=turbin_name)
    db.add(turbine)
    db.commit()
    db.refresh(turbine)
    return turbine

def create_test_valve(db: Session, valve_drawing: str = "VD-001", turbin_id: int = None):
    valve = models.Valve(
        valve_drawing=valve_drawing,
        valve_type="Type A",
        turbin_id=turbin_id
    )
    db.add(valve)
    db.commit()
    db.refresh(valve)
    return valve

def create_test_calculation_result(db: Session, valve_drawing: str, parameters: dict, results: dict):
    calculation_result = models.CalculationResultDB(
        valve_drawing=valve_drawing,
        parameters=parameters,
        results=results,
        date=datetime.now(timezone.utc)
    )
    db.add(calculation_result)
    db.commit()
    db.refresh(calculation_result)
    return calculation_result

# Тесты для функции get_valves_by_turbine
def test_get_valves_by_turbine(db_session):
    # Создаём турбину и клапаны
    turbine = create_test_turbine(db_session)
    valve1 = create_test_valve(db_session, turbin_id=turbine.id)
    valve2 = create_test_valve(db_session, valve_drawing="VD-002", turbin_id=turbine.id)

    # Выполняем функцию
    result = crud.get_valves_by_turbine(db_session, turbin_name="Test Turbine")

    # Проверки
    assert result is not None
    assert result.count == 2
    assert len(result.valves) == 2
    assert result.valves[0].valve_drawing == "VD-001"
    assert result.valves[1].valve_drawing == "VD-002"

def test_get_valves_by_turbine_no_turbine(db_session):
    # Выполняем функцию с несуществующей турбиной
    result = crud.get_valves_by_turbine(db_session, turbin_name="Nonexistent Turbine")

    # Проверки
    assert result is None

# Тесты для функции get_valve_by_drawing
def test_get_valve_by_drawing(db_session):
    # Создаём клапан
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_drawing="VD-003", turbin_id=turbine.id)

    # Выполняем функцию
    result = crud.get_valve_by_drawing(db_session, valve_drawing="VD-003")

    # Проверки
    assert result is not None
    assert result.valve_drawing == "VD-003"
    assert result.turbine.turbin_name == "Test Turbine"

def test_get_valve_by_drawing_not_found(db_session):
    # Выполняем функцию с несуществующим чертежом
    result = crud.get_valve_by_drawing(db_session, valve_drawing="Nonexistent Drawing")

    # Проверки
    assert result is None

# Тесты для функции get_valve_by_id
def test_get_valve_by_id(db_session):
    # Создаём клапан
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_drawing="VD-004", turbin_id=turbine.id)

    # Выполняем функцию
    result = crud.get_valve_by_id(db_session, valve_id=valve.id)

    # Проверки
    assert result is not None
    assert result.id == valve.id
    assert result.valve_drawing == "VD-004"


def test_get_valve_by_id_not_found(db_session):
    # Выполняем функцию с несуществующим ID
    result = crud.get_valve_by_id(db_session, valve_id=999)

    # Проверки
    assert result is None


# Тесты для функции create_calculation_result
def test_create_calculation_result(db_session):
    # Создаём клапан
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_drawing="VD-005", turbin_id=turbine.id)

    # Параметры и результаты
    parameters = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.valve_drawing,
        valve_id=valve.id,
        temperature_start=100.0,
        t_air=300.0,
        count_valves=2,
        p_ejector=[1.0, 2.0],
        p_values=[3.0, 4.0]
    ).model_dump()

    results = schemas.CalculationResult(
        Gi=[1.1, 2.2],
        Pi_in=[3.3, 4.4],
        Ti=[5.5, 6.6],
        Hi=[7.7, 8.8],
        deaerator_props=[9.9, 10.1, 11.11, 12.12],
        ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}]
    ).model_dump()

    # Выполняем функцию
    db_result = crud.create_calculation_result(
        db=db_session,
        valve_drawing="VD-005",
        parameters=parameters,
        results=results
    )

    # Проверки
    assert db_result.id is not None
    assert db_result.valve_drawing == "VD-005"
    assert db_result.parameters == parameters
    assert db_result.results == results
    assert isinstance(db_result.date, datetime)
    assert db_result.date.tzinfo == timezone.utc


# Тесты для функции get_results_by_valve_drawing
def test_get_results_by_valve_drawing(db_session):
    # Создаём клапан и результаты
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_drawing="VD-006", turbin_id=turbine.id)

    parameters1 = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.valve_drawing,
        valve_id=valve.id,
        temperature_start=100.0,
        t_air=300.0,
        count_valves=2,
        p_ejector=[1.0, 2.0],
        p_values=[3.0, 4.0]
    ).model_dump()

    results1 = schemas.CalculationResult(
        Gi=[1.1, 2.2],
        Pi_in=[3.3, 4.4],
        Ti=[5.5, 6.6],
        Hi=[7.7, 8.8],
        deaerator_props=[9.9, 10.1, 11.11, 12.12],
        ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}]
    ).model_dump()

    calculation_result1 = create_test_calculation_result(db_session, "VD-006", parameters1, results1)

    parameters2 = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.valve_drawing,
        valve_id=valve.id,
        temperature_start=200.0,
        t_air=400.0,
        count_valves=3,
        p_ejector=[2.0, 3.0],
        p_values=[4.0, 5.0]
    ).model_dump()

    results2 = schemas.CalculationResult(
        Gi=[2.2, 3.3],
        Pi_in=[4.4, 5.5],
        Ti=[6.6, 7.7],
        Hi=[8.8, 9.9],
        deaerator_props=[10.10, 11.11, 12.12, 13.13],
        ejector_props=[{"g": 14.14, "t": 15.15, "h": 16.16, "p": 17.17}]
    ).model_dump()

    calculation_result2 = create_test_calculation_result(db_session, "VD-006", parameters2, results2)

    # Выполняем функцию
    results = crud.get_results_by_valve_drawing(db_session, valve_drawing="VD-006")

    # Проверки
    assert len(results) == 2
    assert results[0].id == calculation_result2.id  # Порядок по дате.desc
    assert results[1].id == calculation_result1.id
    assert results[0].valve_drawing == "VD-006"
    assert results[1].valve_drawing == "VD-006"


def test_get_results_by_valve_drawing_not_found(db_session):
    # Выполняем функцию с несуществующим чертежом
    results = crud.get_results_by_valve_drawing(db_session, valve_drawing="Nonexistent Drawing")

    # Проверки
    assert results == []


def test_create_calculation_result_invalid_data(db_session):
    # Создаём клапан
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_drawing="VD-007", turbin_id=turbine.id)

    # Некорректные параметры (например, строка вместо числа)
    parameters = {
        "turbine_name": "Test Turbine",
        "valve_drawing": "VD-007",
        "valve_id": valve.id,
        "temperature_start": "invalid",  # Должно быть float
        "t_air": 300.0,
        "count_valves": 2,
        "p_ejector": [1.0, 2.0],
        "p_values": [3.0, 4.0]
    }

    results = {
        "Gi": [1.1, 2.2],
        "Pi_in": [3.3, 4.4],
        "Ti": [5.5, 6.6],
        "Hi": [7.7, 8.8],
        "deaerator_props": [9.9, 10.1, 11.11, 12.12],
        "ejector_props": [{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}]
    }

    with pytest.raises(ValueError):
        crud.create_calculation_result(
            db=db_session,
            valve_drawing="VD-007",
            parameters=parameters,
            results=results
        )