from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    username: str
    nickname: str
    avatar: str
    role_code: int
    wallet_balance: float
    created_at: str
    updated_at: str


class UserProfileSimpleResponse(BaseModel):
    success: bool
    data: dict | None = None
    message: str = ""


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar: str | None = None


class UpdateProfileNewRequest(BaseModel):
    username: str
    nickname: str
    avatar: str | None = None


class UpdateProfileResponse(BaseModel):
    success: bool
    data: dict | None = None
    message: str = ""


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class WalletData(BaseModel):
    cash_balance: float
    bank_balance: float
    debt_amount: float


class WalletResponse(BaseModel):
    success: bool
    message: str
    data: WalletData | None = None


class MembershipStatusResponse(BaseModel):
    success: bool
    role_code: int | None = None
    message: str = ""


class MembershipUpgradeRequest(BaseModel):
    username: str


class MembershipUpgradeResponse(BaseModel):
    success: bool
    message: str
    role_code: int | None = None
