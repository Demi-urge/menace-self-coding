"""Filesystem backed cache for storing chunk summary metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable
import hashlib

logger = logging.getLogger(__name__)


class ChunkSummaryCache:
    """Persist chunk summaries keyed by path hashes on disk."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _file_for(self, key: str) -> Path:
        safe_key = key.strip().replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe_key}.json"

    def hash_path(self, path: Path) -> str:
        return hashlib.sha256(str(path).encode("utf-8")).hexdigest()

    def get(self, key: str) -> Dict[str, Any] | None:
        path = self._file_for(key)
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None
        except Exception:
            logger.debug("failed to read chunk summary cache for key %s", key, exc_info=True)
            return None

    def set(self, key: str, summaries: Iterable[Dict[str, Any]]) -> None:
        path = self._file_for(key)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        data = {"summaries": list(summaries)}
        try:
            with tmp_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh)
            tmp_path.replace(path)
        except Exception:
            logger.debug("failed to write chunk summary cache for key %s", key, exc_info=True)
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                logger.debug("failed to cleanup temporary cache file for key %s", key, exc_info=True)

    def clear(self) -> None:
        try:
            for item in self.directory.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                    except FileNotFoundError:
                        continue
        except Exception:
            logger.debug("failed to clear chunk summary cache", exc_info=True)
