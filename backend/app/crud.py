import uuid
from typing import Any, Type

from sqlmodel import Session, select

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models import Item, ItemCreate, User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


from sqlalchemy.orm import Session, joinedload
from backend.app import models, schemas
from typing import Optional
from datetime import datetime, timezone
import json
from sqlalchemy import text

def get_valves_by_turbine(db: Session, turbin_name: str) -> Optional[schemas.TurbineValves]:
    valves = db.query(models.Valve).join(models.Turbine, text("stocks.name = turbines.valves")).filter(models.Turbine.name == turbin_name).all()

    if not valves:
        return None  # Возвращаем None, если клапаны не найдены

    all_valves = []
    for valve in valves:
        valve_info = schemas.ValveInfo(
            id=valve.id,
            name=valve.name,
            type=valve.type,
            diameter=valve.diameter,
            clearance=valve.clearance,
            count_parts=valve.count_parts,
            section_lengths=[
                valve.len_part1,
                valve.len_part2,
                valve.len_part3,
                valve.len_part4,
                valve.len_part5,
            ],
            round_radius=valve.round_radius,
            turbine=schemas.TurbineInfo(id=valve.turbine_id, name=turbin_name),
        )
        all_valves.append(valve_info)

    return schemas.TurbineValves(count=len(all_valves), valves=all_valves)  # Изменено возвращаемое значение


def get_valve_by_drawing(db: Session, valve_drawing: str) -> Optional[schemas.ValveInfo]:
    valve = db.query(models.Valve).options(joinedload(models.Valve.turbine)).filter(
        models.Valve.name == valve_drawing).first()
    if valve is None:
        return None
    turbine = valve.turbine
    turbine_info = schemas.TurbineInfo(
        id=turbine.id,
        name=turbine.name
    ) if turbine else None
    return schemas.ValveInfo(
        id=valve.id,
        name=valve.name,
        type=valve.type,
        diameter=valve.diameter,
        clearance=valve.clearance,
        count_parts=valve.count_parts,
        section_lengths=[
            valve.len_part1,
            valve.len_part2,
            valve.len_part3,
            valve.len_part4,
            valve.len_part5
        ],
        round_radius=valve.round_radius,
        turbine=turbine_info
    )


def get_valve_by_id(db: Session, valve_id: int) -> Optional[schemas.ValveInfo]:
    valve = db.query(models.Valve).options(joinedload(models.Valve.turbine)).filter(models.Valve.id == valve_id).first()
    if valve is None:
        return None
    turbine = valve.turbine
    turbine_info = schemas.TurbineInfo(
        id=turbine.id,
        name=turbine.name
    ) if turbine else None
    return schemas.ValveInfo(
        id=valve.id,
        name=valve.name,
        type=valve.type,
        diameter=valve.diameter,
        clearance=valve.clearance,
        count_parts=valve.count_parts,
        section_lengths=[
            valve.len_part1,
            valve.len_part2,
            valve.len_part3,
            valve.len_part4,
            valve.len_part5
        ],
        round_radius=valve.round_radius,
        turbine=turbine_info
    )


def create_calculation_result(db: Session, valve_drawing: str, parameters: schemas.CalculationParams, results: schemas.CalculationResult) -> models.CalculationResultDB:
    try:
        db_result = models.CalculationResultDB(
            valve_drawing=valve_drawing,
            parameters=json.dumps(parameters.model_dump()),
            results=json.dumps(results.model_dump()),
            calc_timestamp=datetime.now(timezone.utc)
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while saving the calculation result: {str(e)}")


def get_results_by_valve_drawing(db: Session, valve_drawing: str) -> list[Type[models.CalculationResultDB]]:
    try:
        return db.query(models.CalculationResultDB).filter(models.CalculationResultDB.stock.name == valve_drawing).order_by(models.CalculationResultDB.calc_timestamp.desc()).all()
    except Exception as e:
        raise Exception(f"An error occurred while retrieving results: {str(e)}")
