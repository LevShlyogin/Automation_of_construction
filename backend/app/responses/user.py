from typing import Union
from datetime import datetime
from pydantic import EmailStr, BaseModel
from app.responses.base import BaseResponse


class UserResponse(BaseResponse):
    name: str
    email: EmailStr
    is_active: bool
    created_at: Union[str, None, datetime] = None
    level: int
    main_karma: int
    karma_low_level: int
    karma_medium_level: int
    karma_high_level: int


class UserRatingsResponse(BaseModel):
    name: str
    level: str
    problems_solved: int


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
