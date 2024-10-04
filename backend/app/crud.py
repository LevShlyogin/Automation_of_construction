import uuid
from typing import Any

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
from typing import List, Optional, Union


def get_valves_by_turbine(db: Session, turbin_name: str) -> Optional[schemas.TurbineValves]:
    turbine = db.query(models.Turbine).filter(models.Turbine.turbin_name == turbin_name).first()
    if not turbine:
        return None

    valves = turbine.valves
    valve_infos = [schemas.ValveInfo(
        id=valve.id,
        source=valve.source,
        verified=valve.verified,
        verifier=valve.verifier,
        valve_type=valve.valve_type,
        valve_drawing=valve.valve_drawing,
        section_count=valve.section_count,
        bushing_drawing=valve.bushing_drawing,
        rod_drawing=valve.rod_drawing,
        rod_diameter=valve.rod_diameter,
        rod_accuracy=valve.rod_accuracy,
        bushing_accuracy=valve.bushing_accuracy,
        calculated_gap=valve.calculated_gap,
        section_lengths=[
            valve.section_length_1,
            valve.section_length_2,
            valve.section_length_3,
            valve.section_length_4,
            valve.section_length_5
        ],
        rounding_radius=valve.rounding_radius,
        turbine=schemas.TurbineInfo(
            id=turbine.id,
            turbin_name=turbine.turbin_name
        )
    ) for valve in valves]

    return schemas.TurbineValves(count=len(valve_infos), valves=valve_infos)


def get_valve_by_drawing(db: Session, valve_drawing: str) -> Optional[schemas.ValveInfo]:
    valve = db.query(models.Valve).options(joinedload(models.Valve.turbine)).filter(
        models.Valve.valve_drawing == valve_drawing).first()
    if valve is None:
        return None
    turbine = valve.turbine
    turbine_info = schemas.TurbineInfo(
        id=turbine.id,
        turbin_name=turbine.turbin_name
    ) if turbine else None
    return schemas.ValveInfo(
        id=valve.id,
        source=valve.source,
        verified=valve.verified,
        verifier=valve.verifier,
        valve_type=valve.valve_type,
        valve_drawing=valve.valve_drawing,
        section_count=valve.section_count,
        bushing_drawing=valve.bushing_drawing,
        rod_drawing=valve.rod_drawing,
        rod_diameter=valve.rod_diameter,
        rod_accuracy=valve.rod_accuracy,
        bushing_accuracy=valve.bushing_accuracy,
        calculated_gap=valve.calculated_gap,
        section_lengths=[
            valve.section_length_1,
            valve.section_length_2,
            valve.section_length_3,
            valve.section_length_4,
            valve.section_length_5
        ],
        rounding_radius=valve.rounding_radius,
        turbine=turbine_info
    )


def get_valve_by_id(db: Session, valve_id: int) -> Optional[schemas.ValveInfo]:
    valve = db.query(models.Valve).options(joinedload(models.Valve.turbine)).filter(models.Valve.id == valve_id).first()
    if valve is None:
        return None
    turbine = valve.turbine
    turbine_info = schemas.TurbineInfo(
        id=turbine.id,
        turbin_name=turbine.turbin_name
    ) if turbine else None
    return schemas.ValveInfo(
        id=valve.id,
        source=valve.source,
        verified=valve.verified,
        verifier=valve.verifier,
        valve_type=valve.valve_type,
        valve_drawing=valve.valve_drawing,
        section_count=valve.section_count,
        bushing_drawing=valve.bushing_drawing,
        rod_drawing=valve.rod_drawing,
        rod_diameter=valve.rod_diameter,
        rod_accuracy=valve.rod_accuracy,
        bushing_accuracy=valve.bushing_accuracy,
        calculated_gap=valve.calculated_gap,
        section_lengths=[
            valve.section_length_1,
            valve.section_length_2,
            valve.section_length_3,
            valve.section_length_4,
            valve.section_length_5
        ],
        rounding_radius=valve.rounding_radius,
        turbine=turbine_info
    )
