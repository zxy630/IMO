import re

from fastapi import APIRouter, Depends, Header, Query, UploadFile, File, Form
from chromadb.api.models.Collection import Collection

from app.database import (
    get_bills_collection,
    get_chat_messages_collection,
    get_chat_threads_collection,
    get_chats_collection,
    get_roles_collection,
    get_role_permissions_collection,
    get_users_collection,
)
from app.schemas.billing import (
    BillItemResponse, 
    ExportReportRequest, 
    GenerateReportRequest,
    ParseBillImageResponse,
    BillListResponse,
    BillReportResponse,
    BillDetailItem
)
from app.schemas.chat import (
    BillImageAdjustRequest,
    ChatMessageItemResponse,
    ChatSendResponse,
    ChatThreadItemResponse,
    LatestChatResponse,
    ChatRecordResponse,
    SendTextRequest,
    TextAmountAdjustRequest,
)
from app.schemas.user import ChangePasswordRequest, UpdateProfileRequest, UpdateProfileNewRequest, UpdateProfileResponse, MembershipStatusResponse, MembershipUpgradeRequest, MembershipUpgradeResponse, UserProfileResponse, UserProfileSimpleResponse, WalletData, WalletResponse
from app.services.app_service import (
    add_chat_message,
    change_password,
    create_chat,
    create_chat_thread,
    detect_wallet_adjustment,
    filter_bill_records,
    generate_bill_report,
    get_latest_chat_thread,
    list_chat_threads,
    list_thread_messages,
    list_user_active_metadatas,
    require_permission,
    soft_delete_record,
    update_user_profile,
    wallet_adjust_by_amount,
    wallet_adjust_by_text,
    wallet_adjust_repayment,
)
from app.services.auth_service import get_user_by_username, get_role_by_code, now_iso
from app.services.llm_service import chat_with_model, get_model_provider
from app.services.bill_parser_service import (
    encode_image_to_base64,
    normalize_amount,
    parse_bill_image_with_dashscope,
    create_bill_record,
    list_user_bills,
    calculate_bill_summary,
    update_user_wallet_from_bill
)
from app.config import settings

router = APIRouter(prefix="/user", tags=["user"])
NORMAL_ROLE_BASIC_MODELS = {"qwen-turbo"}
ROLE_MODEL_PROVIDERS = {
    1: {"qwen"},
    2: {"qwen", "deepseek"},
    3: {"qwen", "deepseek", "gpt"},
}


def _get_username(
    x_username: str | None = Header(default=None),
    username: str | None = Query(default=None),
) -> str:
    # 兼容：前端既可以通过 Header 传，也可以通过 Query 传
    return (x_username or username or "").strip()


def _get_role_code(roles: Collection, role_id: str) -> int:
    result = roles.get(ids=[role_id], include=["metadatas"])
    metadata = ((result or {}).get("metadatas") or [None])[0] or {}
    return int(metadata.get("code", 1))


def _can_use_chat_model(roles: Collection, role_id: str, model: str) -> tuple[bool, str]:
    provider = get_model_provider(model)
    if provider == "unknown":
        return False, f"不支持的模型: {model}"

    role_code = _get_role_code(roles, role_id)
    allowed_providers = ROLE_MODEL_PROVIDERS.get(role_code, {"qwen"})
    if provider not in allowed_providers:
        if provider == "deepseek":
            return False, "DeepSeek 模型仅 VIP/SVIP 用户可用"
        if provider == "gpt":
            return False, "GPT 模型仅 SVIP 用户可用"
        return False, "当前角色无该模型调用权限"

    if role_code == 1 and model not in NORMAL_ROLE_BASIC_MODELS:
        return False, "普通用户仅可使用 qwen-turbo"

    return True, ""


@router.get("/profile", response_model=UserProfileSimpleResponse)
def get_profile(
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    roles: Collection = Depends(get_roles_collection),
):
    user = get_user_by_username(users, username)
    if not user:
        return UserProfileSimpleResponse(
            success=False,
            message="用户不存在",
            data=None
        )
    
    # 获取角色信息来判断是否为会员
    role_result = roles.get(ids=[user.role_id], include=["metadatas"])
    role_metadata = ((role_result or {}).get("metadatas") or [None])[0] or {}
    role_code = int(role_metadata.get("code", 1))
    
    # 会员判断：role_code > 1 为会员
    is_member = role_code > 1
    
    return UserProfileSimpleResponse(
        success=True,
        data={
            "nickname": user.nickname,
            "avatar": user.avatar,
            "is_member": is_member
        }
    )


@router.get("/membership/status", response_model=MembershipStatusResponse)
def get_membership_status(
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    roles: Collection = Depends(get_roles_collection),
):
    user = get_user_by_username(users, username)
    if not user:
        return MembershipStatusResponse(
            success=False,
            role_code=None,
            message="用户不存在"
        )

    role_result = roles.get(ids=[user.role_id], include=["metadatas"])
    role_metadata = ((role_result or {}).get("metadatas") or [None])[0] or {}
    role_code = int(role_metadata.get("code", 1))
    
    return MembershipStatusResponse(
        success=True,
        role_code=role_code,
        message=""
    )


@router.post("/membership/upgrade", response_model=MembershipUpgradeResponse)
def upgrade_membership(
    payload: MembershipUpgradeRequest,
    username_header: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    roles: Collection = Depends(get_roles_collection),
):
    import logging
    
    logging.info(f"会员升级请求 - 请求头用户名: {username_header}, 请求体用户名: {payload.username}")
    
    # 验证请求头中的用户名与请求体中的用户名一致
    if username_header != payload.username:
        logging.warning(f"用户名不匹配 - 请求头: {username_header}, 请求体: {payload.username}")
        return MembershipUpgradeResponse(
            success=False,
            message="请求头用户名与请求体用户名不匹配",
            role_code=None
        )
    
    # 获取用户信息
    user = get_user_by_username(users, payload.username)
    if not user:
        logging.warning(f"用户不存在: {payload.username}")
        return MembershipUpgradeResponse(
            success=False,
            message="用户不存在",
            role_code=None
        )
    
    # 获取当前角色信息
    role_result = roles.get(ids=[user.role_id], include=["metadatas"])
    role_metadata = ((role_result or {}).get("metadatas") or [None])[0] or {}
    current_role_code = int(role_metadata.get("code", 1))
    
    logging.info(f"当前角色代码: {current_role_code}")
    
    # 检查是否已是顶级会员
    if current_role_code >= 3:
        logging.info(f"已是顶级会员: {payload.username}")
        return MembershipUpgradeResponse(
            success=False,
            message="已是svip顶级会员",
            role_code=current_role_code
        )
    
    # 计算新角色代码
    new_role_code = current_role_code + 1
    if new_role_code > 3:
        new_role_code = 3
    
    # 获取新角色ID
    new_role = get_role_by_code(roles, new_role_code)
    if not new_role:
        logging.error(f"新角色不存在: {new_role_code}")
        return MembershipUpgradeResponse(
            success=False,
            message="系统错误，无法升级",
            role_code=current_role_code
        )
    
    # 更新用户角色
    users.update(
        ids=[user.id],
        metadatas=[{
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "role_id": new_role["id"],
            "wallet_balance": user.wallet_balance,
            "security_question": user.security_question,
            "security_answer_hash": user.security_answer_hash,
            "created_at": user.created_at,
            "updated_at": now_iso(),
            "is_deleted": user.is_deleted,
        }],
        documents=["user"]
    )
    
    logging.info(f"会员升级成功 - 用户名: {payload.username}, 从 {current_role_code} 升级到 {new_role_code}")
    
    return MembershipUpgradeResponse(
        success=True,
        message="升级成功",
        role_code=new_role_code
    )


@router.get("/wallet", response_model=WalletResponse)
def get_wallet(
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
):
    if not username:
        return WalletResponse(success=False, message="缺少用户名")

    user = get_user_by_username(users, username)
    if not user:
        return WalletResponse(success=False, message="用户不存在")

    result = users.get(ids=[user.id], include=["metadatas"])
    metadata = ((result or {}).get("metadatas") or [None])[0] or {}

    cash_balance = float(metadata.get("wallet_balance", 0.0))
    bank_balance = float(metadata.get("bank_balance", 0.0))
    debt_amount = float(metadata.get("debt_amount", 0.0))

    return WalletResponse(
        success=True,
        message="ok",
        data=WalletData(
            cash_balance=cash_balance,
            bank_balance=bank_balance,
            debt_amount=debt_amount,
        ),
    )


@router.put("/profile")
def put_profile(
    payload: UpdateProfileRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
):
    ok, message = update_user_profile(users, username, payload.nickname, payload.avatar)
    return {"success": ok, "message": message}


@router.post("/profile/update", response_model=UpdateProfileResponse)
def update_profile(
    payload: UpdateProfileNewRequest,
    username_header: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
):
    import logging
    logging.info(f"用户资料更新请求 - 请求头用户名: {username_header}, 请求体用户名: {payload.username}, 昵称: {payload.nickname}, 头像: {payload.avatar}")
    
    # 验证请求头中的用户名与请求体中的用户名一致
    if username_header != payload.username:
        logging.warning(f"用户名不匹配 - 请求头: {username_header}, 请求体: {payload.username}")
        return UpdateProfileResponse(
            success=False,
            message="请求头用户名与请求体用户名不匹配",
            data=None
        )
    
    # 调用现有的更新函数
    ok, message = update_user_profile(users, payload.username, payload.nickname, payload.avatar)
    
    if ok:
        logging.info(f"用户资料更新成功 - 用户名: {payload.username}, 昵称: {payload.nickname}, 头像: {payload.avatar}")
        # 如果有头像，返回头像信息
        data = {}
        if payload.avatar:
            data["avatar"] = payload.avatar
        return UpdateProfileResponse(
            success=True,
            data=data if data else None,
            message="资料更新成功"
        )
    else:
        logging.error(f"用户资料更新失败 - 用户名: {payload.username}, 错误: {message}")
        return UpdateProfileResponse(
            success=False,
            message=message,
            data=None
        )


@router.put("/password")
def put_password(
    payload: ChangePasswordRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
):
    ok, message = change_password(users, username, payload.old_password, payload.new_password)
    return {"success": ok, "message": message}


@router.post("/chat/send")
def send_text_message(
    payload: SendTextRequest,
    username_header: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    roles: Collection = Depends(get_roles_collection),
    role_permissions: Collection = Depends(get_role_permissions_collection),
    chats: Collection = Depends(get_chats_collection),
    threads: Collection = Depends(get_chat_threads_collection),
    messages: Collection = Depends(get_chat_messages_collection),
    bills: Collection = Depends(get_bills_collection),
):
    # 统一用户名来源：优先用 Header/Query，其次才用 body
    username = (username_header or payload.username or "").strip()
    if not username:
        return ChatSendResponse(success=False, message="缺少用户名（请传 X-Username 或 body.username）")
    user = get_user_by_username(users, username)
    if not user:
        return ChatSendResponse(success=False, message="用户不存在")
    can_use_model, model_error = _can_use_chat_model(roles, user.role_id, payload.model)
    if not can_use_model:
        return ChatSendResponse(success=False, message=model_error)
    if payload.model not in NORMAL_ROLE_BASIC_MODELS and not require_permission(
        role_permissions, user.role_id, "advanced_model"
    ):
        return ChatSendResponse(success=False, message="当前角色无高级模型调用权限")

    thread_id = payload.thread_id
    should_seed_greeting = bool(payload.new_chat or not thread_id)
    if should_seed_greeting:
        title = payload.message[:20] if payload.message else "新对话"
        thread_meta = create_chat_thread(threads, username, title=title)
        thread_id = thread_meta["thread_id"]

    greeting_message = (payload.greeting_message or "").strip()
    if should_seed_greeting and greeting_message:
        add_chat_message(messages, threads, thread_id, username, "assistant", greeting_message, payload.model)

    user_mid = add_chat_message(messages, threads, thread_id, username, "user", payload.message, payload.model)

    # 检测报告请求
    import re
    report_match = re.search(r"(生成|给我|查看).*?(?:最近|近|过去)?(.+?)(?:的)?(报告|账单|统计)", payload.message)
    if report_match:
        period = report_match.group(2) or "一个月"
        answer = generate_bill_report(bills, username, period)
    else:
        # 检测钱包调整
        wallet_adjusted = False
        wallet_message = ""
        detected, amount, source_desc, balance_type = detect_wallet_adjustment(payload.message)
        if detected:
            if source_desc.endswith("_repayment"):
                # 还款操作
                ok, msg = wallet_adjust_repayment(users, bills, username, amount, source_desc, payload.message)
            else:
                # 普通调整
                ok, msg = wallet_adjust_by_amount(users, bills, username, amount, source_desc, payload.message, balance_type)
            if ok:
                wallet_adjusted = True
                wallet_message = f"已帮您记录：{msg}。"
            else:
                wallet_message = f"记录失败：{msg}。"

        try:
            answer = chat_with_model(payload.model, payload.message)
        except Exception as exc:
            error_answer = f"模型调用失败: {exc}"
            assistant_mid = add_chat_message(messages, threads, thread_id, username, "assistant", error_answer, payload.model)
            create_chat(chats, username, payload.model, payload.message, error_answer)
            return ChatSendResponse(
                success=False,
                message=error_answer,
                thread_id=thread_id,
                user_message_id=user_mid,
                assistant_message_id=assistant_mid,
                answer=error_answer,
                model=payload.model,
            )

        if wallet_adjusted:
            answer = f"{wallet_message}\n\n{answer}"

    assistant_mid = add_chat_message(messages, threads, thread_id, username, "assistant", answer, payload.model)

    # legacy：仍写入旧表，保证老接口 `/user/chats` 可用
    create_chat(chats, username, payload.model, payload.message, answer)

    return ChatSendResponse(
        success=True,
        message="发送成功",
        thread_id=thread_id,
        user_message_id=user_mid,
        assistant_message_id=assistant_mid,
        answer=answer,
        model=payload.model,
    )


@router.get("/chat/latest", response_model=LatestChatResponse | None)
def get_latest_thread(
    username: str = Depends(_get_username),
    threads: Collection = Depends(get_chat_threads_collection),
    messages: Collection = Depends(get_chat_messages_collection),
):
    meta = get_latest_chat_thread(threads, username)
    if not meta:
        return None
    thread_id = meta.get("thread_id", "")
    items = list_thread_messages(messages, username, thread_id)
    msg_list = [
        ChatMessageItemResponse(
            message_id=m.get("message_id", ""),
            thread_id=m.get("thread_id", ""),
            role=m.get("role", ""),
            content=m.get("content", ""),
            model=m.get("model") or m.get("model_id", ""),
            created_at=m.get("created_at", ""),
        )
        for m in items
    ]
    return LatestChatResponse(
        thread_id=thread_id,
        title=meta.get("title", ""),
        updated_at=meta.get("updated_at", ""),
        messages=msg_list,
    )


@router.get("/chat/threads", response_model=list[ChatThreadItemResponse])
def get_threads(username: str = Depends(_get_username), threads: Collection = Depends(get_chat_threads_collection)):
    items = list_chat_threads(threads, username)
    return [
        ChatThreadItemResponse(
            thread_id=m.get("thread_id", ""),
            title=m.get("title", ""),
            last_message=m.get("last_message", ""),
            updated_at=m.get("updated_at", ""),
        )
        for m in items
    ]


@router.get("/chat/threads/{thread_id}/messages", response_model=list[ChatMessageItemResponse])
def get_thread_messages(
    thread_id: str,
    username: str = Depends(_get_username),
    messages: Collection = Depends(get_chat_messages_collection),
):
    items = list_thread_messages(messages, username, thread_id)
    return [
        ChatMessageItemResponse(
            message_id=m.get("message_id", ""),
            thread_id=m.get("thread_id", ""),
            role=m.get("role", ""),
            content=m.get("content", ""),
            model=m.get("model") or m.get("model_id", ""),
            created_at=m.get("created_at", ""),
        )
        for m in items
    ]


@router.post("/wallet/adjust-by-text")
def adjust_wallet_by_text(
    payload: TextAmountAdjustRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    bills: Collection = Depends(get_bills_collection),
):
    ok, message = wallet_adjust_by_text(users, bills, username, payload.text, source="text")
    return {"success": ok, "message": message}


@router.post("/wallet/adjust-by-bill-image")
def adjust_wallet_by_bill_image(
    payload: BillImageAdjustRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    role_permissions: Collection = Depends(get_role_permissions_collection),
    bills: Collection = Depends(get_bills_collection),
):
    user = get_user_by_username(users, username)
    if not user:
        return {"success": False, "message": "用户不存在"}
    if not require_permission(role_permissions, user.role_id, "ocr_bill_adjust"):
        return {"success": False, "message": "当前角色无票据图片识别记账权限"}
    ok, message = wallet_adjust_by_text(users, bills, username, payload.image_text, source="bill_image")
    return {"success": ok, "message": message}


@router.post("/avatar/upload")
def upload_avatar(
    file: UploadFile = File(...),
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
):
    import logging
    import uuid
    from pathlib import Path
    
    logging.info(f"头像上传请求 - 用户名: {username}, 文件名: {file.filename}")
    
    # 验证用户是否存在
    user = get_user_by_username(users, username)
    if not user:
        logging.warning(f"头像上传失败 - 用户不存在: {username}")
        return {"success": False, "message": "用户不存在"}
    
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        logging.warning(f"头像上传失败 - 无效文件类型: {file.content_type}")
        return {"success": False, "message": "只允许上传图片文件"}
    
    # 验证文件大小（限制为5MB）
    file_size = 0
    content = file.file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        logging.warning(f"头像上传失败 - 文件过大: {file_size} bytes")
        return {"success": False, "message": "文件大小不能超过5MB"}
    
    # 生成唯一文件名
    file_extension = Path(file.filename).suffix.lower()
    if not file_extension:
        file_extension = ".jpg"  # 默认扩展名
    
    unique_filename = f"{username}_{uuid.uuid4().hex}{file_extension}"
    file_path = settings.AVATAR_UPLOAD_DIR / unique_filename
    
    try:
        # 确保上传目录存在
        settings.AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 生成访问URL
        avatar_url = f"/uploads/avatars/{unique_filename}"
        
        logging.info(f"头像上传成功 - 用户名: {username}, 文件: {unique_filename}, URL: {avatar_url}")
        
        return {
            "success": True,
            "message": "头像上传成功",
            "data": {
                "avatar": avatar_url
            }
        }
        
    except Exception as e:
        logging.error(f"头像上传失败 - 用户名: {username}, 错误: {str(e)}")
        return {"success": False, "message": f"文件保存失败: {str(e)}"}


@router.get("/chats", response_model=list[ChatRecordResponse])
def list_chats(username: str = Depends(_get_username), chats: Collection = Depends(get_chats_collection)):
    return [
        ChatRecordResponse(
            id=m.get("id", ""),
            username=m.get("username", ""),
            model_name=m.get("model_name", ""),
            message=m.get("message", ""),
            answer=m.get("answer", ""),
            created_at=m.get("created_at", ""),
        )
        for m in list_user_active_metadatas(chats, username)
    ]


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, username: str = Depends(_get_username), chats: Collection = Depends(get_chats_collection)):
    result = chats.get(ids=[chat_id], include=["metadatas"])
    metadatas = (result or {}).get("metadatas") or []
    if not metadatas:
        return {"success": False, "message": "对话不存在"}
    metadata = metadatas[0]
    if metadata.get("username") != username:
        return {"success": False, "message": "无权删除"}
    soft_delete_record(chats, chat_id, metadata)
    return {"success": True, "message": "删除成功"}


@router.get("/bills", response_model=list[BillItemResponse])
def list_bills(username: str = Depends(_get_username), bills: Collection = Depends(get_bills_collection)):
    return [
        BillItemResponse(
            id=m.get("id", ""),
            username=m.get("username", ""),
            change_amount=float(m.get("change_amount", 0.0)),
            source=m.get("source", ""),
            note=m.get("note", ""),
            created_at=m.get("created_at", ""),
        )
        for m in list_user_active_metadatas(bills, username)
    ]


@router.post("/bills/report")
def generate_report(
    payload: GenerateReportRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    role_permissions: Collection = Depends(get_role_permissions_collection),
    bills: Collection = Depends(get_bills_collection),
):
    user = get_user_by_username(users, username)
    if not user:
        return {"success": False, "message": "用户不存在"}
    if payload.period_type in {"week", "month"}:
        if not require_permission(role_permissions, user.role_id, "report_week_month"):
            return {"success": False, "message": "当前角色无周/月报表权限"}
    if payload.period_type == "custom":
        if not require_permission(role_permissions, user.role_id, "custom_report"):
            return {"success": False, "message": "当前角色无自定义时间报表权限"}
    records = list_user_active_metadatas(bills, username)
    filtered = filter_bill_records(records, payload.period_type, payload.start_time, payload.end_time)
    total = sum(float(r.get("change_amount", 0.0)) for r in filtered)
    return {"success": True, "period_type": payload.period_type, "count": len(filtered), "sum_amount": total}


@router.post("/bills/report/export")
def export_report(
    payload: ExportReportRequest,
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    role_permissions: Collection = Depends(get_role_permissions_collection),
):
    user = get_user_by_username(users, username)
    if not user:
        return {"success": False, "message": "用户不存在"}
    if not require_permission(role_permissions, user.role_id, "export_report"):
        return {"success": False, "message": "当前角色无导出权限"}
    if payload.export_type not in {"excel", "pdf"}:
        return {"success": False, "message": "仅支持excel/pdf导出"}
    return {"success": True, "message": f"已生成{payload.export_type}导出任务（示例实现）"}


# ============ 图片账单解析接口 ============

@router.post("/bills/parse-image", response_model=ParseBillImageResponse)
def parse_bill_image(
    file: UploadFile = File(...),
    greeting_message: str | None = Form(None),
    thread_id: str = Query(None, description="当前对话线程ID，如果不传则使用最新对话"),
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    bills: Collection = Depends(get_bills_collection),
    threads: Collection = Depends(get_chat_threads_collection),
    messages: Collection = Depends(get_chat_messages_collection),
):
    """
    上传账单截图并进行智能解析
    
    支持格式：
    - 支付宝花呗付款截图
    - 微信支付/零钱账单截图
    - 其他常见支付凭证
    
    返回格式：
    {
        "success": bool,
        "message": "处理信息",
        "bill_id": "账单ID",
        "parsed_data": {解析后的账单数据},
        "wallet_balance": 更新后的钱包余额
    }
    """
    import logging
    import tempfile
    from pathlib import Path
    
    logging.info(f"收到图片处理请求 - 用户名: {username}, 文件名: {file.filename}")
    logging.info("开始处理账单图片上传请求")
    
    try:
        # 验证用户存在
        user = get_user_by_username(users, username)
        if not user:
            logging.warning(f"用户不存在: {username}")
            return ParseBillImageResponse(
                success=False,
                message="用户不存在",
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 验证文件类型
        if not file.filename:
            return ParseBillImageResponse(
                success=False,
                message="文件名无效",
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        if file_ext not in allowed_extensions:
            logging.warning(f"不支持的文件格式: {file_ext}")
            return ParseBillImageResponse(
                success=False,
                message=f"不支持的文件格式，请上传图片文件",
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 读取文件内容
        content = file.file.read()
        file_size = len(content)
        logging.info(f"上传文件大小: {file_size} bytes")
        
        # 验证文件大小（最大10MB）
        if file_size > 10 * 1024 * 1024:
            logging.warning(f"文件过大: {file_size} bytes")
            return ParseBillImageResponse(
                success=False,
                message="文件大小不能超过10MB",
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 保存临时文件进行解析
        settings.BILL_IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        import uuid
        unique_filename = f"{username}_{uuid.uuid4().hex}{file_ext}"
        file_path = settings.BILL_IMAGE_UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 生成图片访问URL
        image_url = f"/uploads/bills/{unique_filename}"
        
        # 编码为Base64
        image_base64 = encode_image_to_base64(str(file_path))
        
        # 使用AI解析图片
        logging.info(f"开始解析图片: {unique_filename}")
        parse_result = parse_bill_image_with_dashscope(image_base64)
        
        if not parse_result.get("success"):
            logging.warning(f"图片解析失败: {parse_result.get('message')}")
            return ParseBillImageResponse(
                success=False,
                message=parse_result.get("message", "图片解析失败"),
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 获取解析后的数据
        parsed_data = parse_result.get("data", {})
        logging.info(f"AI解析结果: {parsed_data}")
        
        # 规范化金额字段，支持带符号或中文单位的值
        parsed_data["amount"] = normalize_amount(parsed_data.get("amount", 0))
        parsed_data["actual_amount"] = normalize_amount(parsed_data.get("actual_amount", parsed_data["amount"]))
        if parsed_data["amount"] == 0 and parsed_data["actual_amount"] != 0:
            parsed_data["amount"] = parsed_data["actual_amount"]
        parsed_data["transaction_type"] = (parsed_data.get("transaction_type", "expense") or "expense").lower()
        
        # 检查关键字段
        if parsed_data.get("amount", 0) == 0:
            logging.warning(f"AI未能识别金额: {parsed_data}")
            return ParseBillImageResponse(
                success=False,
                message="未能识别账单中的金额，请确保图片清晰且包含金额信息",
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 创建账单记录
        success, message, bill_id = create_bill_record(
            bills=bills,
            username=username,
            parsed_data=parsed_data,
            image_path=str(file_path)
        )
        
        if not success:
            logging.error(f"账单创建失败: {message}")
            return ParseBillImageResponse(
                success=False,
                message=message,
                bill_id=None,
                parsed_data=None,
                wallet_balance=None
            )
        
        # 根据账单金额和账户类型更新用户余额
        bill_amount = float(parsed_data.get("amount", 0))
        if parsed_data.get("transaction_type") == "expense":
            bill_amount = -abs(bill_amount)
        else:
            bill_amount = abs(bill_amount)
        
        account_type = parsed_data.get("account_type", "")
        wallet_success, wallet_message = update_user_wallet_from_bill(
            users=users,
            username=username,
            bill_amount=bill_amount,
            account_type=account_type
        )
        
        # 获取更新后的用户信息
        updated_user = get_user_by_username(users, username)
        
        # 创建对话记录
        thread_id_to_use = thread_id
        chat_messages = []
        try:
            should_seed_greeting = False
            # 如果没有传入 thread_id，就新建一个会话线程
            if not thread_id_to_use:
                thread_title = f"账单解析-{now_iso()[:10]}"
                thread_meta = create_chat_thread(threads, username, title=thread_title)
                thread_id_to_use = thread_meta["thread_id"]
                should_seed_greeting = True
                logging.info(f"创建新对话线程: {thread_id_to_use}")
            else:
                logging.info(f"使用指定的对话线程: {thread_id_to_use}")
                should_seed_greeting = not list_thread_messages(messages, username, thread_id_to_use)

            greeting_content = (greeting_message or "").strip()
            if should_seed_greeting and greeting_content:
                add_chat_message(messages, threads, thread_id_to_use, username, "assistant", greeting_content, "bill_parser")
                chat_messages.append({"role": "assistant", "content": greeting_content})
            
            # 添加用户消息（图片上传）
            user_message = f"![账单图片]({image_url})\n\n上传了账单图片进行解析：{file.filename}"
            add_chat_message(messages, threads, thread_id_to_use, username, "user", user_message, "bill_parser")
            chat_messages.append({"role": "user", "content": user_message})
            
            # 添加助手消息（解析结果）
            assistant_message = f"""账单解析完成！

📊 解析结果：
- 交易时间：{parsed_data.get('transaction_time', '未知')}
- 商户名称：{parsed_data.get('merchant_name', '未知')}
- 金额：¥{parsed_data.get('amount', 0):.2f}
- 交易类型：{parsed_data.get('transaction_type', '未知')}
- 支付方式：{parsed_data.get('payment_method', '未知')}
- 账户类型：{parsed_data.get('account_type', '未知')}

💰 余额更新：{wallet_message}

账单ID：{bill_id}"""
            
            add_chat_message(messages, threads, thread_id_to_use, username, "assistant", assistant_message, "bill_parser")
            chat_messages.append({"role": "assistant", "content": assistant_message})
            
            logging.info(f"账单解析对话记录已添加到线程: {thread_id_to_use}")
            
        except Exception as chat_error:
            logging.warning(f"创建账单解析对话记录失败: {str(chat_error)}")
            # 不影响主要功能，继续执行
        
        # 获取对应余额字段的值
        result = users.get(ids=[updated_user.id], include=["metadatas"])
        metadata = ((result or {}).get("metadatas") or [None])[0] or {}
        
        account_type_lower = account_type.lower()
        if any(keyword in account_type_lower for keyword in ["零钱", "余额宝", "钱包", "wallet"]):
            new_balance = float(metadata.get("wallet_balance", 0.0))
        elif any(keyword in account_type_lower for keyword in ["银行卡", "储蓄卡", "银行", "bank", "card"]):
            new_balance = float(metadata.get("bank_balance", 0.0))
        elif any(keyword in account_type_lower for keyword in ["花呗", "借贷", "欠款", "debt", "credit", "huabei"]):
            new_balance = float(metadata.get("debt_amount", 0.0))
        else:
            new_balance = float(metadata.get("wallet_balance", 0.0))
        
        logging.info(f"账单创建成功 - 用户名: {username}, 账单ID: {bill_id}, 金额: {bill_amount:.2f}, 账户类型: {account_type}, 余额更新: {wallet_message}")
        
        return ParseBillImageResponse(
            success=True,
            message="账单解析并创建成功",
            bill_id=bill_id,
            parsed_data=parsed_data,
            wallet_balance=new_balance,
            thread_id=thread_id_to_use,
            chat_messages=chat_messages or None,
        )
        
    except Exception as e:
        logging.error(f"图片解析异常 - 用户名: {username}, 错误: {str(e)}")
        return ParseBillImageResponse(
            success=False,
            message=f"处理失败: {str(e)}",
            bill_id=None,
            parsed_data=None,
            wallet_balance=None
        )


@router.get("/bills/list", response_model=BillListResponse)
def get_bills_list(
    limit: int = Query(100, ge=1, le=1000),
    username: str = Depends(_get_username),
    bills: Collection = Depends(get_bills_collection),
):
    """
    获取用户的账单列表
    
    参数：
    - limit: 返回的最大账单数量（默认100，最多1000）
    
    返回：账单列表，按创建时间倒序排列
    """
    import logging
    
    logging.info(f"获取账单列表 - 用户名: {username}, 限制: {limit}")
    
    try:
        user_bills = list_user_bills(bills, username, limit)
        
        bill_items = []
        for bill in user_bills:
            bill_items.append(BillDetailItem(
                id=bill.get("id", ""),
                transaction_time=bill.get("transaction_time", ""),
                merchant_name=bill.get("merchant_name", ""),
                amount=float(bill.get("amount", 0)),
                transaction_type=bill.get("transaction_type", "expense"),
                payment_method=bill.get("payment_method", ""),
                account_type=bill.get("account_type", ""),
                counterparty=bill.get("counterparty", ""),
                actual_amount=float(bill.get("actual_amount", 0)),
                status=bill.get("status", "")
            ))
        
        return BillListResponse(
            success=True,
            message="获取成功",
            bills=bill_items,
            total_count=len(bill_items)
        )
        
    except Exception as e:
        logging.error(f"获取账单列表失败: {str(e)}")
        return BillListResponse(
            success=False,
            message=f"获取失败: {str(e)}",
            bills=[],
            total_count=0
        )


@router.get("/bills/report", response_model=BillReportResponse)
def get_bills_report(
    days: int = Query(30, ge=1, le=365),
    username: str = Depends(_get_username),
    users: Collection = Depends(get_users_collection),
    bills: Collection = Depends(get_bills_collection),
):
    """
    获取账单统计报告
    
    参数：
    - days: 统计天数（默认30天，最多365天）
    
    返回：包含收支统计、账户变化、商户排名等信息
    """
    import logging
    
    logging.info(f"生成账单报告 - 用户名: {username}, 统计天数: {days}")
    
    try:
        user = get_user_by_username(users, username)
        if not user:
            return BillReportResponse(
                success=False,
                message="用户不存在",
                summary=None,
                wallet_balance=None
            )
        
        # 计算账单汇总
        summary_data = calculate_bill_summary(bills, username, days)
        
        # 生成AI建议
        advice = _generate_bill_advice(
            total_income=summary_data["total_income"],
            total_expense=summary_data["total_expense"],
            top_merchants=summary_data["top_merchants"]
        )
        
        return BillReportResponse(
            success=True,
            message="报告生成成功",
            summary=summary_data,
            wallet_balance=float(user.wallet_balance),
            advice=advice
        )
        
    except Exception as e:
        logging.error(f"生成报告失败: {str(e)}")
        return BillReportResponse(
            success=False,
            message=f"生成失败: {str(e)}",
            summary=None,
            wallet_balance=None
        )


def _generate_bill_advice(
    total_income: float,
    total_expense: float,
    top_merchants: list[dict]
) -> str:
    """
    基于账单数据生成AI建议
    """
    advice = ""
    
    if total_income == 0 and total_expense == 0:
        return "暂无账单数据。"
    
    # 收支分析
    if total_income > total_expense:
        surplus = total_income - total_expense
        advice += f"✅ 收支情况良好，本期结余 ¥{surplus:.2f}。"
    elif total_expense > total_income:
        deficit = total_expense - total_income
        advice += f"⚠️ 本期支出超收入 ¥{deficit:.2f}，建议合理控制消费。"
    else:
        advice += "💭 本期收支平衡。"
    
    # 消费习惯分析
    if top_merchants:
        top_merchant = top_merchants[0].get("merchant", "")
        top_amount = top_merchants[0].get("amount", 0)
        advice += f"\n📊 主要消费来源：{top_merchant}，金额 ¥{abs(top_amount):.2f}。"
    
    advice += "\n💡 建议：定期检查账单，监控消费趋势。"
    
    return advice
