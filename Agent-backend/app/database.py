from typing import Generator

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings


_client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))


def get_users_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_USERS)
    yield collection


def get_roles_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_ROLES)
    yield collection


def get_permissions_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_PERMISSIONS)
    yield collection


def get_role_permissions_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_ROLE_PERMISSIONS)
    yield collection


def get_chats_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHATS)
    yield collection


def get_chat_threads_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHAT_THREADS)
    yield collection


def get_chat_messages_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_CHAT_MESSAGES)
    yield collection


def get_bills_collection() -> Generator[Collection, None, None]:
    collection = _client.get_or_create_collection(name=settings.CHROMA_COLLECTION_BILLS)
    yield collection

