import re
import uuid
from datetime import datetime, timezone, timedelta

from chromadb.api.models.Collection import Collection

from app.models.user import User
from app.utils.security import hash_password, verify_password


def now_iso() -> str:
    # return datetime.utcnow().isoformat()
    # 东八区 = 北京时间
    beijing = timezone(timedelta(hours=8))
    return datetime.now(beijing).isoformat()


def _first_metadata(result: dict) -> dict:
    return ((result or {}).get("metadatas") or [None])[0] or {}


def get_user_by_username(users: Collection, username: str) -> User | None:
    result = users.get(where={"username": username}, include=["metadatas"])
    metadatas = (result or {}).get("metadatas") or []
    ids = (result or {}).get("ids") or []
    if not metadatas or not ids:
        return None
    metadata = metadatas[0]
    if int(metadata.get("is_deleted", 0)) == 1:
        return None
    return User(
        id=ids[0],
        username=metadata.get("username", ""),
        password_hash=metadata.get("password_hash", ""),
        nickname=metadata.get("nickname", ""),
        avatar=metadata.get("avatar", ""),
        role_id=metadata.get("role_id", ""),
        wallet_balance=float(metadata.get("wallet_balance", 0.0)),
        security_question=metadata.get("security_question", ""),
        security_answer_hash=metadata.get("security_answer_hash", ""),
        created_at=metadata.get("created_at", ""),
        updated_at=metadata.get("updated_at", ""),
        is_deleted=int(metadata.get("is_deleted", 0)),
    )


def get_role_by_code(roles: Collection, role_code: int) -> dict | None:
    result = roles.get(where={"code": role_code}, include=["metadatas"])
    metadata = _first_metadata(result)
    if not metadata or int(metadata.get("is_deleted", 0)) == 1:
        return None
    return metadata


def authenticate_user(users: Collection, username: str, password: str) -> User | None:
    user = get_user_by_username(users, username)
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def register_user(
    users: Collection,
    roles: Collection,
    username: str,
    password: str,
    nickname: str,
    avatar: str,
    role_code: int,
    security_question: str,
    security_answer: str,
    initial_wallet_balance: float,
) -> tuple[bool, str, str | None, int | None]:
    existing = get_user_by_username(users, username)
    if existing:
        return False, "用户名已存在", None, None
    role = get_role_by_code(roles, role_code)
    if not role:
        return False, "角色不存在", None, None
    now = now_iso()
    user_id = str(uuid.uuid4())
    users.add(
        ids=[user_id],
        metadatas=[
            {
                "id": user_id,
                "username": username,
                "password_hash": hash_password(password),
                "nickname": nickname or username,
                "avatar": avatar or "",
                "role_id": role.get("id", ""),
                "wallet_balance": float(initial_wallet_balance),
                "security_question": security_question,
                "security_answer_hash": hash_password(security_answer),
                "created_at": now,
                "updated_at": now,
                "is_deleted": 0,
            }
        ],
        documents=["user"],
    )
    return True, "注册成功", user_id, role_code


def reset_password_by_security_answer(
    users: Collection, username: str, security_answer: str, new_password: str
) -> tuple[bool, str]:
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    if not verify_password(security_answer, user.security_answer_hash):
        return False, "密保答案错误"
    users.update(
        ids=[user.id],
        metadatas=[
            {
                "id": user.id,
                "username": user.username,
                "password_hash": hash_password(new_password),
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role_id": user.role_id,
                "wallet_balance": user.wallet_balance,
                "security_question": user.security_question,
                "security_answer_hash": user.security_answer_hash,
                "created_at": user.created_at,
                "updated_at": now_iso(),
                "is_deleted": user.is_deleted,
            }
        ],
        documents=["user"],
    )
    return True, "密码重置成功"


def get_security_question(users: Collection, username: str) -> tuple[bool, str, str | None]:
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在", None
    if not user.security_question:
        return False, "未设置密保问题", None
    return True, "获取成功", user.security_question


def parse_amount_from_text(text: str) -> float:
    match = re.search(r"(-?\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else 0.0

