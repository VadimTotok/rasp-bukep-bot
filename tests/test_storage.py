import pytest

from bukep_bot.domain import GroupContext
from bukep_bot.infra.storage import Storage, make_ctx_id

@pytest.fixture
async def storage(tmp_path):
    s = Storage(tmp_path / "test.db")
    await s.start()
    yield s
    await s.close()

def _ctx(**overrides) -> GroupContext:
    base = dict(
        ft="F1", st="S1", kt="K1", gt="G1", gl="ИС-21",
        fi=0, si=0, ki=0, gi=0,
    )
    base.update(overrides)
    return GroupContext(**base)

def test_ctx_id_stable():
    assert make_ctx_id("F1", "S1", "ИС-21") == make_ctx_id("F1", "S1", "ИС-21")

def test_ctx_id_differs_for_different_groups():
    assert make_ctx_id("F1", "S1", "ИС-21") != make_ctx_id("F1", "S1", "ИС-22")

def test_ctx_id_is_hex16():
    v = make_ctx_id("F1", "S1", "ИС-21")
    assert len(v) == 16
    assert all(c in "0123456789abcdef" for c in v)

async def test_upsert_creates_context(storage):
    ctx = _ctx()
    ctx_id = await storage.upsert_context(ctx)
    assert await storage.get_context(ctx_id) == ctx

async def test_upsert_updates_targets(storage):
    ctx_id = await storage.upsert_context(_ctx())
    await storage.upsert_context(_ctx(kt="K2", gt="G2", ki=1, gi=0))
    got = await storage.get_context(ctx_id)
    assert got.kt == "K2"
    assert got.gt == "G2"

async def test_get_missing_returns_none(storage):
    assert await storage.get_context("0000000000000000") is None

async def test_add_and_check_favorite(storage):
    ctx_id = await storage.upsert_context(_ctx())
    await storage.add_favorite(42, ctx_id)
    assert await storage.is_favorite(42, ctx_id) is True
    assert await storage.is_favorite(43, ctx_id) is False

async def test_add_favorite_twice_is_idempotent(storage):
    ctx_id = await storage.upsert_context(_ctx())
    await storage.add_favorite(42, ctx_id)
    await storage.add_favorite(42, ctx_id)
    assert len(await storage.list_favorites(42)) == 1

async def test_remove_favorite(storage):
    ctx_id = await storage.upsert_context(_ctx())
    await storage.add_favorite(42, ctx_id)
    await storage.remove_favorite(42, ctx_id)
    assert await storage.is_favorite(42, ctx_id) is False

async def test_favorites_isolated_by_user(storage):
    id_a = await storage.upsert_context(_ctx(gl="A"))
    id_b = await storage.upsert_context(_ctx(gl="B"))
    await storage.add_favorite(42, id_a)
    await storage.add_favorite(43, id_b)
    assert [it["gl"] for it in await storage.list_favorites(42)] == ["A"]
    assert [it["gl"] for it in await storage.list_favorites(43)] == ["B"]
