import uuid

import sqlalchemy
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = sqlalchemy.orm.declarative_base()

class Turbine(Base):
    __tablename__ = 'unique_turbine'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)

    # Связь с Valve
    valves = relationship("Valve", back_populates="turbine")

    def __repr__(self):
        return f"<Turbine(name='{self.name}')>"

class Valve(Base):
    __tablename__ = 'stocks'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=True)
    diameter = Column(Float, nullable=True)
    clearance = Column(Float, nullable=True)
    count_parts = Column(Integer, nullable=True)
    len_part1 = Column(Float, nullable=True)
    len_part2 = Column(Float, nullable=True)
    len_part3 = Column(Float, nullable=True)
    len_part4 = Column(Float, nullable=True)
    len_part5 = Column(Float, nullable=True)
    round_radius = Column(Float, nullable=True)

    # Внешний ключ на UniqueTurbine
    turbine_id = Column(Integer, ForeignKey('autocalc.unique_turbine.id'), nullable=False)

    # Связь с Turbine
    turbine = relationship("Turbine", back_populates="valves")

    # Связь с CalculationResultDB
    calculation_results = relationship("CalculationResultDB", back_populates="valve")

    def __repr__(self):
        return f"<Valve(name='{self.name}', valve_type='{self.type}')>"

class CalculationResultDB(Base):
    __tablename__ = 'resultcalcs'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=True)
    stock_name = Column(String, nullable=False)
    turbine_name = Column(String, nullable=False)
    calc_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)

    # Внешний ключ на Valve - обязательно применять на бд
    valve_id = Column(Integer, ForeignKey('autocalc.stocks.id'), nullable=False)

    # Связь с Valve
    valve = relationship("Valve", back_populates="calculation_results")


    def __repr__(self):
        return f"<CalculationResultDB(stock_name='{self.stock_name}', turbine_name='{self.turbine_name}')>"
