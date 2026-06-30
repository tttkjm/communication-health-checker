from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    """値オブジェクト基底（不変・値等価）。"""

    model_config = ConfigDict(frozen=True)
