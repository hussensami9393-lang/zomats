# 🤖 AI Bot Configuration
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Optional

load_dotenv()

@dataclass
class BotConfig:
    # ============================
    # Telegram Configuration
    # ============================
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    ADMIN_IDS: list = field(default_factory=lambda: [
        int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])

    # ============================
    # AI API Keys
    # ============================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_VISION_MODEL: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
    
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    STABILITY_API_KEY: str = os.getenv("STABILITY_API_KEY", "")
    
    # Free Image Generation (no key needed)
    POLLINATIONS_API: str = "https://image.pollinations.ai/prompt"
    
    # ============================
    # Database Configuration
    # ============================
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_bot_db")
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ============================
    # Subscription Plans
    # ============================
    FREE_DAILY_MESSAGES: int = 10
    FREE_DAILY_IMAGES: int = 3
    PREMIUM_DAILY_MESSAGES: int = 500
    PREMIUM_DAILY_IMAGES: int = 50
    
    FREE_MAX_TOKENS: int = 1000
    PREMIUM_MAX_TOKENS: int = 4000
    
    # ============================
    # Security
    # ============================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Rate Limiting
    RATE_LIMIT_MESSAGES: int = 30  # per minute
    RATE_LIMIT_IMAGES: int = 5   # per minute
    SPAM_THRESHOLD: int = 20     # messages per minute = spam
    
    # ============================
    # App Configuration
    # ============================
    PORT: int = int(os.getenv("PORT", 8080))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Supported Languages
    SUPPORTED_LANGUAGES: list = field(default_factory=lambda: [
        "ar", "en", "fr", "es", "de", "it", "pt", "ru", "zh", "ja", "ko", "tr"
    ])
    
    BOT_NAME: str = "🤖 NexusAI Bot"
    BOT_VERSION: str = "2.0.0"
    
    # Max file sizes
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_AUDIO_SIZE_MB: int = 25
    MAX_FILE_SIZE_MB: int = 20
    
    # Context memory
    MAX_CONTEXT_MESSAGES: int = 20
    
    # Admin Panel
    ADMIN_PANEL_URL: str = os.getenv("ADMIN_PANEL_URL", "http://localhost:8080")
    
    # Payments (Telegram Stars / TON)
    PAYMENT_PROVIDER_TOKEN: str = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    PREMIUM_MONTHLY_PRICE: int = 499  # in cents = $4.99
    PREMIUM_YEARLY_PRICE: int = 3999  # in cents = $39.99

config = BotConfig()
