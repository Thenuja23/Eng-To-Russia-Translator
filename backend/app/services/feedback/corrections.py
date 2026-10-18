import threading
from typing import Any, Dict, List


class CorrectionService:
    """In-memory store for user feedback / corrections.

    Persistence to Supabase is a later step; this keeps the API honest (it
    really stores what it receives) without a hard dependency on a database.
    """

    def __init__(self):
        self._items: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def submit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._items.append(dict(data))
        return data

    def count(self) -> int:
        return len(self._items)

    def export_for_training(self, approved_only: bool = True) -> List[Dict[str, Any]]:
        # Only approved corrections from consenting users may be exported.
        with self._lock:
            items = list(self._items)
        if approved_only:
            items = [i for i in items if i.get("consent_to_train")]
        return items
