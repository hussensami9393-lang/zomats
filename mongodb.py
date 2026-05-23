from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from config.settings import config
import asyncio


class Database:
    """
    Main Database Manager - MongoDB with Motor (Async)
    Handles all database operations for the AI Bot
    """
    
    _instance = None
    client: Optional[AsyncIOMotorClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(config.MONGODB_URI)
            self.db = self.client[config.MONGODB_DB_NAME]
            
            # Collections
            self.users = self.db.users
            self.conversations = self.db.conversations
            self.messages = self.db.messages
            self.subscriptions = self.db.subscriptions
            self.usage_stats = self.db.usage_stats
            self.payments = self.db.payments
            self.banned_users = self.db.banned_users
            self.admin_logs = self.db.admin_logs
            self.image_generations = self.db.image_generations
            
            # Create indexes
            await self._create_indexes()
            
            logger.success("✅ Connected to MongoDB successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        # Users indexes
        await self.users.create_indexes([
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("username", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("subscription.type", ASCENDING)]),
        ])
        
        # Messages indexes
        await self.messages.create_indexes([
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
        ])
        
        # Usage stats indexes
        await self.usage_stats.create_indexes([
            IndexModel([("user_id", ASCENDING), ("date", DESCENDING)]),
        ])
        
        logger.info("📊 Database indexes created")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 Disconnected from MongoDB")

    # ============================
    # User Operations
    # ============================
    
    async def get_or_create_user(self, user_data: Dict) -> Dict:
        """Get existing user or create new one"""
        user_id = user_data["user_id"]
        
        existing = await self.users.find_one({"user_id": user_id})
        
        if existing:
            # Update last seen and username
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "last_seen": datetime.utcnow(),
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "language_code": user_data.get("language_code", "en"),
                }}
            )
            return existing
        
        # Create new user
        new_user = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "language_code": user_data.get("language_code", "en"),
            "language_preference": user_data.get("language_code", "ar"),
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "subscription": {
                "type": "free",
                "expires_at": None,
                "started_at": None,
            },
            "settings": {
                "ai_model": "gpt-4o",
                "language": user_data.get("language_code", "ar"),
                "notifications": True,
                "voice_response": False,
            },
            "stats": {
                "total_messages": 0,
                "total_images": 0,
                "total_tokens": 0,
            },
            "is_banned": False,
            "is_admin": user_id in config.ADMIN_IDS,
            "referral_code": f"REF{user_id}",
            "referred_by": None,
        }
        
        await self.users.insert_one(new_user)
        logger.info(f"👤 New user created: {user_id} (@{user_data.get('username')})")
        return new_user
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return await self.users.find_one({"user_id": user_id})
    
    async def update_user(self, user_id: int, update_data: Dict):
        """Update user data"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        user = await self.users.find_one({"user_id": user_id, "is_banned": True})
        return user is not None
    
    async def ban_user(self, user_id: int, reason: str, admin_id: int):
        """Ban a user"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": True, "ban_reason": reason}}
        )
        await self.admin_logs.insert_one({
            "action": "ban_user",
            "target_user_id": user_id,
            "admin_id": admin_id,
            "reason": reason,
            "timestamp": datetime.utcnow()
        })
    
    async def unban_user(self, user_id: int, admin_id: int):
        """Unban a user"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": False, "ban_reason": None}}
        )
    
    # ============================
    # Subscription Operations
    # ============================
    
    async def upgrade_subscription(self, user_id: int, plan: str, duration_days: int):
        """Upgrade user subscription"""
        expires_at = datetime.utcnow() + timedelta(days=duration_days)
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "subscription.type": plan,
                "subscription.expires_at": expires_at,
                "subscription.started_at": datetime.utcnow(),
            }}
        )
        await self.subscriptions.insert_one({
            "user_id": user_id,
            "plan": plan,
            "duration_days": duration_days,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        })
        logger.info(f"⭐ User {user_id} upgraded to {plan} for {duration_days} days")
    
    async def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium subscription"""
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return False
        
        sub = user.get("subscription", {})
        if sub.get("type") == "free":
            return False
        
        expires_at = sub.get("expires_at")
        if expires_at and datetime.utcnow() < expires_at:
            return True
        
        # Subscription expired, downgrade
        if expires_at and datetime.utcnow() >= expires_at:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"subscription.type": "free"}}
            )
        
        return False
    
    # ============================
    # Usage Tracking
    # ============================
    
    async def track_usage(self, user_id: int, usage_type: str, tokens: int = 0):
        """Track user usage for rate limiting"""
        today = datetime.utcnow().date().isoformat()
        
        await self.usage_stats.update_one(
            {"user_id": user_id, "date": today},
            {
                "$inc": {
                    f"{usage_type}_count": 1,
                    "total_tokens": tokens,
                },
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        # Update user total stats
        await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {
                f"stats.total_{usage_type}s": 1,
                "stats.total_tokens": tokens,
            }}
        )
    
    async def get_daily_usage(self, user_id: int) -> Dict:
        """Get user's usage for today"""
        today = datetime.utcnow().date().isoformat()
        usage = await self.usage_stats.find_one({"user_id": user_id, "date": today})
        return usage or {"message_count": 0, "image_count": 0, "total_tokens": 0}
    
    async def check_rate_limit(self, user_id: int, usage_type: str) -> bool:
        """Check if user has exceeded daily limits. Returns True if allowed."""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        is_prem = await self.is_premium(user_id)
        usage = await self.get_daily_usage(user_id)
        
        if usage_type == "message":
            limit = config.PREMIUM_DAILY_MESSAGES if is_prem else config.FREE_DAILY_MESSAGES
            current = usage.get("message_count", 0)
        elif usage_type == "image":
            limit = config.PREMIUM_DAILY_IMAGES if is_prem else config.FREE_DAILY_IMAGES
            current = usage.get("image_count", 0)
        else:
            return True
        
        return current < limit
    
    # ============================
    # Conversation Memory
    # ============================
    
    async def save_message(self, user_id: int, role: str, content: str, 
                           session_id: str = None, metadata: Dict = None):
        """Save a message to conversation history"""
        await self.messages.insert_one({
            "user_id": user_id,
            "session_id": session_id or str(user_id),
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        })
    
    async def get_conversation_history(self, user_id: int, session_id: str = None, 
                                        limit: int = None) -> List[Dict]:
        """Get conversation history for context"""
        limit = limit or config.MAX_CONTEXT_MESSAGES
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id
        
        cursor = self.messages.find(query).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        return list(reversed(messages))
    
    async def clear_conversation(self, user_id: int):
        """Clear user's conversation history"""
        await self.messages.delete_many({"user_id": user_id})
    
    # ============================
    # Admin Statistics
    # ============================
    
    async def get_bot_statistics(self) -> Dict:
        """Get overall bot statistics for admin"""
        total_users = await self.users.count_documents({})
        premium_users = await self.users.count_documents({"subscription.type": {"$ne": "free"}})
        banned_users = await self.users.count_documents({"is_banned": True})
        
        today = datetime.utcnow().date().isoformat()
        active_today = await self.usage_stats.count_documents({"date": today})
        
        # New users today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = await self.users.count_documents({"created_at": {"$gte": today_start}})
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "free_users": total_users - premium_users,
            "banned_users": banned_users,
            "active_today": active_today,
            "new_today": new_today,
        }
    
    async def get_all_users(self, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Get all users with pagination"""
        cursor = self.users.find({}).sort("created_at", DESCENDING).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)


# Global database instance
db = Database()
