import os
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(os.environ.get("BUKEP_DATA_DIR", "./data"))
RASP_BASE_URL = "https://rasp.bukep.ru"

GITHUB_URL = "https://github.com/VadimTotok/rasp-bukep-bot"
ISSUES_URL = f"{GITHUB_URL}/issues"

RASP_VERIFY_SSL = False

HTTP_TIMEOUT = 15.0
HTTP_RETRIES = 3
SCHEDULE_TTL = 600
TREE_TTL = 86400
CACHE_MAXSIZE = 2000
THROTTLE_RATE = 1.5

def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    data_dir: Path

def load_config() -> Config:
    _load_dotenv()

    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token or ":" not in token:
        raise SystemExit(
            "BOT_TOKEN не задан.\n"
            "Положите его в .env (BOT_TOKEN=...) или в переменную окружения."
        )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        DATA_DIR.chmod(0o700)
    except OSError:
        pass
    return Config(bot_token=token, data_dir=DATA_DIR)
