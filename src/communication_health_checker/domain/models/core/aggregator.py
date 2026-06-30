from typing import Generic

from communication_health_checker.domain.models.core.entity import Entity, TId


class Aggregator(Entity[TId], Generic[TId]):
    """集約ルート基底（一貫性境界）。"""

    def validate_invariants(self) -> None:  # サブクラスで上書き
        ...
