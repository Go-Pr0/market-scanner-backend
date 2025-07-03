import time
import random
from typing import List, Dict, Optional, Any

import pandas as pd
import requests
import json
import numpy as np

from threading import Lock

from pathlib import Path

# Example user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]

# Optional proxy list — format: {"http": "http://proxy_ip:port", "https": "http://proxy_ip:port"}
PROXIES_LIST = [
    # Example:
    # {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
    # Add your proxies here or leave empty for no proxies
]

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "top_500_full.json"

# Cache variables
_cached_dataset: List[Dict[str, Any]] = []  # full 500 coin dataset with fd_pct added
_threshold_cache: Dict[int, List[Dict[str, Any]]] = {}
_last_update: float = 0.0
_cache_lock: Lock = Lock()


def _fetch_market_page(page: int, proxies: Optional[Dict] = None) -> pd.DataFrame:
    """Fetch a single page from CoinGecko markets endpoint with stealth headers and optional proxy."""
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd&order=market_cap_desc&per_page=250"
        f"&page={page}&sparkline=false&price_change_percentage=24h"
    )
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.coingecko.com/",
        "Connection": "keep-alive",
    }

    # Rotate proxies if provided, else no proxy
    proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None

    response = requests.get(url, headers=headers, proxies=proxy, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json())


def get_fully_diluted_symbols(threshold: float = 0.85) -> List[str]:
    """Return a list of coin symbols that meet or exceed the fully-diluted percentage threshold."""
    dfs = []
    for page in (1, 2):
        dfs.append(_fetch_market_page(page))
        # Random delay between 1.0 and 3.0 seconds to reduce request fingerprinting
        time.sleep(random.uniform(1.0, 3.0))

    df = pd.concat(dfs)
    df = df.dropna(subset=["max_supply"])
    df["fd_pct"] = df["circulating_supply"] / df["max_supply"]

    filtered = df.loc[df["fd_pct"] >= threshold, ["symbol"]]

    return filtered["symbol"].str.lower().tolist()


def _fetch_full_dataset() -> pd.DataFrame:
    """Fetch the top 500 coins (two pages * 250) and compute fd_pct."""
    dfs = []
    for page in (1, 2):
        dfs.append(_fetch_market_page(page))
        # Light random delay to reduce likelihood of being rate-limited
        time.sleep(random.uniform(0.8, 2.0))

    df = pd.concat(dfs, ignore_index=True)

    # Only consider coins with max_supply defined, because fd_pct cannot be computed otherwise
    df = df.dropna(subset=["max_supply"])
    df["fd_pct"] = df["circulating_supply"] / df["max_supply"]

    # Keep numeric percentage 0-100 as a convenience column
    df["fd_pct_percent"] = (df["fd_pct"] * 100).round(2)

    # Replace inf/-inf with NaN so they become null in JSON
    df.replace([np.inf, -np.inf], pd.NA, inplace=True)

    return df


def _build_threshold_cache(dataset: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Pre-compute lists of coins meeting each 5-percent threshold (0–100)."""
    cache: Dict[int, List[Dict[str, Any]]] = {}
    for threshold in range(0, 101, 5):
        pct = threshold / 100
        cache[threshold] = sorted(
            (coin for coin in dataset if coin["fd_pct"] >= pct),
            key=lambda c: c.get("market_cap_rank", 1e9)
        )
    return cache


def update_fully_diluted_cache() -> None:
    """Fetch full dataset, persist it to disk, and rebuild threshold caches."""
    global _cached_dataset, _threshold_cache, _last_update

    with _cache_lock:
        try:
            df = _fetch_full_dataset()

            # Persist complete data to JSON (records orientation) – this automatically
            # converts NaN to null so the stored file is valid JSON.
            json_records = df.to_json(orient="records")
            DATA_FILE.write_text(json_records, encoding="utf-8")

            # Build in-memory dataset from the same JSON so NaN → None.
            dataset = json.loads(json_records)

            _cached_dataset = dataset
            _threshold_cache = _build_threshold_cache(dataset)
            _last_update = time.time()
        except Exception as exc:
            print(f"[fully_diluted_service] Failed to refresh cache: {exc}")


def get_cached_coins_by_threshold(threshold: int) -> List[Dict[str, Any]]:
    """Return cached coins whose fd_pct >= threshold/100.

    If cache is empty (e.g., app just started), an empty list is returned.
    """
    # Clamp to valid multiples of 5 between 0 and 100 to guard against incorrect calls
    if threshold not in range(0, 101, 5):
        raise ValueError("Threshold must be one of 0, 5, 10, …, 100")

    return list(_threshold_cache.get(threshold, []))
