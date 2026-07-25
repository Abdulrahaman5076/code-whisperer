"""
Code Whisperer - Cache Utility
Simple in-memory cache for analysis results.
"""

import time
import hashlib
from typing import Optional, Dict, Any
from django.conf import settings

class AnalysisCache:
    """
    In-memory cache with TTL and size limits.
    Avoids redundant processing of identical code submissions.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 200
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached item if it exists and hasn't expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires_at']:
                # Move to end (most recently used)
                value = entry['data']
                del self._cache[key]
                self._cache[key] = entry
                return value
            else:
                # Expired
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Dict[str, Any], ttl: int = None):
        """Store data in cache with TTL."""
        if ttl is None:
            ttl = settings.CACHE_TTL_SECONDS
        
        # Remove oldest entry if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = {
            'data': data,
            'expires_at': time.time() + ttl,
            'created_at': time.time(),
        }
    
    def make_key(self, code: str) -> str:
        """Generate a cache key from code content."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def clear_expired(self):
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items() if now >= v['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def clear_all(self):
        """Clear the entire cache."""
        self._cache.clear()
    
    @property
    def size(self) -> int:
        """Current number of cached items."""
        return len(self._cache)