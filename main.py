"""
NexusAI Telegram Bot - Main Entry Point
Supports both Webhook (production/fly.io) and Polling (local dev)
"""
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from loguru import logger

from config.settings import config
from database.mongodb import db
from handlers import (
    start_handler, menu_handler, help_handler, profile_handler,
    callback_handler,
    message_handler, tts_command_handler, clear_command_handler,
    photo_handler, voice_handler, document_handler,
    admin_handler, broadcast_command, ban_user_command,
    unban_user_command, grant_premium_command, users_command,
)
from admin.panel import app as admin_app


# ============================
# Build Telegram Application
# ============================

def build_application() -> Application:
    """Create and configure the Telegram bot application"""
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # ── Commands ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start",   start_handler))
    app.add_handler(CommandHandler("menu",    menu_handler))
    app.add_handler(CommandHandler("help",    help_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("clear",   clear_command_handler))
    app.add_handler(CommandHandler("tts",     tts_command_handler))

    # ── Admin commands ────────────────────────────────────────
    app.add_handler(CommandHandler("admin",     admin_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("ban",       ban_user_command))
    app.add_handler(CommandHandler("unban",     unban_user_command))
    app.add_handler(CommandHandler("premium",   grant_premium_command))
    app.add_handler(CommandHandler("users",     users_command))

    # ── Inline buttons ────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(callback_handler))

    # ── Media ─────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.PHOTO,                 photo_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handler))
    app.add_handler(MessageHandler(filters.Document.ALL,          document_handler))

    # ── Text messages (must be last) ──────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return app


# ============================
# Webhook mode (fly.io / production)
# ============================

ptb_app: Application | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start / stop lifecycle for FastAPI + PTB"""
    global ptb_app

    # Connect DB
    await db.connect()

    # Build & start PTB (initialise + start, but do NOT start polling)
    ptb_app = build_application()
    await ptb_app.initialize()
    await ptb_app.start()

    # Register bot commands in Telegram menu
    await ptb_app.bot.set_my_commands([
        BotCommand("start",   "🚀 تشغيل البوت / Start bot"),
        BotCommand("menu",    "🏠 القائمة الرئيسية / Main menu"),
        BotCommand("help",    "📚 المساعدة / Help"),
        BotCommand("profile", "👤 ملفي الشخصي / My profile"),
        BotCommand("clear",   "🗑️ مسح المحادثة / Clear chat"),
        BotCommand("tts",     "🔊 نص إلى صوت / Text to speech"),
    ])

    # Set webhook
    webhook_url = config.TELEGRAM_WEBHOOK_URL
    if webhook_url:
        await ptb_app.bot.set_webhook(
            url=f"{webhook_url}/webhook",
            allowed_updates=Update.ALL_TYPES,
        )
        logger.success(f"✅ Webhook set → {webhook_url}/webhook")
    else:
        logger.warning("⚠️  TELEGRAM_WEBHOOK_URL not set – webhook NOT registered")

    logger.success("🤖 NexusAI Bot is running (webhook mode)")
    yield

    # ── Shutdown ──────────────────────────────────────────────
    if webhook_url:
        await ptb_app.bot.delete_webhook()
    await ptb_app.stop()
    await ptb_app.shutdown()
    await db.disconnect()
    logger.info("👋 Bot stopped")


# Main FastAPI app (serves the webhook endpoint + admin panel)
web_app = FastAPI(title="NexusAI Bot", lifespan=lifespan)

# Mount admin panel under /admin
web_app.mount("/admin", admin_app)


@web_app.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    """Receive updates from Telegram"""
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@web_app.get("/health")
async def health_check():
    return {"status": "ok", "bot": config.BOT_NAME, "version": config.BOT_VERSION}


# ============================
# Polling mode (local dev)
# ============================

async def run_polling():
    """Run bot in polling mode – for local development only"""
    await db.connect()
    app = build_application()

    await app.bot.set_my_commands([
        BotCommand("start",   "🚀 تشغيل البوت"),
        BotCommand("menu",    "🏠 القائمة الرئيسية"),
        BotCommand("help",    "📚 المساعدة"),
        BotCommand("profile", "👤 ملفي الشخصي"),
        BotCommand("clear",   "🗑️ مسح المحادثة"),
        BotCommand("tts",     "🔊 نص إلى صوت"),
    ])

    logger.success("🤖 NexusAI Bot is running (polling mode)…")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


# ============================
# Entrypoint
# ============================

if __name__ == "__main__":
    mode = os.getenv("BOT_MODE", "webhook").lower()

    if mode == "polling":
        # Local dev
        asyncio.run(run_polling())
    else:
        # Production / fly.io – launch uvicorn programmatically
        import uvicorn
        uvicorn.run(
            "main:web_app",
            host="0.0.0.0",
            port=config.PORT,
            log_level="info",
        )
