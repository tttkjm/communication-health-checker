from pydantic import Field

from communication_health_checker.domain.models.core import Aggregator, InvalidOperationException
from communication_health_checker.domain.models.target.host import Host
from communication_health_checker.domain.models.target.target_id import TargetId


class Target(Aggregator[TargetId]):
    """ターゲット機器の集約ルート。"""

    target_id: TargetId = Field(..., description="ターゲットID")
    name: str = Field(..., min_length=1, max_length=100, description="表示名")
    host: Host = Field(..., description="ホスト（IP/ホスト名）")
    description: str = Field(default="", max_length=500, description="説明")

    @property
    def id(self) -> TargetId:
        return self.target_id

    def rename(self, name: str) -> None:
        if not name.strip():
            raise InvalidOperationException("name must not be empty")
        self.name = name

    def change_host(self, host: Host) -> None:
        self.host = host

    def validate_invariants(self) -> None:
        if not self.name.strip():
            raise InvalidOperationException("target name must not be empty")
