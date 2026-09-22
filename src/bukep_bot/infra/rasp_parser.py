import re

from bs4 import BeautifulSoup

from ..domain import Lesson, Schedule, Week
from .html import soup_of

TYPE_SHORT = {
    "Лекционное занятие": "Лекция",
    "Практическое занятие": "Практика",
    "Лабораторное занятие": "Лабораторная",
    "Семинарское занятие": "Семинар",
}

_EMPTY_MARKER = "Расписание отсутствует"
_ROOT_ID = "ctl00_head_Tbl_rasp1"
_TWO_COL_RE = re.compile(r"^(.*?)\s{2,}(.*)$")

def is_empty_schedule(html: str) -> bool:
    return _EMPTY_MARKER in soup_of(html).get_text()

def parse_schedule(html: str) -> Schedule:
    return parse_soup(soup_of(html))

def parse_soup(soup: BeautifulSoup) -> Schedule:
    root = soup.find(id=_ROOT_ID)
    if root is None:
        return {}

    result: Schedule = {}
    for day_tbl in root.find_all("table", class_="tbl_day"):
        day_tr = day_tbl.find("tr", class_="day")
        if day_tr is None:
            continue
        day_name = day_tr.get_text(" ", strip=True)

        lessons: list[Lesson] = []
        for tr in day_tbl.find_all("tr"):
            if tr is day_tr:
                continue
            num_td = tr.find("td", class_="num_para")
            para_td = tr.find("td", class_="para")
            if num_td is None or para_td is None:
                continue

            num_parts = [p.strip() for p in
                         num_td.get_text(separator="\n", strip=True).split("\n")
                         if p.strip()]
            para_num = num_parts[0] if num_parts else ""
            week: Week = "both"
            if len(num_parts) > 1:
                if "Числ" in num_parts[1]:
                    week = "numerator"
                elif "Знам" in num_parts[1]:
                    week = "denominator"

            span = para_td.find("span")
            if span is None:
                continue
            lines = [ln.strip() for ln in span.get_text(separator="\n").split("\n")
                     if ln.strip()]
            subject = lines[0] if lines else ""
            lesson_type, room = "", ""
            if len(lines) > 1:
                m = _TWO_COL_RE.match(lines[1])
                if m:
                    lesson_type = m.group(1).strip()
                    room = m.group(2).strip()
                else:
                    lesson_type = lines[1]

            lesson_type = TYPE_SHORT.get(lesson_type, lesson_type)
            teachers = tuple(
                _s(inp.get("value"))
                for inp in para_td.find_all("input", class_="fioprep")
            )
            lessons.append(Lesson(
                para=para_num, week=week, subject=subject,
                type=lesson_type, room=room, teachers=teachers,
            ))

        if lessons:
            result[day_name] = lessons

    return result

def _s(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " ".join(str(x) for x in v)
    return str(v)
