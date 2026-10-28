"""Disposable context cache; the HACK-013 store remains the source of truth.

Synchronous calls: async consumers should use a worker thread. Cache state lasts
for this process only; rehydrate it with remember() from the store after restart.
"""

import hashlib
import json
import re
import unicodedata
from http.client import HTTPException
from threading import RLock
from urllib.request import Request, urlopen

from app.config import settings


def _tokens(text):
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return set(re.findall(r"\w+", "".join(c for c in normalized if not unicodedata.combining(c))))


class MemoryService:
    def __init__(self, api_key=None, *, demo_mode=None):
        self._key = settings.BACKBOARD_API_KEY if api_key is None else api_key
        self._demo = settings.DEMO_MODE if demo_mode is None else demo_mode
        self._records = {}
        self._assistants = {}
        self._remote_ids = {}
        self._lock = RLock()

    def _post(self, path, body):
        request = Request("https://app.backboard.io/api" + path,
                          data=json.dumps(body).encode(), method="POST",
                          headers={"X-API-Key": self._key, "Content-Type": "application/json"})
        with urlopen(request, timeout=8) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise TypeError("Invalid Backboard object")
        return result

    @staticmethod
    def _id(response, field):
        value = response.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("Invalid Backboard identifier")
        return value

    def remember(self, run_id, kind, text, source):
        """Cache one passage, preserving its exact provenance. Returns a copy."""
        if not all(isinstance(v, str) and v.strip() for v in (run_id, kind, text, source)):
            raise ValueError("run_id, kind, text and source must be nonempty strings")
        identity = hashlib.sha256(json.dumps([run_id, kind, text, source]).encode()).hexdigest()
        with self._lock:
            records = self._records.setdefault(run_id, {})
            if identity in records:
                return dict(records[identity])
            record = {"run_id": run_id, "kind": kind, "text": text, "source": source, "demo_data": True}
            records[identity] = record
            if self._key and not self._demo:
                try:
                    if run_id not in self._assistants:
                        assistant = self._id(self._post("/assistants", {
                            "name": "SpeedHack " + hashlib.sha256(run_id.encode()).hexdigest()[:16]
                        }), "assistant_id")
                        # Save before thread creation: a failed thread is never retried blindly.
                        self._assistants[run_id] = assistant
                        self._id(self._post(f"/assistants/{assistant}/threads", {}), "thread_id")
                    assistant = self._assistants[run_id]
                    response = self._post(f"/assistants/{assistant}/memories", {
                        "content": text, "metadata": {"run_id": run_id, "kind": kind, "source": source}
                    })
                    memory_id = self._id(response, "memory_id")
                    self._remote_ids[(run_id, memory_id)] = identity
                    record["demo_data"] = False
                except (OSError, HTTPException, ValueError, TypeError, KeyError):
                    pass  # No provider response/error is logged; it may contain secrets.
            return dict(record)

    def recall(self, run_id, query, k=5):
        """Return up to k source-bearing passages; unsupported queries return []."""
        if type(k) is not int or not 0 <= k <= 50:
            raise ValueError("k must be an integer between 0 and 50")
        if not isinstance(query, str) or not isinstance(run_id, str):
            raise TypeError("run_id and query must be strings")
        words = _tokens(query)
        if not words or not k:
            return []
        with self._lock:
            records = self._records.get(run_id, {})
            if self._key and not self._demo and run_id in self._assistants:
                try:
                    response = self._post(f"/assistants/{self._assistants[run_id]}/memories/search",
                                          {"query": query, "limit": k})
                    memories = response["memories"]
                    if not isinstance(memories, list):
                        raise TypeError("Invalid memories")
                    result, seen = [], set()
                    for memory in memories:
                        if not isinstance(memory, dict):
                            raise TypeError("Invalid memory")
                        identity = self._remote_ids.get((run_id, memory.get("id", memory.get("memory_id"))))
                        if identity in records and identity not in seen:
                            seen.add(identity)
                            result.append(dict(records[identity]))
                    if result:
                        return result[:k]
                except (OSError, HTTPException, ValueError, TypeError, KeyError):
                    pass
            ranked = [(len(words & _tokens(record["text"])), record) for record in records.values()]
            ranked.sort(key=lambda item: item[0], reverse=True)
            return [dict(record, demo_data=True) for score, record in ranked if score > 0][:k]


_service = MemoryService()


def remember(run_id, kind, text, source):
    return _service.remember(run_id, kind, text, source)


def recall(run_id, query, k=5):
    return _service.recall(run_id, query, k)
