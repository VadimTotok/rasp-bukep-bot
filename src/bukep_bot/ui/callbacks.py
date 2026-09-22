from aiogram.filters.callback_data import CallbackData
from pydantic import Field

_HEX16 = r"^[0-9a-f]{16}$"

class MenuCB(CallbackData, prefix="menu"):
    pass

class FacultyCB(CallbackData, prefix="fac"):
    idx: int

class SpecialtyCB(CallbackData, prefix="spec"):
    f: int
    s: int

class CourseCB(CallbackData, prefix="crs"):
    f: int
    s: int
    k: int

class GroupPickCB(CallbackData, prefix="grp"):
    f: int
    s: int
    k: int
    g: int

class ScheduleCB(CallbackData, prefix="sch"):
    ctx_id: str = Field(pattern=_HEX16)
    action: str = "today"     # today|refresh|pick|all|refresh_all|day|refresh_day
    day: int = 0

class BellsCB(CallbackData, prefix="bells"):
    pass

class FavListCB(CallbackData, prefix="fav"):
    action: str               # list|add|del|open
    ctx_id: str = ""

class HelpCB(CallbackData, prefix="help"):
    pass
