from pathlib import Path

import pytest

from bukep_bot.domain import DAY_ORDER
from bukep_bot.infra.html import soup_of
from bukep_bot.infra.rasp_parser import (
    is_empty_schedule,
    parse_schedule,
    parse_soup,
)

MINI_HTML = """
<html><body>
<div id="ctl00_head_Tbl_rasp1">
  <table class="tbl_day">
    <tr class="day"><td>Понедельник</td></tr>
    <tr>
      <td class="num_para">1<br>Числитель</td>
      <td class="para">
        <span>Математика<br>Лекционное занятие      ауд. 101</span>
        <input class="fioprep" value="Иванов И.И.">
        <input class="fioprep" value="Петров П.П.">
      </td>
    </tr>
    <tr>
      <td class="num_para">2</td>
      <td class="para">
        <span>Физика<br>Практическое занятие      202</span>
      </td>
    </tr>
  </table>
</div>
</body></html>
"""

def test_parse_empty_html_returns_empty_dict():
    assert parse_schedule("<html></html>") == {}

def test_parse_no_root_returns_empty_dict():
    html = "<html><body><div>Что-то другое</div></body></html>"
    assert parse_schedule(html) == {}

def test_is_empty_schedule_detects_marker():
    html = "<html><body><div>Расписание отсутствует</div></body></html>"
    assert is_empty_schedule(html) is True

def test_is_empty_schedule_false_for_real():
    assert is_empty_schedule(MINI_HTML) is False

def test_mini_schedule_parses_correctly():
    sched = parse_schedule(MINI_HTML)
    assert "Понедельник" in sched
    lessons = sched["Понедельник"]
    assert len(lessons) == 2

    first, second = lessons

    assert first.para == "1"
    assert first.week == "numerator"
    assert first.subject == "Математика"
    assert first.type == "Лекция"              # сокращено из "Лекционное занятие"
    assert first.room == "ауд. 101"
    assert first.teachers == ("Иванов И.И.", "Петров П.П.")

    assert second.para == "2"
    assert second.week == "both"
    assert second.subject == "Физика"
    assert second.type == "Практика"
    assert second.teachers == ()


def test_mini_schedule_denominator():
    html = MINI_HTML.replace("Числитель", "Знаменатель")
    sched = parse_schedule(html)
    assert sched["Понедельник"][0].week == "denominator"

def test_parse_soup_accepts_soup_object():
    soup = soup_of(MINI_HTML)
    sched = parse_soup(soup)
    assert "Понедельник" in sched

def test_all_days_from_day_order():
    sched = parse_schedule(MINI_HTML)
    for day in sched:
        assert day in DAY_ORDER

@pytest.fixture
def schedule_html() -> str:
    p = Path(__file__).parent / "fixtures" / "schedule.html"
    if not p.exists():
        pytest.skip(f"нет фикстуры {p}")
    return p.read_text(encoding="utf-8")

@pytest.fixture
def empty_html() -> str:
    p = Path(__file__).parent / "fixtures" / "empty.html"
    if not p.exists():
        pytest.skip(f"нет фикстуры {p}")
    return p.read_text(encoding="utf-8")

def test_real_schedule_parses(schedule_html):
    sched = parse_schedule(schedule_html)
    assert isinstance(sched, dict)
    assert sched, "расписание с реальной страницы не должно быть пустым"
    for day in sched:
        assert day in DAY_ORDER, f"неизвестный день: {day!r}"


def test_real_schedule_lessons_have_required_fields(schedule_html):
    sched = parse_schedule(schedule_html)
    for day, lessons in sched.items():
        for i, lesson in enumerate(lessons):
            assert lesson.para, f"{day}[{i}]: нет номера пары"
            assert lesson.subject, f"{day}[{i}]: нет предмета"
            assert lesson.week in ("both", "numerator", "denominator"), \
                f"{day}[{i}]: плохая неделя {lesson.week!r}"


def test_real_schedule_has_lessons(schedule_html):
    sched = parse_schedule(schedule_html)
    total = sum(len(lessons) for lessons in sched.values())
    assert total > 0, "расписание распарсилось, но пар нет"


def test_empty_fixture_detected(empty_html):
    assert is_empty_schedule(empty_html) is True
