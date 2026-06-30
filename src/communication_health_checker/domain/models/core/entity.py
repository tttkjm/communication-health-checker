from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

TId = TypeVar("TId")


class Entity(BaseModel, Generic[TId]):
    """ID 等値性を提供するエンティティ基底。"""

    model_config = ConfigDict(validate_assignment=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def id(self) -> TId:  # サブクラスで実体IDを返す
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
