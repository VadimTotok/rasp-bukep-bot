# Telegram-бот с расписанием БУКЭП

[![CI](https://github.com/VadimTotok/rasp-bukep-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/VadimTotok/rasp-bukep-bot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)](https://python.org)

Неофициальный Telegram-бот с расписанием занятий БУКЭП. Удобный
интерфейс, избранные группы, расписание звонков.

## Зачем это нужно?

Сайт вуза — это старый ASP.NET WebForms ещё с 2008 года. API нет,
JSON тоже нет. Только HTML и postback'и.

Пользоваться сайтом то ещё удовольствие. Таблицы разваливаются, до
нужной страницы приходится добираться через кучу шагов, а каждый
переход полностью перегружает страницу.

Бот делает то же самое, но за пару тапов и с кэшем.

## Что умеет

- 📅 **Навигация**: факультет → специальность → курс → группа
- ⭐ **Избранное**: закрепить группы, открывать одной кнопкой
- 🔔 **Расписание звонков**
- 📋 **По дням или всё сразу**
- 🔄 **Кэш двух уровней**: если сайт вуза лежит, показываем последнее
  известное расписание
- ↩️ **Перепривязка групп**: если группу перевели на другой курс,
  бот найдёт её сам

## Технические решения

### Скрейпинг ASP.NET WebForms

Сайт вуза использует `__doPostBack`. Навигация идёт через скрытые
POST-запросы с состоянием в `__VIEWSTATE` и `__EVENTVALIDATION`.
Одна группа — это 5 последовательных POST-запросов:

```
GET  /Default.aspx
POST /Default.aspx  (клик «Группы»)
POST /Default.aspx  (клик по факультету)
POST /Default.aspx  (клик по специальности)
POST /Default.aspx  (клик по курсу)
POST /Default.aspx  (клик по группе)   → HTML с расписанием
```

Каждый запрос возвращает новый HTML, из которого нужно вытащить
скрытые поля для следующего. Плюс IIS-специфичные URL с `%uXXXX`.

### Кэш двух уровней

- **В памяти** — `TTLCache` на 10 минут. Хиты мгновенные, не бьют
  по сайту.
- **На диске** — атомарный JSON. Если сайт упал, отдаём последнее
  известное расписание и честно помечаем «данные могут быть
  устаревшими».

### Стабильный идентификатор группы

`ctx_id = blake2b(ft | st | group_label)` — не зависит от курса.
Если группу перевели на другой курс, избранное не потеряется,
бот найдёт её заново по названию.

### Безопасность

Все данные с сайта проходят через `html.escape()` перед вставкой
в сообщения Telegram. HTML-инъекция через подменённый ответ
невозможна. Подробнее в [SECURITY.md](SECURITY.md).

## Стек

- **Python**
- **aiogram** — асинхронный Telegram-фреймворк
- **BeautifulSoup + lxml** — парсинг HTML
- **aiohttp** — HTTP-клиент
- **aiosqlite** — асинхронный SQLite
- **cachetools** — TTL-кэш

## Запуск

```bash
git clone https://github.com/твой_ник/bukep-schedule-bot
cd bukep-schedule-bot

python -m venv .venv
source .venv/bin/activate

pip install -e .
cp .env.example .env
# впиши в .env свой BOT_TOKEN от @BotFather

python -m bukep_bot
```

Данные (SQLite и кэш) кладутся в `./data/`. Каталог можно вынести
через переменную `BUKEP_DATA_DIR`.

## Разработка

```bash
pip install -e ".[dev]"

ruff check src tests
mypy src
pytest -v
```

Тесты:

- `tests/test_parser.py` — 12 тестов парсера, включая 4 на
  **реальном HTML** с сайта. Если сайт изменит разметку, эти тесты
  упадут первыми.
- `tests/test_storage.py` — 10 тестов SQLite и `ctx_id`.
- `tests/test_renderers.py` — 3 теста на HTML-экранирование.

### Настройка недели

В `.env` укажи начало семестра (первый полный понедельник):

    BUKEP_SEMESTER_START=2026-09-07
    BUKEP_SEMESTER_FIRST_WEEK=numerator

Если не задать бот покажет все пары без фильтра по неделям. В начале каждого семестра дату нужно обновлять.

## Обратная связь

Нашли баг или есть идея — [откройте issue](https://github.com/VadimTotok/rasp-bukep-bot/issues).
Буду рад любой обратной связи.

## Дисклеймер

Неофициальный проект. Не связан с БУКЭП. Данные берутся с открытого
сайта [rasp.bukep.ru](https://rasp.bukep.ru).

## Лицензия

MIT.