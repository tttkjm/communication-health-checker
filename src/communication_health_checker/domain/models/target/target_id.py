import uuid

from pydantic import Field

from communication_health_checker.domain.models.core import ValueObject


class TargetId(ValueObject):
    """ターゲット機器の一意識別子。形式: tgt_{uuid32hex}."""

    value: str = Field(..., pattern=r"^tgt_[0-9a-f]{32}$", description="ターゲットID")

    @classmethod
    def generate(cls) -> "TargetId":
        return cls(value=f"tgt_{uuid.uuid4().hex}")

    def __str__(self) -> str:
        return self.value
