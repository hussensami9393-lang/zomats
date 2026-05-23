"""
Anti-Spam Middleware & Security
Protects the bot from abuse, spam, and exploitation
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Set, Deque
from loguru import logger
from config.settings import config
from database.mongodb import db


class RateLimiter:
    """
    Token bucket rate limiter for spam protection
    """
    
    def __init__(self):
        self._message_timestamps: Dict[int, Deque] = defaultdict(lambda: deque(maxlen=100))
        self._blocked_users: Set[int] = set()
        self._warning_count: Dict[int, int] = defaultdict(int)
        self._last_message: Dict[int, float] = {}
    
    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is sending messages too fast"""
        now = time.time()
        user_times = self._message_timestamps[user_id]
        
        # Add current timestamp
        user_times.append(now)
        
        # Count messages in last 60 seconds
        one_minute_ago = now - 60
        recent_messages = sum(1 for t in user_times if t > one_minute_ago)
        
        if recent_messages > config.SPAM_THRESHOLD:
            self._warning_count[user_id] += 1
            
            if self._warning_count[user_id] >= 3:
                self._blocked_users.add(user_id)
                logger.warning(f"🚫 User {user_id} auto-blocked for spam")
            
            return True
        
        return False
    
    def is_blocked(self, user_id: int) -> bool:
        """Check if user is blocked in memory"""
        return user_id in self._blocked_users
    
    def unblock_user(self, user_id: int):
        """Unblock a user"""
        self._blocked_users.discard(user_id)
        self._warning_count[user_id] = 0
    
    def get_wait_time(self, user_id: int) -> float:
        """Get how long user needs to wait"""
        user_times = self._message_timestamps[user_id]
        if not user_times:
            return 0
        
        oldest = user_times[0]
        wait = max(0, 60 - (time.time() - oldest))
        return wait


class SecurityMiddleware:
    """
    Security middleware for the Telegram bot
    - Rate limiting
    - Spam detection
    - Ban checking
    - Input sanitization
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self._flood_detect: Dict[int, list] = defaultdict(list)
    
    async def check_user(self, user_id: int, user_data: dict = None) -> tuple[bool, str]:
        """
        Comprehensive user security check
        Returns (is_allowed, reason_if_blocked)
        """
        # Check in-memory block first (faster)
        if self.rate_limiter.is_blocked(user_id):
            return False, "blocked"
        
        # Check rate limit
        if self.rate_limiter.is_rate_limited(user_id):
            return False, "rate_limited"
        
        # Check database ban
        try:
            if await db.is_user_banned(user_id):
                return False, "banned"
        except Exception:
            pass
        
        return True, "ok"
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    
    async def log_suspicious_activity(self, user_id: int, activity_type: str, details: str):
        """Log suspicious activity for admin review"""
        try:
            await db.admin_logs.insert_one({
                "type": "suspicious_activity",
                "user_id": user_id,
                "activity_type": activity_type,
                "details": details,
                "timestamp": __import__("datetime").datetime.utcnow()
            })
        except Exception:
            pass


# Global instances
rate_limiter = RateLimiter()
security = SecurityMiddleware()
