from pydantic import BaseModel, Field


class CreateTargetRequest(BaseModel):
    """ターゲット作成リクエスト（プリミティブのみ・ドメイン非依存）。"""

    name: str = Field(..., min_length=1, max_length=100, description="表示名", examples=["Router-1"])
    host: str = Field(..., description="ホスト（IP/ホスト名）", examples=["192.168.0.1"])
    description: str = Field(default="", max_length=500, description="説明", examples=["1F コアスイッチ"])


class UpdateTargetRequest(BaseModel):
    """ターゲット更新リクエスト。"""

    name: str = Field(..., min_length=1, max_length=100, description="表示名", examples=["Router-1"])
    host: str = Field(..., description="ホスト（IP/ホスト名）", examples=["192.168.0.1"])
    description: str = Field(default="", max_length=500, description="説明")


class TargetResponse(BaseModel):
    """ターゲット応答。"""

    id: str = Field(..., description="ターゲットID", examples=["tgt_0123456789abcdef0123456789abcdef"])
    name: str = Field(..., description="表示名")
    host: str = Field(..., description="ホスト")
    description: str = Field(..., description="説明")
    created_at: str = Field(..., description="作成日時 (ISO8601)")
    updated_at: str = Field(..., description="更新日時 (ISO8601)")
