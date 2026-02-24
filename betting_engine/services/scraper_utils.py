"""Shared utilities for scrapers: randomized delays and user-agent rotation to reduce detection."""
import random
import time

from django.conf import settings

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def get_user_agent():
    """Use PLAYWRIGHT_USER_AGENT if set, otherwise pick randomly from pool."""
    ua = getattr(settings, "PLAYWRIGHT_USER_AGENT", None)
    return ua if ua else random.choice(USER_AGENTS)


def random_sleep(mode):
    """
    Random delays by context. Modes: short, medium, nav, long,
    between_bets, between_games, between_leagues, final.
    Ranges tuned to avoid robotic patterns while ensuring DOM loads.
    """
    ranges = {
        "short": (0.3, 0.8),
        "medium": (0.8, 2.0),
        "nav": (1.5, 3.5),
        "long": (2.5, 5.5),
        "between_bets": (2, 5),
        "between_games": (1.5, 4),
        "between_leagues": (2, 5),
        "final": (7, 14),
    }
    lo, hi = ranges.get(mode, (0.5, 1.5))
    time.sleep(random.uniform(lo, hi))
