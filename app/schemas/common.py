from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    service: str


class HealthDatabaseResponse(BaseModel):
    status: str
    service: str
    database: str
