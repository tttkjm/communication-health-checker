import sqlite3
from datetime import datetime

from communication_health_checker.domain.models.target.host import Host
from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId


def row_to_target(row: sqlite3.Row) -> Target:
    return Target(
        target_id=TargetId(value=row["id"]),
        name=row["name"],
        host=Host(value=row["host"]),
        description=row["description"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def target_to_row(target: Target) -> dict:
    return {
        "id": str(target.target_id),
        "name": target.name,
        "host": str(target.host),
        "description": target.description,
        "created_at": target.created_at.isoformat(),
        "updated_at": target.updated_at.isoformat(),
    }
