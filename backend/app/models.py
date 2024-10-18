import uuid

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


from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Turbine(Base):
    __tablename__ = 'turbines'

    id = Column(Integer, primary_key=True, index=True)
    turbin_name = Column(String, nullable=False, unique=True, index=True)
    valves = relationship("Valve", back_populates="turbine")

    def __repr__(self):
        return f"<Turbine(turbin_name='{self.turbin_name}')>"


class Valve(Base):
    __tablename__ = 'valves'

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=True)
    verified = Column(Boolean, nullable=True)
    verifier = Column(String, nullable=True)
    valve_type = Column(String, nullable=True)
    valve_drawing = Column(String, nullable=False, unique=True, index=True)
    section_count = Column(Integer, nullable=True)
    bushing_drawing = Column(String, nullable=True)
    rod_drawing = Column(String, nullable=True)
    rod_diameter = Column(Float, nullable=True)
    rod_accuracy = Column(Float, nullable=True)
    bushing_accuracy = Column(Float, nullable=True)
    calculated_gap = Column(Float, nullable=True)
    rounding_radius = Column(Float, nullable=True)
    turbin_id = Column(Integer, ForeignKey('turbines.id'), nullable=True)
    turbine = relationship("Turbine", back_populates="valves")
    section_length_1 = Column(Float, nullable=True)
    section_length_2 = Column(Float, nullable=True)
    section_length_3 = Column(Float, nullable=True)
    section_length_4 = Column(Float, nullable=True)
    section_length_5 = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Valve(valve_drawing='{self.valve_drawing}', valve_type='{self.valve_type}')>"


class CalculationResultDB(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    valve_drawing = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    results = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<CalculationResultDB(valve_drawing='{self.valve_drawing}', date='{self.date}')>"
