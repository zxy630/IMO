from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    username: str
    password_hash: str
    nickname: str
    avatar: str
    role_id: str
    wallet_balance: float
    security_question: str
    security_answer_hash: str
    created_at: str
    updated_at: str
    is_deleted: int

