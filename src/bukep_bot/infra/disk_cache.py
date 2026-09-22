import json
import logging
import os
import re
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)
_SAFE = re.compile(r"[^a-zA-Z0-9_.-]")

class DiskCache:
    def __init__(self, root: Path):
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._root / (_SAFE.sub("_", key) + ".json")

    def save(self, key: str, data) -> None:
        try:
            fd, tmp = tempfile.mkstemp(dir=self._root, prefix=".tmp-")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self._path(key))
        except Exception:
            log.exception("cache save failed: %s", key)

    def load(self, key: str):
        p = self._path(key)
        if not p.exists():
            return None
        try:
            with p.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            log.exception("cache load failed: %s", key)
            return None
