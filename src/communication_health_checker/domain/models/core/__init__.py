"""ドメインモデルの基底クラス（唯一の re-export 許可ディレクトリ）。"""

from communication_health_checker.domain.models.core.aggregator import Aggregator
from communication_health_checker.domain.models.core.entity import Entity
from communication_health_checker.domain.models.core.exceptions import (
    DomainException,
    EntityNotFoundException,
    InvalidOperationException,
    InvariantViolationException,
)
from communication_health_checker.domain.models.core.value_object import ValueObject

__all__ = [
    "Aggregator",
    "Entity",
    "ValueObject",
    "DomainException",
    "EntityNotFoundException",
    "InvalidOperationException",
    "InvariantViolationException",
]
