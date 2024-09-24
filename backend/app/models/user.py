from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, ForeignKey
from app.config.database import Base
from sqlalchemy.orm import mapped_column, relationship


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, server_default="NumericaUser")
    email = Column(String(255), unique=True, index=True)
    password = Column(String(100))
    karma_low_level = Column(Integer, nullable=False, default=0)
    karma_medium_level = Column(Integer, nullable=False, default=0)
    karma_high_level = Column(Integer, nullable=False, default=0)
    main_karma = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    tokens = relationship("UserToken", back_populates="user")

    def get_context_string(self, context: str):
        return f"{context}{self.password[-6:]}{self.updated_at.strftime('%m%d%Y%H%M%S')}".strip()


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey('users.id'))
    access_key = Column(String(250), nullable=True, index=True, default=None)
    refresh_key = Column(String(250), nullable=True, index=True, default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="tokens")

# class UserExample(Base): # сохраненные примеры пользователей
#     __tablename__ = "user_examples"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = mapped_column(ForeignKey('users.id'))
#     example = Column(String(255))
#
#     user1 = relationship("User", back_populates="examples")
