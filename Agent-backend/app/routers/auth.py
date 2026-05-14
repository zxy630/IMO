from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, Request, UploadFile
from chromadb.api.models.Collection import Collection
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import settings
from app.database import get_roles_collection, get_users_collection
from app.schemas.auth import (
    GetSecurityQuestionRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SecurityQuestionResponse,
)
from app.services.auth_service import (
    authenticate_user,
    get_security_question,
    register_user,
    reset_password_by_security_answer,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, users: Collection = Depends(get_users_collection)) -> LoginResponse:
    user = authenticate_user(users, payload.username, payload.password)
    if not user:
        return LoginResponse(success=False, message="用户名或密码错误")
    return LoginResponse(
        success=True,
        message="登录成功",
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar,
        user_id=user.id,
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    request: Request,
    users: Collection = Depends(get_users_collection),
    roles: Collection = Depends(get_roles_collection),
) -> LoginResponse:
    content_type = request.headers.get("content-type", "")
    payload_data: dict = {}

    if "multipart/form-data" in content_type:
        form = await request.form()
        avatar_url = ""
        avatar_obj = form.get("avatar")
        if isinstance(avatar_obj, (UploadFile, StarletteUploadFile)) and avatar_obj.filename:
            avatar_url = await _save_avatar_file(avatar_obj)
        payload_data = {
            "username": str(form.get("username", "")),
            "password": str(form.get("password", "")),
            "nickname": str(form.get("nickname", "")),
            "avatar": avatar_url,
            "security_question": str(form.get("security_question", "")),
            "security_answer": str(form.get("security_answer", "")),
            "role_code": int(str(form.get("role_code", "1"))),
            "initial_wallet_balance": float(str(form.get("initial_wallet_balance", "0"))),
        }
    else:
        payload_json = await request.json()
        payload_data = dict(payload_json or {})

    payload = RegisterRequest(**payload_data)
    ok, message, user_id, role_code = register_user(
        users=users,
        roles=roles,
        username=payload.username,
        password=payload.password,
        nickname=payload.nickname,
        avatar=payload.avatar,
        role_code=payload.role_code,
        security_question=payload.security_question,
        security_answer=payload.security_answer,
        initial_wallet_balance=payload.initial_wallet_balance,
    )
    if not ok:
        return LoginResponse(success=False, message=message)
    return LoginResponse(
        success=True,
        message=message,
        username=payload.username,
        nickname=payload.nickname or payload.username,
        avatar=payload.avatar,
        user_id=user_id,
        role_code=role_code,
    )


async def _save_avatar_file(avatar_file: UploadFile) -> str:
    settings.AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(avatar_file.filename).suffix or ".png"
    filename = f"{uuid.uuid4().hex}{suffix}"
    target_path = settings.AVATAR_UPLOAD_DIR / filename
    content = await avatar_file.read()
    with open(target_path, "wb") as f:
        f.write(content)
    return f"/uploads/avatars/{filename}"


@router.post("/reset-password", response_model=LoginResponse)
def reset_password(
    payload: ResetPasswordRequest, users: Collection = Depends(get_users_collection)
) -> LoginResponse:
    ok, message = reset_password_by_security_answer(
        users, payload.username, payload.security_answer, payload.new_password
    )
    if not ok:
        return LoginResponse(success=False, message=message)
    return LoginResponse(success=True, message=message, username=payload.username)


@router.post("/get-security-question", response_model=SecurityQuestionResponse)
def get_security_question_api(
    payload: GetSecurityQuestionRequest, users: Collection = Depends(get_users_collection)
) -> SecurityQuestionResponse:
    ok, message, security_question = get_security_question(users, payload.username)
    if not ok:
        return SecurityQuestionResponse(success=False, message=message, username=payload.username)
    return SecurityQuestionResponse(
        success=True,
        message=message,
        username=payload.username,
        security_question=security_question,
    )

