"""The request rate of a machine translation service."""
from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    """Keep the characters sent in any one minute under what the plan allows.

    The free Azure tier refuses requests once a rolling minute passes its limit, and a refused request
    costs the backoff that follows it, not only the retry. Waiting a little before sending is cheaper
    than being refused: it turns a run full of "slow down" replies into a steady one.
    """

    def __init__(self, characters_per_minute: int | None):
        self.limit = characters_per_minute
        self.window: deque[tuple[float, int]] = deque()

    def seconds_to_wait(self, characters: int, now: float) -> float:
        """How long to wait before this batch fits inside the limit of the last minute."""
        if not self.limit:
            return 0.0
        while self.window and now - self.window[0][0] >= 60:
            self.window.popleft()
        spent = sum(size for _, size in self.window)
        if spent + characters <= self.limit or not self.window:
            return 0.0
        return max(60 - (now - self.window[0][0]), 0.0)

    def take(self, characters: int, now: float | None = None) -> float:
        """Wait if the batch would pass the limit, then record it. Returns the seconds waited."""
        now = time.time() if now is None else now
        waited = self.seconds_to_wait(characters, now)
        if waited:
            time.sleep(waited)
            now += waited
        self.window.append((now, characters))
        return waited
