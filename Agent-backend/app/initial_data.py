import chromadb

from app.config import settings
from app.services.auth_service import now_iso
from app.utils.security import hash_password


def init_db() -> None:
    client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
    users = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_USERS)
    roles = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_ROLES)
    permissions = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_PERMISSIONS)
    role_permissions = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_ROLE_PERMISSIONS)
    client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHATS)
    client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHAT_THREADS)
    client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHAT_MESSAGES)
    client.get_or_create_collection(name=settings.CHROMA_COLLECTION_BILLS)

    role_seed = [
        {"id": "1", "code": 1, "name": "normal_user"},
        {"id": "2", "code": 2, "name": "vip_user"},
        {"id": "3", "code": 3, "name": "svip_user"},
    ]
    for role in role_seed:
        existing = roles.get(ids=[role["id"]], include=["metadatas"])
        if existing and existing.get("ids"):
            continue
        roles.add(
            ids=[role["id"]],
            metadatas=[
                {
                    **role,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "is_deleted": 0,
                }
            ],
            documents=["role"],
        )

    permission_seed = [
        {"id": "p1", "permission_key": "chat_text", "name": "对话"},
        {"id": "p2", "permission_key": "advanced_model", "name": "使用高级模型"},
        {"id": "p3", "permission_key": "report_week_month", "name": "生成周/月账单报告"},
        {"id": "p4", "permission_key": "export_report", "name": "导出账单报告"},
        {"id": "p5", "permission_key": "ocr_bill_adjust", "name": "账单/图片识别增减金额"},
        {"id": "p6", "permission_key": "custom_report", "name": "自定义时间段报告"},
        {"id": "p7", "permission_key": "manage_wallet", "name": "钱包管理"},
        {"id": "p8", "permission_key": "history_manage", "name": "历史对话管理"},
        {"id": "p9", "permission_key": "view_bill", "name": "账单查看"},
    ]
    for permission in permission_seed:
        existing = permissions.get(ids=[permission["id"]], include=["metadatas"])
        if existing and existing.get("ids"):
            continue
        permissions.add(
            ids=[permission["id"]],
            metadatas=[
                {
                    **permission,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "is_deleted": 0,
                }
            ],
            documents=["permission"],
        )

    role_permission_map = {
        "1": {"chat_text", "manage_wallet", "history_manage", "view_bill"},
        "2": {
            "chat_text",
            "manage_wallet",
            "history_manage",
            "view_bill",
            "advanced_model",
            "report_week_month",
            "ocr_bill_adjust",
        },
        "3": {
            "chat_text",
            "manage_wallet",
            "history_manage",
            "view_bill",
            "advanced_model",
            "report_week_month",
            "ocr_bill_adjust",
            "custom_report",
            "export_report",
        },
    }
    for role_id, permission_keys in role_permission_map.items():
        for permission_key in permission_keys:
            mapping_id = f"{role_id}_{permission_key}"
            existing = role_permissions.get(ids=[mapping_id], include=["metadatas"])
            if existing and existing.get("ids"):
                continue
            role_permissions.add(
                ids=[mapping_id],
                metadatas=[
                    {
                        "id": mapping_id,
                        "role_id": role_id,
                        "permission_key": permission_key,
                        "created_at": now_iso(),
                        "updated_at": now_iso(),
                        "is_deleted": 0,
                    }
                ],
                documents=["role_permission"],
            )

    username = "test"
    existing = users.get(where={"username": username}, include=["metadatas"])
    if existing and existing.get("ids"):
        return

    user_id = "u_test"
    users.add(
        ids=[user_id],
        metadatas=[
            {
                "id": user_id,
                "username": username,
                "password_hash": hash_password("123456"),
                "nickname": "测试用户",
                "avatar": "",
                "role_id": "1",
                "wallet_balance": 1000.0,
                "bank_balance": 5678.9,
                "debt_amount": 100.0,
                "security_question": "你的宠物名字?",
                "security_answer_hash": hash_password("tom"),
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "is_deleted": 0,
            }
        ],
        documents=["user"],
    )


if __name__ == "__main__":
    init_db()
    print("Initialized database with default user: test / 123456, answer: tom")

