# app/ratelimit.py
# Простой ограничитель частоты запросов (без внешних библиотек).

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """Позволяет не более max_hits запросов с одного IP за window секунд."""

    def __init__(self, max_hits: int, window: int):
        self.max_hits = max_hits
        self.window = window
        self.hits = defaultdict(deque)

    def __call__(self, request: Request) -> bool:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        dq = self.hits[ip]
        
        # Удаляем старые запросы, которые вышли за пределы окна времени
        while dq and now - dq[0] > self.window:
            dq.popleft()
            
        if len(dq) >= self.max_hits:
            raise HTTPException(
                status_code=429,
                detail="Слишком много запросов. Пожалуйста, попробуйте через несколько минут."
            )
        dq.append(now)
        return True


# 5 заявок с одного IP за 10 минут (600 секунд) — защита формы от спама
limit_booking = RateLimiter(max_hits=5, window=600)

# 8 попыток входа за 15 минут (900 секунд) — защита от подбора пароля админки
limit_login = RateLimiter(max_hits=8, window=900)