from fastapi import APIRouter, Depends, Header, Query
from chromadb.api.models.Collection import Collection

from app.database import get_bills_collection
from app.schemas.billing import WalletBillItemResponse, WalletBillsData, WalletBillsResponse
from app.services.app_service import list_user_active_metadatas

router = APIRouter(prefix="/api", tags=["wallet"])


def _get_username(
    x_username: str | None = Header(default=None),
    username: str | None = Query(default=None),
) -> str:
    return (x_username or username or "").strip()


@router.get("/wallet/bills", response_model=WalletBillsResponse)
def get_wallet_bills(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    bill_type: str = Query(default="all", pattern="^(all|income|expense)$", alias="type"),
    username: str = Depends(_get_username),
    bills: Collection = Depends(get_bills_collection),
):
    if not username:
        return WalletBillsResponse(
            code=1,
            msg="缺少用户名",
            data=WalletBillsData(bills=[], page=page, page_size=page_size),
        )

    records = list_user_active_metadatas(bills, username)
    records.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    if bill_type != "all":
        if bill_type == "income":
            records = [r for r in records if float(r.get("change_amount", 0.0)) >= 0]
        else:
            records = [r for r in records if float(r.get("change_amount", 0.0)) < 0]

    start = (page - 1) * page_size
    end = start + page_size
    page_items = records[start:end]

    bills_data = [
        WalletBillItemResponse(
            id=m.get("id", ""),
            type="income" if float(m.get("change_amount", 0.0)) >= 0 else "expense",
            amount=float(m.get("change_amount", 0.0)),
            description=str(m.get("source", "")),
            created_at=str(m.get("created_at", "")),
            remark=str(m.get("note", "")),
        )
        for m in page_items
    ]

    return WalletBillsResponse(
        code=0,
        msg="success",
        data=WalletBillsData(bills=bills_data, page=page, page_size=page_size),
    )
