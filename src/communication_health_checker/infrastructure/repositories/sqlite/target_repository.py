from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository
from communication_health_checker.infrastructure.repositories.sqlite.connection import Database
from communication_health_checker.infrastructure.repositories.sqlite.target_mapper import row_to_target, target_to_row


class SqliteTargetRepository(ITargetRepository):
    """SQLite による ITargetRepository 実装（SQL アクセス = DAO 役を内包）。"""

    def __init__(self, database: Database) -> None:
        self._db = database

    def save(self, target: Target) -> None:
        row = target_to_row(target)
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO targets (id, name, host, description, created_at, updated_at)
                VALUES (:id, :name, :host, :description, :created_at, :updated_at)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    host = excluded.host,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                row,
            )

    def find_by_id(self, target_id: TargetId) -> Target | None:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM targets WHERE id = ?", (str(target_id),))
            row = cur.fetchone()
        return row_to_target(row) if row is not None else None

    def find_all(self) -> list[Target]:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM targets ORDER BY created_at ASC, id ASC")
            rows = cur.fetchall()
        return [row_to_target(r) for r in rows]

    def exists(self, target_id: TargetId) -> bool:
        with self._db.cursor() as cur:
            cur.execute("SELECT 1 FROM targets WHERE id = ?", (str(target_id),))
            return cur.fetchone() is not None

    def delete(self, target_id: TargetId) -> None:
        with self._db.cursor() as cur:
            cur.execute("DELETE FROM targets WHERE id = ?", (str(target_id),))

    def delete_all(self) -> None:
        with self._db.cursor() as cur:
            cur.execute("DELETE FROM targets")
