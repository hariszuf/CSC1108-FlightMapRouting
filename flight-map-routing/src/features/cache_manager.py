# src/features/cache_manager.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

class CacheManager:
    """Cache manager for frequently accessed routes"""
    
    def __init__(self, use_redis=False, default_ttl=3600):
        self.cache: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}  # timestamp expiry
        self.use_redis = use_redis
        self.default_ttl = default_ttl  # 1 hour default TTL
        
    def get_shortest_path(self, src: str, dst: str, mode: str) -> Optional[Any]:
        """Get cached route if available and not expired"""
        key = self._make_key(src, dst, mode)
        
        # Check in-memory cache
        if key in self.cache:
            # Check if expired
            if key in self.expiry and time.time() > self.expiry[key]:
                del self.cache[key]
                del self.expiry[key]
                return None
            return self.cache[key]
        
        return None
    
    def cache_route(self, src: str, dst: str, mode: str, data: Any, ttl: int = None):
        """Cache a route with optional TTL"""
        key = self._make_key(src, dst, mode)
        expiry = time.time() + (ttl or self.default_ttl)
        
        # Store in-memory
        self.cache[key] = data
        self.expiry[key] = expiry
    
    def _make_key(self, src: str, dst: str, mode: str) -> str:
        """Create cache key"""
        return f"{src}:{dst}:{mode}"
    
    def clear_expired(self):
        """Clear expired cache entries"""
        now = time.time()
        expired_keys = [k for k, v in self.expiry.items() if now > v]
        for k in expired_keys:
            self.cache.pop(k, None)
            self.expiry.pop(k, None)
    
    def clear_all(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.expiry.clear()