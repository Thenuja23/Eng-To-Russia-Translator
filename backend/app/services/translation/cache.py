"""Small thread-safe TTL cache for translation results.

The UI translates as the user types (debounced), and the same sentence is often
re-translated when switching modes or re-opening a history item. Caching keeps
repeated requests cheap - important for a paid engine such as Google - and
makes repeated output deterministic.

Only successful, placeholder-safe results are cached. Errors and flagged
translations are deliberately not cached so a transient network problem can
recover on the next request.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple


class TranslationCache:
    def __init__(self, ttl_seconds: int = 900, max_entries: int = 256):
        self.ttl_seconds = max(0, int(ttl_seconds))
        self.max_entries = max(1, int(max_entries))
        self._data: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def make_key(
        engine: str,
        src: str,
        tgt: str,
        text: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        # repr of extra is stable enough for the few numeric options we support.
        suffix = repr(sorted((extra or {}).items()))
        return f"{engine}|{src}|{tgt}|{len(text)}|{suffix}|{text}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self.ttl_seconds <= 0:
            return None
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            created, value = item
            if now - created > self.ttl_seconds:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return dict(value)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        if self.ttl_seconds <= 0:
            return
        with self._lock:
            self._data[key] = (time.time(), dict(value))
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
