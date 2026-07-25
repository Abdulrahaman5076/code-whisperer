"""
Code Whisperer - Validators & Rate Limiter
Input validation and rate limiting utilities.
"""

import time
from collections import defaultdict
from typing import Tuple, Optional
from django.conf import settings

class RateLimiter:
    """
    Sliding window rate limiter using in-memory storage.
    Tracks requests per client IP address.
    """
    
    def __init__(self):
        self._requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a request from this IP is allowed.
        Returns True if under limit, False if exceeded.
        """
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
        
        # Clean old requests for this IP
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]
        
        # Check limit
        if len(self._requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            return False
        
        # Record this request
        self._requests[client_ip].append(now)
        return True
    
    def remaining_requests(self, client_ip: str) -> int:
        """Get remaining allowed requests for this IP."""
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]
        return max(0, settings.RATE_LIMIT_REQUESTS - len(self._requests[client_ip]))
    
    def reset_for_ip(self, client_ip: str):
        """Reset rate limiter for a specific IP."""
        if client_ip in self._requests:
            del self._requests[client_ip]

def validate_code_length(code: str) -> Tuple[bool, Optional[str]]:
    """Validate code length against configured limits."""
    if not code or not code.strip():
        return False, "Code cannot be empty."
    
    if len(code) > settings.MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {settings.MAX_CODE_LENGTH:,} characters."
    
    if len(code.splitlines()) > settings.MAX_CODE_LINES:
        return False, f"Code exceeds maximum of {settings.MAX_CODE_LINES:,} lines."
    
    return True, None

def sanitize_code(code: str) -> str:
    """Basic code sanitization to prevent obvious injection."""
    # Remove null bytes
    code = code.replace('\x00', '')
    # Limit to printable characters mostly
    code = ''.join(char for char in code if ord(char) >= 32 or char in '\n\r\t')
    return code