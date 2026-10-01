"""SQLite repository and JSON serialization for Master Profile Bank."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from careercompiler.models.profile import Profile


def export_profile_json(profile: Profile) -> str:
    """Serialize a Profile model to a formatted, deterministic JSON string.

    Keys are formatted with indentation to guarantee human-readability
    and byte-identical round-trips.
    """
    # Parse to dict and re-serialize with sorted keys for byte determinism
    data = json.loads(profile.model_dump_json())
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def import_profile_json(json_str: str) -> Profile:
    """Deserialize a JSON string into a validated Profile model.

    Raises ValidationError on schema violations.
    """
    return Profile.model_validate_json(json_str)


class SQLiteProfileRepository:
    """SQLite-backed storage repository for Master Profiles with schema versioning."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            # Check current version
            cur = self.conn.execute("SELECT MAX(version) FROM schema_migrations")
            row = cur.fetchone()
            current_ver = row[0] if row and row[0] is not None else 0

            if current_ver < 1:
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS profiles (
                        id TEXT PRIMARY KEY,
                        version INTEGER NOT NULL,
                        updated_at TEXT NOT NULL,
                        data TEXT NOT NULL
                    )
                    """
                )
                now = datetime.now(UTC).isoformat()
                self.conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?)",
                    (now,),
                )

    def save(self, profile: Profile) -> None:
        """Insert or update a Profile in SQLite."""
        now = datetime.now(UTC).isoformat()
        payload = export_profile_json(profile)
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO profiles (id, version, updated_at, data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    version = excluded.version,
                    updated_at = excluded.updated_at,
                    data = excluded.data
                """,
                (profile.id, profile.version, now, payload),
            )

    def get(self, profile_id: str) -> Profile | None:
        """Retrieve a Profile by ID, returning None if not found."""
        cur = self.conn.execute("SELECT data FROM profiles WHERE id = ?", (profile_id,))
        row = cur.fetchone()
        if not row:
            return None
        return import_profile_json(row["data"])

    def list_ids(self) -> list[str]:
        """List all stored profile IDs."""
        cur = self.conn.execute("SELECT id FROM profiles ORDER BY id ASC")
        return [str(row["id"]) for row in cur.fetchall()]

    def delete(self, profile_id: str) -> bool:
        """Delete a profile by ID. Returns True if deleted, False if not found."""
        with self.conn:
            cur = self.conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            return cur.rowcount > 0

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SQLiteProfileRepository":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
