from ..domain import GroupContext
from ..infra.storage import Storage


class FavoritesService:
    def __init__(self, storage: Storage):
        self._s = storage

    async def ensure_context(self, ctx: GroupContext) -> str:
        return await self._s.upsert_context(ctx)

    async def get(self, ctx_id: str) -> GroupContext | None:
        return await self._s.get_context(ctx_id)

    async def add(self, user_id: int, ctx: GroupContext) -> str:
        ctx_id = await self._s.upsert_context(ctx)
        await self._s.add_favorite(user_id, ctx_id)
        return ctx_id

    async def remove(self, user_id: int, ctx_id: str) -> None:
        await self._s.remove_favorite(user_id, ctx_id)

    async def is_favorite(self, user_id: int, ctx_id: str) -> bool:
        return await self._s.is_favorite(user_id, ctx_id)

    async def list(self, user_id: int) -> list[dict]:
        return await self._s.list_favorites(user_id)
