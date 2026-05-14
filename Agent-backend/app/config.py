from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # ChromaDB 持久化数据目录（默认在项目根目录下）
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    CHROMA_PATH: Path = BASE_DIR / "chroma_data"
    CHROMA_COLLECTION_USERS: str = "users"
    CHROMA_COLLECTION_ROLES: str = "roles"
    CHROMA_COLLECTION_PERMISSIONS: str = "permissions"
    CHROMA_COLLECTION_ROLE_PERMISSIONS: str = "role_permissions"
    CHROMA_COLLECTION_CHATS: str = "chats"  # legacy: 单条对话记录
    CHROMA_COLLECTION_CHAT_THREADS: str = "chat_threads"
    CHROMA_COLLECTION_CHAT_MESSAGES: str = "chat_messages"
    CHROMA_COLLECTION_BILLS: str = "bills"
    AVATAR_UPLOAD_DIR: Path = BASE_DIR / "uploads" / "avatars"
    BILL_IMAGE_UPLOAD_DIR: Path = BASE_DIR / "uploads" / "bills"
    DASHSCOPE_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str = "sk-xxxxx" 
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


