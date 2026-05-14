from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""
    avatar: str = ""
    security_question: str
    security_answer: str
    role_code: int = Field(default=1, ge=1, le=3)
    initial_wallet_balance: float = 0.0


class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str


class GetSecurityQuestionRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    username: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    user_id: str | None = None
    role_code: int | None = None


class SecurityQuestionResponse(BaseModel):
    success: bool
    message: str
    username: str | None = None
    security_question: str | None = None

