from pydantic import BaseModel, Field
from pydantic import ConfigDict


class SendTextRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str
    message: str
    model: str = Field(default="qwen-turbo", alias="model_id")
    thread_id: str | None = None
    new_chat: bool = False
    greeting_message: str | None = None


class ChatSendResponse(BaseModel):
    success: bool
    message: str
    thread_id: str | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None
    answer: str | None = None
    model: str | None = None


class ChatThreadItemResponse(BaseModel):
    thread_id: str
    title: str
    last_message: str
    updated_at: str


class ChatMessageItemResponse(BaseModel):
    message_id: str
    thread_id: str
    role: str  # user/assistant
    content: str
    model: str
    created_at: str


class LatestChatResponse(BaseModel):
    thread_id: str
    title: str
    updated_at: str
    messages: list[ChatMessageItemResponse]


class TextAmountAdjustRequest(BaseModel):
    text: str


class BillImageAdjustRequest(BaseModel):
    image_text: str


class ChatRecordResponse(BaseModel):
    id: str
    username: str
    model_name: str
    message: str
    answer: str
    created_at: str
