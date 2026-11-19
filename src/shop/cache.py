"""A small in-memory TTL cache. In production this is Redis (shared by all servers) with the same rules:

- search results: minutes (the catalog changes slowly; an update event can clear it)
- stock and orders: never cached here; they're read live at answer time
"""
import time


class TTLCache:
    def __init__(self, ttl_seconds: float = 300, max_items: int = 1000):
        self.ttl, self.max, self.items = ttl_seconds, max_items, {}
        self.hits = self.misses = 0

    def get(self, key):
        v = self.items.get(key)
        if v and v[0] > time.time():
            self.hits += 1
            return v[1]
        self.items.pop(key, None)
        self.misses += 1
        return None

    def set(self, key, value):
        if len(self.items) >= self.max:  # drop the entry closest to expiry
            self.items.pop(min(self.items, key=lambda k: self.items[k][0]))
        self.items[key] = (time.time() + self.ttl, value)
