from bukep_bot.domain import Lesson
from bukep_bot.ui.renderers import format_schedule

def test_renderer_escapes_html_from_site():
    sched = {
        "Понедельник": [
            Lesson(
                para="1", week="both",
                subject="<script>alert(1)</script>",
                type="Лекция", room="101",
                teachers=("<b>Хакер</b>",),
            ),
        ],
    }
    text = format_schedule(sched, group_label="<i>Группа</i>")
    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert "<b>Хакер</b>" not in text
    assert "&lt;b&gt;Хакер&lt;/b&gt;" in text
    assert "<i>Группа</i>" not in text

def test_renderer_keeps_own_tags():
    sched = {
        "Понедельник": [
            Lesson(para="1", week="numerator", subject="Математика",
                   type="Лекция", room="101", teachers=()),
        ],
    }
    text = format_schedule(sched, group_label="ИС-21")
    assert "<b>" in text
    assert "<i>[Числ.]</i>" in text
    assert "Математика" in text

def test_renderer_empty_day():
    sched = {"Понедельник": []}
    text = format_schedule(sched, group_label="ИС-21", day="Понедельник")
    assert "занятий нет" in text
