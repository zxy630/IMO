"""
图片账单智能解析服务
支持支付宝花呗、微信支付/零钱等账单截图识别和解析
"""
import base64
import json
import logging
import re
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from chromadb.api.models.Collection import Collection

from app.config import settings
from app.services.auth_service import get_user_by_username, now_iso


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为Base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def normalize_amount(value) -> float:
    """将金额字符串清洗为浮点数，支持带货币符号和中文的输入"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    # 删除非数字、非小数点、非负号字符
    cleaned = re.sub(r"[^0-9.\-]", "", raw)
    if cleaned in {"", ".", "-", "-."}:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_bill_image_with_dashscope(image_base64: str) -> dict:
    """
    使用DashScope视觉模型解析账单截图
    
    返回格式:
    {
        "success": bool,
        "data": {
            "transaction_time": "交易时间",
            "merchant_name": "商户名称",
            "amount": 金额,
            "transaction_type": "交易类型(income/expense)",
            "payment_method": "支付方式(支付宝/微信等)",
            "account_type": "账户类型(余额宝/花呗/零钱等)",
            "counterparty": "交易对象",
            "actual_amount": 实际金额,
            "status": "交易状态(completed/pending等)"
        },
        "message": "错误信息或解析说明"
    }
    """
    if not settings.DASHSCOPE_API_KEY:
        logging.error("DashScope API Key 未配置")
        return {
            "success": False,
            "message": "未配置 DASHSCOPE_API_KEY"
        }
    
    logging.info("开始调用DashScope进行账单图片解析")
    
    # 构建提示词用于账单识别
    system_prompt = """你是一个专业的支付账单图片识别助手。

你需要分析上传的支付宝、微信等支付截图，提取以下关键信息：
1. 交易时间 (transaction_time): 格式为 ISO 8601
2. 商户名称 (merchant_name): 支付给谁
3. 金额 (amount): 支付/收款金额（数字）
4. 交易类型 (transaction_type): income(收入) 或 expense(支出)。注意：大部分支付截图都是支出，只有明确显示"收款"、"转入"等字样的才是收入
5. 支付方式 (payment_method): 支付宝 Alipay / 微信 WeChat / 其他
6. 账户类型 (account_type): 余额宝、花呗、零钱、储蓄卡等
7. 交易对象 (counterparty): 对方账户名或昵称
8. 实收/实付金额 (actual_amount): 最终交易金额（数字）
9. 交易状态 (status): 已完成 completed / 待确认 pending / 已取消 cancelled

重要提示：
- 大部分上传的账单截图都是支出（消费、转账等），只有明确显示"收款"、"转入"、"收入"等字样的才是收入
- 如果不确定交易类型，默认为expense（支出）

如果信息不完整，请根据图片内容合理推断。
返回格式必须是有效的JSON对象。"""
    
    user_prompt = """请分析这张支付账单截图，提取所有关键信息。
    
    返回格式必须是以下JSON结构（缺失的字段使用空字符串或0）:
    {
        "transaction_time": "...",
        "merchant_name": "...",
        "amount": 0.0,
        "transaction_type": "income|expense",
        "payment_method": "...",
        "account_type": "...",
        "counterparty": "...",
        "actual_amount": 0.0,
        "status": "completed|pending|cancelled"
    }
    
    只返回JSON对象，不要包含任何其他文字。"""
    
    try:
        # 使用DashScope API进行视觉识别
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-vl-plus",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logging.info("DashScope返回结果，开始解析JSON内容")
        
        # 检查是否是OpenAI兼容格式或DashScope原生格式
        if "choices" in result and result.get("choices"):
            # OpenAI兼容格式
            message = result["choices"][0].get("message", {})
            content = message.get("content", "")
        elif result.get("code") == "200":
            # DashScope原生格式
            output = result.get("output", {})
            message = output.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
        else:
            return {
                "success": False,
                "message": f"API调用失败: {result.get('message', '未知错误')}"
            }
            
        # 从返回内容中提取JSON
        if content:
            # 尝试直接解析
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                # 尝试从markdown代码块中提取JSON
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group(1))
                else:
                    # 尝试查找JSON对象
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed_data = json.loads(json_match.group(0))
                    else:
                        return {
                            "success": False,
                            "message": f"无法解析返回的数据格式: {content}"
                        }
            
            # 验证必要字段
            required_fields = ["transaction_time", "merchant_name", "amount", "transaction_type"]
            if all(field in parsed_data for field in required_fields):
                return {
                    "success": True,
                    "data": parsed_data,
                    "message": "账单识别成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"返回数据缺少必要字段"
                }
        else:
            return {
                "success": False,
                "message": "API返回内容为空"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"网络请求失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"图片解析失败: {str(e)}"
        }


def create_bill_record(
    bills: Collection,
    username: str,
    parsed_data: dict,
    image_path: str = ""
) -> tuple[bool, str, str]:
    """
    创建结构化账单记录
    
    返回: (success, message, bill_id)
    """
    try:
        bill_id = str(uuid.uuid4())
        logging.info(f"开始创建账单记录, username={username}, bill_id={bill_id}")
        
        # 解析交易时间，转换为北京时间ISO格式
        transaction_time = parsed_data.get("transaction_time", "")
        try:
            if transaction_time:
                # 尝试解析多种时间格式
                dt = None
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%Y/%m/%d %H:%M:%S",
                ]:
                    try:
                        dt = datetime.strptime(transaction_time, fmt)
                        break
                    except ValueError:
                        continue
                
                if dt is None:
                    # 如果无法解析，使用当前时间
                    dt = datetime.now(timezone(timedelta(hours=8)))
                else:
                    # 如果没有时区信息，假设是北京时间
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
                
                transaction_time_iso = dt.isoformat()
            else:
                transaction_time_iso = now_iso()
        except Exception:
            transaction_time_iso = now_iso()
        
        # 提取金额
        actual_amount = normalize_amount(parsed_data.get("actual_amount", parsed_data.get("amount", 0)))
        amount = actual_amount
        if amount == 0:
            amount = normalize_amount(parsed_data.get("amount", 0))
        
        # 根据交易类型调整金额符号
        transaction_type = parsed_data.get("transaction_type", "expense").lower()
        if transaction_type == "income":
            amount = abs(amount)
        elif transaction_type == "expense":
            amount = -abs(amount)
        
        # 构建账单元数据
        metadata = {
            "id": bill_id,
            "username": username,
            "transaction_time": transaction_time_iso,
            "merchant_name": parsed_data.get("merchant_name", ""),
            "amount": amount,
            "transaction_type": transaction_type,
            "payment_method": parsed_data.get("payment_method", ""),
            "account_type": parsed_data.get("account_type", ""),
            "counterparty": parsed_data.get("counterparty", ""),
            "actual_amount": actual_amount,
            "status": parsed_data.get("status", "completed"),
            "image_path": image_path,
            "source": parsed_data.get("merchant_name", "图片解析"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "is_deleted": 0,
        }
        
        # 保存到数据库
        bills.add(
            ids=[bill_id],
            metadatas=[metadata],
            documents=["bill"]
        )
        logging.info(f"账单记录已保存, bill_id={bill_id}, amount={amount:.2f}")
        
        return True, f"账单创建成功，金额: {amount:.2f}元", bill_id
        
    except Exception as e:
        return False, f"账单创建失败: {str(e)}", ""


def list_user_bills(bills: Collection, username: str, limit: int = 100) -> list[dict]:
    """
    获取用户最近的账单列表
    
    返回: 账单列表，按创建时间倒序
    """
    try:
        result = bills.get(
            where={"username": username},
            include=["metadatas"]
        )
        
        metadatas = (result or {}).get("metadatas") or []
        
        # 过滤未删除的账单
        active_bills = [m for m in metadatas if int(m.get("is_deleted", 0)) == 0]
        
        # 按创建时间倒序排序
        active_bills.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return active_bills[:limit]
    except Exception as e:
        return []


def calculate_bill_summary(bills: Collection, username: str, days: int = 30) -> dict:
    """
    计算账单汇总信息
    
    返回格式:
    {
        "total_income": 总收入,
        "total_expense": 总支出,
        "net_change": 净变化,
        "bill_count": 账单数量,
        "payment_methods": {"支付宝": 金额, ...},
        "top_merchants": [{"merchant": "名称", "amount": 金额}, ...],
        "daily_avg": 日均,
        "period_days": 统计天数
    }
    """
    try:
        result = bills.get(
            where={"username": username},
            include=["metadatas"]
        )
        
        metadatas = (result or {}).get("metadatas") or []
        
        # 过滤时间范围内的有效账单
        beijing_tz = timezone(timedelta(hours=8))
        now = datetime.now(beijing_tz)
        cutoff_time = now - timedelta(days=days)
        
        active_bills = []
        for m in metadatas:
            if int(m.get("is_deleted", 0)) == 0:
                try:
                    bill_time = datetime.fromisoformat(m.get("created_at", ""))
                    if bill_time >= cutoff_time:
                        active_bills.append(m)
                except ValueError:
                    pass
        
        # 统计数据
        total_income = 0.0
        total_expense = 0.0
        payment_method_stats = {}
        merchant_stats = {}
        
        for bill in active_bills:
            amount = float(bill.get("actual_amount", 0))
            transaction_type = bill.get("transaction_type", "").lower()
            
            if transaction_type == "income":
                total_income += amount
            else:
                total_expense += amount
            
            # 按支付方式统计
            payment_method = bill.get("payment_method", "其他")
            payment_method_stats[payment_method] = payment_method_stats.get(payment_method, 0) + amount
            
            # 按商户统计
            merchant = bill.get("merchant_name", "未知")
            if merchant not in merchant_stats:
                merchant_stats[merchant] = 0
            merchant_stats[merchant] += float(bill.get("amount", 0))
        
        # 获取排名前5的商户
        top_merchants = sorted(
            [{"merchant": k, "amount": v} for k, v in merchant_stats.items()],
            key=lambda x: abs(x["amount"]),
            reverse=True
        )[:5]
        
        # 计算日均
        daily_avg = (total_income - total_expense) / max(1, days)
        
        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_change": round(total_income - total_expense, 2),
            "bill_count": len(active_bills),
            "payment_methods": payment_method_stats,
            "top_merchants": top_merchants,
            "daily_avg": round(daily_avg, 2),
            "period_days": days
        }
        
    except Exception as e:
        return {
            "total_income": 0,
            "total_expense": 0,
            "net_change": 0,
            "bill_count": 0,
            "payment_methods": {},
            "top_merchants": [],
            "daily_avg": 0,
            "period_days": days
        }


def update_user_wallet_from_bill(
    users: Collection,
    username: str,
    bill_amount: float,
    account_type: str = ""
) -> tuple[bool, str]:
    """
    根据账单金额和账户类型更新用户余额
    
    支持的账户类型：
    - 零钱、余额宝等 -> 更新 wallet_balance
    - 银行卡、储蓄卡等 -> 更新 bank_balance  
    - 花呗、借贷等 -> 更新 debt_amount
    """
    try:
        user = get_user_by_username(users, username)
        if not user:
            return False, "用户不存在"
        
        # 获取当前用户元数据
        result = users.get(ids=[user.id], include=["metadatas"])
        metadata = ((result or {}).get("metadatas") or [None])[0] or {}
        
        # 根据账户类型确定更新哪个余额字段
        account_type_lower = account_type.lower()
        if any(keyword in account_type_lower for keyword in ["零钱", "余额宝", "钱包", "wallet"]):
            # 更新钱包余额
            current_balance = float(metadata.get("wallet_balance", 0.0))
            new_balance = current_balance + float(bill_amount)
            balance_field = "wallet_balance"
            balance_name = "零钱"
        elif any(keyword in account_type_lower for keyword in ["银行卡", "储蓄卡", "银行", "bank", "card"]):
            # 更新银行卡余额
            current_balance = float(metadata.get("bank_balance", 0.0))
            new_balance = current_balance + float(bill_amount)
            balance_field = "bank_balance"
            balance_name = "银行卡"
        elif any(keyword in account_type_lower for keyword in ["花呗", "借贷", "欠款", "debt", "credit", "huabei"]):
            # 更新借贷金额（支出增加欠款，收入减少欠款）
            current_balance = float(metadata.get("debt_amount", 0.0))
            new_balance = current_balance - float(bill_amount)  # 注意：支出增加欠款，收入减少欠款
            balance_field = "debt_amount"
            balance_name = "借贷"
        else:
            # 默认更新钱包余额
            current_balance = float(metadata.get("wallet_balance", 0.0))
            new_balance = current_balance + float(bill_amount)
            balance_field = "wallet_balance"
            balance_name = "零钱"
        
        # 更新用户元数据
        updated_metadata = {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "role_id": user.role_id,
            "wallet_balance": metadata.get("wallet_balance", 0.0),
            "bank_balance": metadata.get("bank_balance", 0.0),
            "debt_amount": metadata.get("debt_amount", 0.0),
            "security_question": user.security_question,
            "security_answer_hash": user.security_answer_hash,
            "created_at": user.created_at,
            "updated_at": now_iso(),
            "is_deleted": user.is_deleted,
        }
        updated_metadata[balance_field] = new_balance
        
        users.update(
            ids=[user.id],
            metadatas=[updated_metadata],
            documents=["user"]
        )
        
        return True, f"{balance_name}已更新，当前余额: {new_balance:.2f}元"
        
    except Exception as e:
        return False, f"余额更新失败: {str(e)}"
