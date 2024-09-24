from pydantic import BaseModel, EmailStr


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyUserRequest(BaseModel):
    token: str
    email: EmailStr


class EmailRequest(BaseModel):
    email: EmailStr


class ResetRequest(BaseModel):
    token: str
    email: EmailStr
    password: str


class ChangeName(BaseModel):
    email: EmailStr
    name: str


class FiltersForGenerationExampleRequest(BaseModel):
    example_type: str = None
    difficulty: int = None
    operations: str = None


class AnswerToExample(BaseModel):
    email: EmailStr
    difficulty: int
    user_answer: str
    correct_answer: str
