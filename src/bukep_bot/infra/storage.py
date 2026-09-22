import hashlib
import logging
import time
from pathlib import Path

import aiosqlite

from ..domain import GroupContext

log = logging.getLogger(__name__)

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS contexts (
    ctx_id      TEXT PRIMARY KEY,
    ft          TEXT NOT NULL,
    st          TEXT NOT NULL,
    kt          TEXT NOT NULL,
    gt          TEXT NOT NULL,
    gl          TEXT NOT NULL,
    fi          INTEGER NOT NULL,
    si          INTEGER NOT NULL,
    ki          INTEGER NOT NULL,
    gi          INTEGER NOT NULL,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id   INTEGER NOT NULL,
    ctx_id    TEXT NOT NULL REFERENCES contexts(ctx_id) ON DELETE CASCADE,
    added_at  INTEGER NOT NULL,
    PRIMARY KEY (user_id, ctx_id)
);

CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id);
"""

def make_ctx_id(ft: str, st: str, gl: str) -> str:
    raw = f"{ft}|{st}|{gl}"
    return hashlib.blake2b(raw.encode("utf-8"), digest_size=8).hexdigest()

class Storage:
    def __init__(self, db_path: Path):
        self._path = db_path
        self._db: aiosqlite.Connection | None = None

    async def start(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()
        try:
            self._path.chmod(0o600)
        except OSError:
            pass

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage.start() не вызван")
        return self._db

    async def upsert_context(self, ctx: GroupContext) -> str:
        ctx_id = make_ctx_id(ctx.ft, ctx.st, ctx.gl)
        now = int(time.time())
        await self.db.execute(
            """
            INSERT INTO contexts
                (ctx_id, ft, st, kt, gt, gl, fi, si, ki, gi, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ctx_id) DO UPDATE SET
                ft = excluded.ft, st = excluded.st,
                kt = excluded.kt, gt = excluded.gt, gl = excluded.gl,
                fi = excluded.fi, si = excluded.si,
                ki = excluded.ki, gi = excluded.gi,
                updated_at = excluded.updated_at
            """,
            (ctx_id, ctx.ft, ctx.st, ctx.kt, ctx.gt, ctx.gl,
             ctx.fi, ctx.si, ctx.ki, ctx.gi, now, now),
        )
        await self.db.commit()
        return ctx_id

    async def get_context(self, ctx_id: str) -> GroupContext | None:
        async with self.db.execute(
            "SELECT * FROM contexts WHERE ctx_id = ?", (ctx_id,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return GroupContext(
            ft=row["ft"], st=row["st"], kt=row["kt"], gt=row["gt"], gl=row["gl"],
            fi=row["fi"], si=row["si"], ki=row["ki"], gi=row["gi"],
        )

    async def add_favorite(self, user_id: int, ctx_id: str) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, ctx_id, added_at) "
            "VALUES (?, ?, ?)",
            (user_id, ctx_id, int(time.time())),
        )
        await self.db.commit()

    async def remove_favorite(self, user_id: int, ctx_id: str) -> None:
        await self.db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND ctx_id = ?",
            (user_id, ctx_id),
        )
        await self.db.commit()

    async def is_favorite(self, user_id: int, ctx_id: str) -> bool:
        async with self.db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND ctx_id = ?",
            (user_id, ctx_id),
        ) as cur:
            return await cur.fetchone() is not None

    async def list_favorites(self, user_id: int) -> list[dict]:
        async with self.db.execute(
            """
            SELECT c.ctx_id, c.gl, c.ft, c.st, c.kt, c.gt,
                   c.fi, c.si, c.ki, c.gi, f.added_at
            FROM favorites f
            JOIN contexts c ON f.ctx_id = c.ctx_id
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
            """,
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]
