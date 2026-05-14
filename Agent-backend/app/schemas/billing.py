from typing import Literal

from pydantic import BaseModel


class BillItemResponse(BaseModel):
    id: str
    username: str
    change_amount: float
    source: str
    note: str
    created_at: str


class WalletBillItemResponse(BaseModel):
    id: str
    type: Literal["income", "expense"]
    amount: float
    description: str
    created_at: str
    remark: str


class WalletBillsData(BaseModel):
    bills: list[WalletBillItemResponse]
    page: int
    page_size: int


class WalletBillsResponse(BaseModel):
    code: int
    msg: str
    data: WalletBillsData


class GenerateReportRequest(BaseModel):
    period_type: str  # week/month/custom
    start_time: str | None = None
    end_time: str | None = None


class ExportReportRequest(BaseModel):
    period_type: str
    export_type: str  # excel/pdf
    start_time: str | None = None
    end_time: str | None = None


# ============ 图片账单解析相关模型 ============

class BillParseResult(BaseModel):
    """AI解析的账单数据"""
    transaction_time: str
    merchant_name: str
    amount: float
    transaction_type: Literal["income", "expense"]
    payment_method: str
    account_type: str
    counterparty: str
    actual_amount: float
    status: str


class ParseBillImageRequest(BaseModel):
    """图片账单上传请求"""
    username: str
    # 图片数据由multipart/form-data提供


class ChatTextItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ParseBillImageResponse(BaseModel):
    """图片账单解析响应"""
    success: bool
    message: str
    bill_id: str | None = None
    parsed_data: BillParseResult | None = None
    wallet_balance: float | None = None
    thread_id: str | None = None
    chat_messages: list[ChatTextItem] | None = None


class BillSummary(BaseModel):
    """账单汇总信息"""
    total_income: float
    total_expense: float
    net_change: float
    bill_count: int
    payment_methods: dict[str, float]
    top_merchants: list[dict[str, str | float]]
    daily_avg: float
    period_days: int


class BillDetailItem(BaseModel):
    """账单详情项"""
    id: str
    transaction_time: str
    merchant_name: str
    amount: float
    transaction_type: Literal["income", "expense"]
    payment_method: str
    account_type: str
    counterparty: str
    actual_amount: float
    status: str


class BillListResponse(BaseModel):
    """账单列表响应"""
    success: bool
    message: str
    bills: list[BillDetailItem]
    total_count: int


class BillReportResponse(BaseModel):
    """账单报告响应"""
    success: bool
    message: str
    summary: BillSummary
    wallet_balance: float | None = None
    advice: str = ""
