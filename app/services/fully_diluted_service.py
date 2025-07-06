"""
Fully diluted market cap service for fetching and caching cryptocurrency data.
"""
import requests
import json
import os
import logging
import time  # NEW: for polite rate-limiting
from typing import List, Dict, Any, Optional
from datetime import datetime
from threading import Lock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fully_diluted_service')

# Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
CACHE_FILE = "fully_diluted_cache.json"
CACHE_EXPIRY_HOURS = 24  # Cache expires after 24 hours

# Cache variables
_cached_data: List[Dict[str, Any]] = []
_threshold_cache: Dict[int, List[Dict[str, Any]]] = {}
_last_update: float = 0.0
_cache_lock: Lock = Lock()

class FullyDilutedService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_coingecko_data(self, pages: int = 2, delay: float = 1.2) -> List[Dict[str, Any]]:
        """Fetch cryptocurrency data from multiple CoinGecko pages.

        Args:
            pages: How many pages of 250 coins to request (CoinGecko max page size).
            delay: Seconds to wait between requests to respect API rate limits.
        """
        try:
            all_coins: List[Dict[str, Any]] = []

            for page in range(1, pages + 1):
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 250,  # CoinGecko maximum page size
                    'page': page,
                    'sparkline': 'false',
                    'price_change_percentage': '24h'
                }

                response = self.session.get(COINGECKO_API_URL, params=params, timeout=30)
                response.raise_for_status()

                page_data = response.json()
                logger.info(f"Fetched {len(page_data)} coins from CoinGecko page {page}")
                all_coins.extend(page_data)

                # If we received fewer than requested items, we've reached the end.
                if len(page_data) < 250:
                    break

                # Be courteous – avoid hitting the rate limit.
                time.sleep(delay)

            logger.info(f"Total coins fetched across pages: {len(all_coins)}")

            # Process the data to calculate fully diluted percentage
            processed_data: List[Dict[str, Any]] = []
            for coin in all_coins:
                # Skip wrapped or staked derivative tokens (e.g., wrapped-bitcoin)
                if any(sub in coin_id for sub in ('wrapped-', 'staked-', 'dollar', 'usd')):
                    continue

                circulating_supply = coin.get('circulating_supply')
                max_supply = coin.get('max_supply') or coin.get('total_supply')

                # Skip coins without supply information
                if not circulating_supply or not max_supply:
                    continue

                fd_pct = circulating_supply / max_supply  # fraction 0-1

                processed_data.append({
                    'market_cap_rank': coin.get('market_cap_rank', 0),
                    'id': coin['id'],
                    'symbol': coin['symbol'].upper(),
                    'circulating_supply': circulating_supply,
                    'max_supply': max_supply,
                    'fd_pct': fd_pct
                })

            logger.info(f"Processed {len(processed_data)} coins with valid supply data")
            return processed_data

        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {str(e)}")
            return []

# Global service instance
fully_diluted_service = FullyDilutedService()

def update_fully_diluted_cache() -> None:
    """Update the cached fully diluted data"""
    global _cached_data, _threshold_cache, _last_update
    
    with _cache_lock:
        try:
            # Fetch fresh data
            data = fully_diluted_service.fetch_coingecko_data()
            
            if data:
                _cached_data = data
                _last_update = datetime.now().timestamp()
                
                # Pre-compute threshold cache for all thresholds (0, 5, 10, ..., 100)
                _threshold_cache = {}
                for threshold in range(0, 101, 5):
                    # Convert threshold percentage to fraction for comparison
                    threshold_fraction = threshold / 100.0
                    _threshold_cache[threshold] = [
                        coin for coin in data 
                        if coin['fd_pct'] >= threshold_fraction
                    ]
                
                # Save to file
                cache_data = {
                    'data': data,
                    'last_update': _last_update,
                    'threshold_cache': _threshold_cache
                }
                
                with open(CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                logger.info(f"Fully diluted cache updated with {len(data)} coins")
                
        except Exception as exc:
            logger.error(f"Failed to refresh fully diluted cache: {exc}")

def load_fully_diluted_cache() -> bool:
    """Load cached data from file"""
    global _cached_data, _threshold_cache, _last_update
    
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                
            _cached_data = cache_data.get('data', [])
            _last_update = cache_data.get('last_update', 0.0)
            _threshold_cache = cache_data.get('threshold_cache', {})
            
            # Convert string keys back to integers
            _threshold_cache = {int(k): v for k, v in _threshold_cache.items()}
            
            logger.info(f"Loaded {len(_cached_data)} coins from cache")
            return True
            
    except Exception as e:
        logger.error(f"Error loading cache: {str(e)}")
        
    return False

def get_cached_coins_by_threshold(threshold: int) -> List[Dict[str, Any]]:
    """
    Get cached coins with fully diluted percentage >= threshold
    
    Args:
        threshold: Minimum fully diluted percentage (0-100, must be multiple of 5)
        
    Returns:
        List of coins meeting the criteria
    """
    # Validate threshold
    if threshold not in range(0, 101, 5):
        raise ValueError("Threshold must be 0, 5, 10, ..., 100")
    
    # Load cache if not loaded
    if not _cached_data:
        load_fully_diluted_cache()
    
    # Check if cache is stale
    if datetime.now().timestamp() - _last_update > CACHE_EXPIRY_HOURS * 3600:
        logger.info("Cache is stale, updating...")
        update_fully_diluted_cache()
    
    # Return cached results
    return _threshold_cache.get(threshold, [])

def get_cached_fully_diluted_data() -> List[Dict[str, Any]]:
    """Return all cached fully diluted data"""
    return list(_cached_data)

def get_cache_last_updated() -> float:
    """Return the timestamp of the last cache update"""
    return _last_update

# Initialize cache on import
if not load_fully_diluted_cache():
    logger.info("No cache found, will update on first request")
