from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GuildConfig:
    welcome_channel_id: int | None = None
    autorole_id: int | None = None


class GuildConfigStore:
    def __init__(self, path: Path, defaults: GuildConfig) -> None:
        self._path = path
        self._defaults = defaults
        self._lock = asyncio.Lock()
        self._cache: dict[int, GuildConfig] = self._read()

    def get(self, guild_id: int) -> GuildConfig:
        return self._cache.get(guild_id, self._defaults)

    def is_configured(self, guild_id: int) -> bool:
        return guild_id in self._cache

    def __len__(self) -> int:
        return len(self._cache)

    @property
    def path(self) -> Path:
        return self._path

    def dumps(self) -> str:
        return json.dumps(self._as_payload(), ensure_ascii=False, indent=2)

    async def update(self, guild_id: int, **changes: Any) -> GuildConfig:
        async with self._lock:
            config = replace(self.get(guild_id), **changes)
            self._cache[guild_id] = config
            await asyncio.to_thread(self._write)
            return config

    async def load_dump(self, text: str) -> int:
        raw = json.loads(text)
        if not isinstance(raw, dict):
            raise ValueError("Ожидается JSON-объект вида {\"id сервера\": {...}}")

        parsed = self._parse(raw)
        if not parsed:
            raise ValueError("В файле нет ни одной корректной записи")

        async with self._lock:
            self._cache = parsed
            await asyncio.to_thread(self._write)
        return len(parsed)

    def _as_payload(self) -> dict[str, dict[str, Any]]:
        return {str(gid): asdict(cfg) for gid, cfg in self._cache.items()}

    def _read(self) -> dict[int, GuildConfig]:
        if not self._path.is_file():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Не удалось прочитать %s, настройки серверов сброшены", self._path)
            return {}
        if not isinstance(raw, dict):
            logger.error("Неверный формат %s, настройки серверов сброшены", self._path)
            return {}
        return self._parse(raw)

    @staticmethod
    def _parse(raw: dict[str, Any]) -> dict[int, GuildConfig]:
        result: dict[int, GuildConfig] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                continue
            try:
                result[int(key)] = GuildConfig(
                    welcome_channel_id=_as_optional_int(value.get("welcome_channel_id")),
                    autorole_id=_as_optional_int(value.get("autorole_id")),
                )
            except (TypeError, ValueError):
                logger.warning("Пропущена некорректная запись настроек для %r", key)
        return result

    def _write(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._as_payload(), handle, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self._path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise


def _as_optional_int(value: Any) -> int | None:
    return None if value is None else int(value)
