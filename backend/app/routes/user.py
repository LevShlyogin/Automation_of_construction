from fastapi import APIRouter, BackgroundTasks, Depends, status, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, List

from app.config.database import get_session
from app.responses.user import UserResponse, LoginResponse, UserRatingsResponse
from app.schemas.user import RegisterUserRequest, ResetRequest, VerifyUserRequest, EmailRequest, \
    FiltersForGenerationExampleRequest, AnswerToExample, ChangeName
from app.services import user
from app.config.security import get_current_user, oauth2_scheme
from app.services.user import get_top_users_by_difficulty

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

auth_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(get_current_user)]
)

guest_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)


@user_router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(data: RegisterUserRequest, background_tasks: BackgroundTasks,
                        session: Session = Depends(get_session)):
    return await user.create_user_account(data, session, background_tasks)


@user_router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_account(data: VerifyUserRequest, background_tasks: BackgroundTasks,
                              session: Session = Depends(get_session)):
    await user.activate_user_account(data, session, background_tasks)
    return JSONResponse({"message": "Account is activated successfully."})


@guest_router.post("/login", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def user_login(data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    return await user.get_login_token(data, session)


@guest_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_token(refresh_token=Header(), session: Session = Depends(get_session)):
    return await user.get_refresh_token(refresh_token, session)


@guest_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks,
                          session: Session = Depends(get_session)):
    await user.email_forgot_password_link(data, background_tasks, session)
    return JSONResponse({"message": "A email with password reset link has been sent to you."})


@guest_router.post("/get-example", status_code=status.HTTP_200_OK)
async def get_example(data: FiltersForGenerationExampleRequest):
    example, answer, difficulty = await user.get_example(data)
    return JSONResponse({"example": example, "correct_answer": str(answer), "difficulty": difficulty})


@guest_router.post("/get-answer", status_code=status.HTTP_200_OK)
async def check_answer(data: AnswerToExample, session: Session = Depends(get_session)):
    is_correct_answer = await user.check_example_answer(data, session)
    return JSONResponse({"message": is_correct_answer,
                         "correct_answer": data.correct_answer})


@guest_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: Session = Depends(get_session)):
    await user.reset_user_password(data, session)
    return JSONResponse({"message": "Your password has been updated."})


@guest_router.put("/{change-name}", status_code=status.HTTP_200_OK)
async def change_name(data: ChangeName, session: Session = Depends(get_session)):
    await user.change_user_name(data, session)
    return JSONResponse({"message": "Your name has been changed."})


@guest_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user=Depends(get_current_user)):
    return user


@guest_router.get("/ratings", status_code=status.HTTP_200_OK, response_model=Dict[str, List[UserRatingsResponse]])
async def read_top_users(session: Session = Depends(get_session)):
    return get_top_users_by_difficulty(session)


@guest_router.get("/{pk}", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user_info(pk, session: Session = Depends(get_session)):
    return await user.fetch_user_detail(pk, session)
