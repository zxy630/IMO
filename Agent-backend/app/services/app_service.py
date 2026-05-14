import uuid
from datetime import datetime

from chromadb.api.models.Collection import Collection

from app.services.auth_service import get_user_by_username, now_iso, parse_amount_from_text
from app.utils.security import hash_password, verify_password

BASIC_PERMISSIONS = {"chat_text", "view_bill", "manage_wallet", "history_manage"}
VIP_PERMISSIONS = {"ocr_bill_adjust", "report_week_month", "advanced_model"}
SVIP_PERMISSIONS = {"custom_report", "export_report"}


def get_role_permissions(role_permissions: Collection, role_id: str) -> set[str]:
    result = role_permissions.get(where={"role_id": role_id}, include=["metadatas"])
    metadatas = (result or {}).get("metadatas") or []
    return {m.get("permission_key", "") for m in metadatas if int(m.get("is_deleted", 0)) == 0}


def require_permission(role_permissions: Collection, role_id: str, permission_key: str) -> bool:
    return permission_key in get_role_permissions(role_permissions, role_id)


def update_user_profile(users: Collection, username: str, nickname: str | None, avatar: str | None) -> tuple[bool, str]:
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    users.update(
        ids=[user.id],
        metadatas=[
            {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "nickname": user.nickname if nickname is None else nickname,
                "avatar": user.avatar if avatar is None else avatar,
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
    return True, "资料修改成功"


def change_password(users: Collection, username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    if not verify_password(old_password, user.password_hash):
        return False, "旧密码错误"
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
    return True, "密码修改成功"


def wallet_adjust_by_text(users: Collection, bills: Collection, username: str, text: str, source: str) -> tuple[bool, str]:
    amount = parse_amount_from_text(text)
    if amount == 0:
        return False, "文本中未识别到有效金额"
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    new_balance = float(user.wallet_balance) + float(amount)
    users.update(
        ids=[user.id],
        metadatas=[
            {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role_id": user.role_id,
                "wallet_balance": new_balance,
                "security_question": user.security_question,
                "security_answer_hash": user.security_answer_hash,
                "created_at": user.created_at,
                "updated_at": now_iso(),
                "is_deleted": user.is_deleted,
            }
        ],
        documents=["user"],
    )
    bill_id = str(uuid.uuid4())
    bills.add(
        ids=[bill_id],
        metadatas=[
            {
                "id": bill_id,
                "username": username,
                "change_amount": amount,
                "source": source,
                "note": text,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "is_deleted": 0,
            }
        ],
        documents=["bill"],
    )
    return True, f"钱包更新成功，当前余额: {new_balance:.2f}"


def generate_bill_report(bills: Collection, username: str, period: str) -> str:
    """生成账单报告"""
    import re
    from datetime import datetime, timedelta, timezone
    
    # 解析时间范围
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    
    # 改进时间段解析逻辑
    period_lower = period.lower()
    days = 30  # 默认一个月
    
    # 检查各种时间表达
    if re.search(r'(最近|近|过去)?三天|3天', period_lower):
        days = 3
    elif re.search(r'(最近|近|过去)?一?周|7天', period_lower):
        days = 7
    elif re.search(r'(最近|近|过去)?一?个月|30天', period_lower):
        days = 30
    
    start_time = (now - timedelta(days=days)).isoformat()
    
    # 获取账单记录
    records = list_user_active_metadatas(bills, username)
    filtered_records = [
        r for r in records 
        if datetime.fromisoformat(r.get("created_at", "")) >= datetime.fromisoformat(start_time)
    ]
    
    if not filtered_records:
        return f"近{days}天内没有账单记录。"
    
    # 统计数据
    total_income = 0
    total_expense = 0
    balance_changes = {"cash": 0, "bank": 0, "debt": 0}
    category_stats = {}
    
    for record in filtered_records:
        amount = float(record.get("change_amount", 0))
        balance_type = record.get("balance_type", "cash")
        source = record.get("source", "")
        
        if amount > 0:
            total_income += amount
        else:
            total_expense += abs(amount)
        
        balance_changes[balance_type] += amount
        
        # 按来源分类统计
        if source not in category_stats:
            category_stats[source] = 0
        category_stats[source] += amount
    
    # 生成报告
    report = f"📊 近{days}天账单报告\n\n"
    report += f"💰 总收入: {total_income:.2f}元\n"
    report += f"💸 总支出: {total_expense:.2f}元\n"
    report += f"📈 净收支: {total_income - total_expense:.2f}元\n\n"
    
    report += "🏦 各账户变化:\n"
    for balance_type, change in balance_changes.items():
        balance_name = {"cash": "零钱", "bank": "银行卡", "debt": "欠贷"}.get(balance_type, balance_type)
        report += f"  {balance_name}: {change:+.2f}元\n"
    
    report += "\n📋 分类统计:\n"
    for source, amount in sorted(category_stats.items(), key=lambda x: abs(x[1]), reverse=True):
        report += f"  {source}: {amount:+.2f}元\n"
    
    report += f"\n📝 共{len(filtered_records)}笔记录"
    
    return report


def detect_wallet_adjustment(text: str) -> tuple[bool, float, str, str]:
    import re
    amount_match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not amount_match:
        return False, 0.0, "", ""
    amount = float(amount_match.group(1))
    lower_text = text.lower()
    
    # 检测还款
    if "还" in lower_text and ("花呗" in text or "借呗" in text):
        # 检测还款来源
        if "银行卡" in text or "银行" in text:
            return True, amount, "bank_repayment", "bank"
        else:
            return True, amount, "cash_repayment", "cash"
    
    # 检测余额类型
    balance_type = "cash"  # 默认零钱
    balance_name = "零钱"
    if "银行卡" in text or "银行" in text:
        balance_type = "bank"
        balance_name = "银行卡"
    elif "花呗" in text or "借呗" in text or "欠" in text or "贷" in text:
        balance_type = "debt"
        balance_name = "花呗"
    
    income_keywords = ["发工资", "工资", "薪资", "收入"]
    expense_keywords = ["消费", "买", "花", "支出", "扣", "交"]
    if any(kw in lower_text for kw in income_keywords):
        source = f"{balance_name}收入"
        return True, amount, source, balance_type
    elif any(kw in lower_text for kw in expense_keywords):
        # 尝试提取具体消费项目
        item = ""
        if "买" in lower_text:
            buy_match = re.search(r'买([^0-9]+)', text)
            if buy_match:
                item = buy_match.group(1).strip()
        elif "交" in lower_text:
            pay_match = re.search(r'交([^0-9]+)', text)
            if pay_match:
                item = pay_match.group(1).strip()
        
        if item:
            source = f"{balance_name}{item}支出"
        else:
            source = f"{balance_name}消费支出"
        return True, -amount, source, balance_type
    return False, 0.0, "", ""


def wallet_adjust_repayment(users: Collection, bills: Collection, username: str, amount: float, repayment_type: str, note: str) -> tuple[bool, str]:
    if amount == 0:
        return False, "金额不能为0"
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    
    # 获取当前余额
    result = users.get(ids=[user.id], include=["metadatas"])
    metadata = ((result or {}).get("metadatas") or [None])[0] or {}
    
    if repayment_type == "cash_repayment":
        # 零钱还款：零钱-，欠贷+
        cash_balance = float(metadata.get("wallet_balance", 0.0))
        debt_balance = float(metadata.get("debt_amount", 0.0))
        new_cash_balance = cash_balance - amount
        new_debt_balance = debt_balance + amount
        metadata["wallet_balance"] = new_cash_balance
        metadata["debt_amount"] = new_debt_balance
        balance_name = "零钱"
    elif repayment_type == "bank_repayment":
        # 银行卡还款：银行卡-，欠贷+
        bank_balance = float(metadata.get("bank_balance", 0.0))
        debt_balance = float(metadata.get("debt_amount", 0.0))
        new_bank_balance = bank_balance - amount
        new_debt_balance = debt_balance + amount
        metadata["bank_balance"] = new_bank_balance
        metadata["debt_amount"] = new_debt_balance
        balance_name = "银行卡"
    else:
        return False, "无效的还款类型"
    
    # 更新用户元数据
    metadata["updated_at"] = now_iso()
    users.update(ids=[user.id], metadatas=[metadata], documents=["user"])
    
    # 生成两条账单记录
    now = now_iso()
    
    # 支出账单
    expense_bill_id = str(uuid.uuid4())
    bills.add(
        ids=[expense_bill_id],
        metadatas=[
            {
                "id": expense_bill_id,
                "username": username,
                "change_amount": -amount,
                "source": f"{balance_name}花呗还款支出",
                "note": note,
                "balance_type": repayment_type.split("_")[0],  # cash 或 bank
                "created_at": now,
                "updated_at": now,
                "is_deleted": 0,
            }
        ],
        documents=["bill"],
    )
    
    # 收入账单
    income_bill_id = str(uuid.uuid4())
    bills.add(
        ids=[income_bill_id],
        metadatas=[
            {
                "id": income_bill_id,
                "username": username,
                "change_amount": amount,
                "source": "花呗还款收入",
                "note": note,
                "balance_type": "debt",
                "created_at": now,
                "updated_at": now,
                "is_deleted": 0,
            }
        ],
        documents=["bill"],
    )
    
    return True, f"{balance_name}还款成功，欠贷减少{amount:.2f}元"


def wallet_adjust_by_amount(users: Collection, bills: Collection, username: str, amount: float, source: str, note: str, balance_type: str = "cash") -> tuple[bool, str]:
    if amount == 0:
        return False, "金额不能为0"
    user = get_user_by_username(users, username)
    if not user:
        return False, "用户不存在"
    
    # 获取当前余额
    result = users.get(ids=[user.id], include=["metadatas"])
    metadata = ((result or {}).get("metadatas") or [None])[0] or {}
    
    if balance_type == "cash":
        current_balance = float(metadata.get("wallet_balance", 0.0))
        new_balance = current_balance + amount
        balance_field = "wallet_balance"
        balance_name = "零钱"
    elif balance_type == "bank":
        current_balance = float(metadata.get("bank_balance", 0.0))
        new_balance = current_balance + amount
        balance_field = "bank_balance"
        balance_name = "银行卡"
    elif balance_type == "debt":
        current_balance = float(metadata.get("debt_amount", 0.0))
        new_balance = current_balance + amount
        balance_field = "debt_amount"
        balance_name = "欠贷"
    else:
        return False, "无效的余额类型"
    
    # 更新用户元数据
    metadata[balance_field] = new_balance
    metadata["updated_at"] = now_iso()
    users.update(ids=[user.id], metadatas=[metadata], documents=["user"])
    
    bill_id = str(uuid.uuid4())
    bills.add(
        ids=[bill_id],
        metadatas=[
            {
                "id": bill_id,
                "username": username,
                "change_amount": amount,
                "source": source,
                "note": note,
                "balance_type": balance_type,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "is_deleted": 0,
            }
        ],
        documents=["bill"],
    )
    return True, f"{balance_name}更新成功，当前余额: {new_balance:.2f}"


def create_chat(chats: Collection, username: str, model_name: str, message: str, answer: str) -> None:
    chat_id = str(uuid.uuid4())
    chats.add(
        ids=[chat_id],
        metadatas=[
            {
                "id": chat_id,
                "username": username,
                "model_name": model_name,
                "message": message,
                "answer": answer,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "is_deleted": 0,
            }
        ],
        documents=["chat"],
    )


def create_chat_thread(threads: Collection, username: str, title: str) -> dict:
    thread_id = str(uuid.uuid4())
    now = now_iso()
    metadata = {
        "id": thread_id,
        "thread_id": thread_id,
        "username": username,
        "title": title,
        "last_message": "",
        "created_at": now,
        "updated_at": now,
        "is_deleted": 0,
    }
    threads.add(ids=[thread_id], metadatas=[metadata], documents=["chat_thread"])
    return metadata


def add_chat_message(
    messages: Collection,
    threads: Collection,
    thread_id: str,
    username: str,
    role: str,
    content: str,
    model: str,
) -> str:
    message_id = str(uuid.uuid4())
    now = now_iso()
    messages.add(
        ids=[message_id],
        metadatas=[
            {
                "id": message_id,
                "message_id": message_id,
                "thread_id": thread_id,
                "username": username,
                "role": role,
                "content": content,
                "model": model,
                "model_id": model,  # 兼容旧数据读取
                "created_at": now,
                "updated_at": now,
                "is_deleted": 0,
            }
        ],
        documents=["chat_message"],
    )

    # 更新 thread 的 last_message / updated_at
    result = threads.get(ids=[thread_id], include=["metadatas"])
    thread_meta = ((result or {}).get("metadatas") or [None])[0] or {}
    if thread_meta and int(thread_meta.get("is_deleted", 0)) == 0:
        thread_meta["last_message"] = content if role == "user" else thread_meta.get("last_message", "")
        thread_meta["updated_at"] = now
        threads.update(ids=[thread_id], metadatas=[thread_meta], documents=["chat_thread"])
    return message_id


def list_chat_threads(threads: Collection, username: str) -> list[dict]:
    result = threads.get(where={"username": username}, include=["metadatas"])
    metas = [m for m in ((result or {}).get("metadatas") or []) if int(m.get("is_deleted", 0)) == 0]
    metas.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return metas


def get_latest_chat_thread(threads: Collection, username: str) -> dict | None:
    items = list_chat_threads(threads, username)
    return items[0] if items else None


def list_thread_messages(messages: Collection, username: str, thread_id: str) -> list[dict]:
    # Chroma where 只允许一个条件；这里先按 thread_id 查，再用 username 过滤
    result = messages.get(where={"thread_id": thread_id}, include=["metadatas"])
    metas = [
        m
        for m in ((result or {}).get("metadatas") or [])
        if int(m.get("is_deleted", 0)) == 0 and m.get("username") == username
    ]
    metas.sort(key=lambda x: x.get("created_at", ""))
    return metas


def list_user_active_metadatas(collection: Collection, username: str) -> list[dict]:
    result = collection.get(where={"username": username}, include=["metadatas"])
    return [m for m in ((result or {}).get("metadatas") or []) if int(m.get("is_deleted", 0)) == 0]


def soft_delete_record(collection: Collection, record_id: str, metadata: dict) -> None:
    metadata["is_deleted"] = 1
    metadata["updated_at"] = now_iso()
    collection.update(ids=[record_id], metadatas=[metadata], documents=["deleted"])


def filter_bill_records(records: list[dict], period_type: str, start_time: str | None, end_time: str | None) -> list[dict]:
    if period_type in {"week", "month"}:
        days = 7 if period_type == "week" else 30
        start_dt = datetime.utcnow().timestamp() - days * 24 * 3600
        return [r for r in records if datetime.fromisoformat(r.get("created_at", now_iso())).timestamp() >= start_dt]
    if period_type == "custom" and start_time and end_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        return [
            r
            for r in records
            if start_dt <= datetime.fromisoformat(r.get("created_at", now_iso())) <= end_dt
        ]
    return records
