# src/stock_analysis/infrastructure/utils/rate_limit.py
import time, random

class RateLimiter:
    """
    לא יותר מ-rate_per_minute בקשות לדקה, refill רציף.
    שימוש:
      limiter = RateLimiter(90)
      limiter.acquire() לפני כל קריאה ל-yfinance
    """
    def __init__(self, rate_per_minute: int = 60):
        self.capacity = int(rate_per_minute)
        self.tokens = float(rate_per_minute)
        self.rate_per_sec = float(rate_per_minute) / 60.0
        self.last = time.time()

    def acquire(self):
        now = time.time()
        delta = now - self.last
        self.tokens = min(self.capacity, self.tokens + delta * self.rate_per_sec)
        self.last = now
        if self.tokens < 1.0:
            wait = (1.0 - self.tokens) / self.rate_per_sec
            time.sleep(wait + random.uniform(0, 0.25))  # jitter
            self.tokens = 0.0
            self.last = time.time()
        else:
            self.tokens -= 1.0
