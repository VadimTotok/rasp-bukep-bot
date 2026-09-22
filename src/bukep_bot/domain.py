from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Week = Literal["both", "numerator", "denominator"]

DAY_ORDER = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Воскресенье",
]

DAY_EMOJI = {"Понедельник": "🥱", "Пятница": "🎉"}

BELL_TIMES: dict[str, dict[int, str]] = {
    "weekday": {
        1: "08:30–10:05", 2: "10:15–11:50", 3: "12:25–14:00",
        4: "14:35–16:10", 5: "16:20–17:55", 6: "18:05–19:40",
        7: "19:50–21:25",
    },
    "saturday": {
        1: "08:30–10:05", 2: "10:15–11:50", 3: "12:00–13:35",
        4: "14:10–15:45", 5: "15:55–17:30", 6: "17:40–19:15",
        7: "19:25–21:00",
    },
}

BELL_DETAILED = (
    "<b>🔔 Расписание звонков</b>\n\n"
    "<b>Понедельник — пятница</b>\n"
    "1 пара · 08:30–09:15 / 09:20–10:05\n"
    "2 пара · 10:15–11:00 / 11:05–11:50\n"
    "<i>перерыв 11:50–12:25 (35 мин.)</i>\n"
    "3 пара · 12:25–13:10 / 13:15–14:00\n"
    "<i>перерыв 14:00–14:35 (35 мин.)</i>\n"
    "4 пара · 14:35–15:20 / 15:25–16:10\n"
    "5 пара · 16:20–17:05 / 17:10–17:55\n"
    "6 пара · 18:05–18:50 / 18:55–19:40\n"
    "7 пара · 19:50–20:35 / 20:40–21:25\n\n"
    "<b>Суббота</b>\n"
    "1 пара · 08:30–09:15 / 09:20–10:05\n"
    "2 пара · 10:15–11:00 / 11:05–11:50\n"
    "3 пара · 12:00–12:45 / 12:50–13:35\n"
    "<i>перерыв 13:35–14:10 (35 мин.)</i>\n"
    "4 пара · 14:10–14:55 / 15:00–15:45\n"
    "5 пара · 15:55–16:40 / 16:45–17:30\n"
    "6 пара · 17:40–18:25 / 18:30–19:15\n"
    "7 пара · 19:25–20:10 / 20:15–21:00"
)

def bell_for(day_name: str, para: str) -> str:
    key = "saturday" if day_name == "Суббота" else "weekday"
    try:
        return BELL_TIMES[key].get(int(para), "")
    except (ValueError, TypeError):
        return ""

def today_day_name() -> str | None:
    wd = datetime.now().weekday()
    return None if wd >= 6 else DAY_ORDER[wd]

@dataclass(slots=True, frozen=True)
class Lesson:
    para: str
    week: Week
    subject: str
    type: str
    room: str
    teachers: tuple[str, ...] = ()

@dataclass(slots=True, frozen=True)
class Item:
    """Факультет / специальность / курс / группа."""
    target: str
    label: str

@dataclass(slots=True, frozen=True)
class GroupContext:
    ft: str
    st: str
    kt: str
    gt: str
    gl: str
    fi: int
    si: int
    ki: int
    gi: int

Schedule = dict[str, list[Lesson]]

class BotError(Exception):
    """Базовая ошибка домена."""

class SiteUnavailable(BotError):
    """Сайт вуза недоступен и данных нет ни в сети, ни в кэше."""

class ScheduleMissing(BotError):
    """Для группы на сайте нет расписания."""
