"""
Start Handler - Welcome message and user onboarding
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from database.mongodb import db
from utils.keyboards import keyboards
from utils.messages import Messages
from config.settings import config


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    try:
        # Get or create user in database
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code or "en",
        }
        
        db_user = await db.get_or_create_user(user_data)
        
        # Detect language preference
        lang = db_user.get("language_preference") or db_user.get("language_code", "en")
        if lang not in ["ar", "en"]:
            lang = "ar"  # Default to Arabic
        
        # Handle referral
        if context.args:
            referral_code = context.args[0]
            if referral_code.startswith("REF") and not db_user.get("referred_by"):
                await db.update_user(user.id, {"referred_by": referral_code})
        
        # Get username display
        name = user.first_name or user.username or "صديق"
        
        # Build welcome message
        welcome_text = Messages.get(
            "WELCOME",
            lang,
            name=name,
            free_messages=config.FREE_DAILY_MESSAGES,
            free_images=config.FREE_DAILY_IMAGES,
        )
        
        # Send welcome with main menu
        if chat.type == "private":
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboards.main_menu(lang),
                parse_mode="Markdown"
            )
        
        logger.info(f"👋 User {user.id} (@{user.username}) started the bot")
        
    except Exception as e:
        logger.error(f"Start handler error: {e}")
        await update.message.reply_text(
            "🌟 **مرحباً بك في NexusAI Bot!**\n\nاضغط /menu للقائمة الرئيسية",
            parse_mode="Markdown"
        )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    user = update.effective_user
    
    try:
        db_user = await db.get_user(user.id)
        lang = "ar"
        if db_user:
            lang = db_user.get("language_preference", "ar")
        
        await update.message.reply_text(
            "🏠 **القائمة الرئيسية**" if lang == "ar" else "🏠 **Main Menu**",
            reply_markup=keyboards.main_menu(lang),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Menu handler error: {e}")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    
    help_text_ar = """📚 **دليل الاستخدام - NexusAI Bot**

**الأوامر المتاحة:**
/start - تشغيل البوت
/menu - القائمة الرئيسية
/help - هذا الدليل
/clear - مسح سجل المحادثة
/tts [نص] - تحويل نص إلى صوت
/profile - معلومات حسابك
/premium - الترقية للبريميوم
/stats - إحصائياتك

**كيفية الاستخدام:**
1. استخدم القائمة الرئيسية للتنقل بين الميزات
2. أرسل رسائل مباشرة للمحادثة الذكية
3. أرسل صوراً للتحليل أو المعالجة
4. أرسل ملفات للتلخيص

**ملاحظات:**
• الحد اليومي المجاني: 10 رسائل، 3 صور
• البريميوم: 500 رسالة، 50 صورة
• يمكن إرسال صور حتى 10MB

للدعم: @NexusAI_Support"""

    help_text_en = """📚 **User Guide - NexusAI Bot**

**Available Commands:**
/start - Start the bot
/menu - Main menu
/help - This guide
/clear - Clear conversation history
/tts [text] - Convert text to voice
/profile - Your account info
/premium - Upgrade to Premium
/stats - Your statistics

**How to use:**
1. Use the main menu to navigate features
2. Send direct messages for smart chat
3. Send images for analysis or processing
4. Send files for summarization

**Notes:**
• Free daily limit: 10 messages, 3 images
• Premium: 500 messages, 50 images
• Can send images up to 10MB

Support: @NexusAI_Support"""
    
    try:
        db_user = await db.get_user(user.id)
        lang = db_user.get("language_preference", "ar") if db_user else "ar"
        
        help_text = help_text_ar if lang == "ar" else help_text_en
        
        await update.message.reply_text(
            help_text,
            reply_markup=keyboards.back_to_menu(lang),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Help handler error: {e}")
        await update.message.reply_text(help_text_ar, parse_mode="Markdown")


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command - Show user profile"""
    user = update.effective_user
    
    try:
        db_user = await db.get_user(user.id)
        if not db_user:
            await update.message.reply_text("❌ لم يتم العثور على ملفك الشخصي. استخدم /start أولاً")
            return
        
        lang = db_user.get("language_preference", "ar")
        
        sub = db_user.get("subscription", {})
        sub_type = sub.get("type", "free")
        is_prem = await db.is_premium(user.id)
        
        stats = db_user.get("stats", {})
        usage = await db.get_daily_usage(user.id)
        
        if lang == "ar":
            profile_text = f"""👤 **ملفك الشخصي**

**المعلومات:**
• الاسم: {user.first_name or 'N/A'}
• المعرف: @{user.username or 'N/A'}
• ID: `{user.id}`
• الاشتراك: {'⭐ بريميوم' if is_prem else '🆓 مجاني'}
• رمز الإحالة: `{db_user.get('referral_code', 'N/A')}`

**إحصائيات اليوم:**
• الرسائل المستخدمة: {usage.get('message_count', 0)}
• الصور المنشأة: {usage.get('image_count', 0)}

**الإحصائيات الكلية:**
• إجمالي الرسائل: {stats.get('total_messages', 0):,}
• إجمالي الصور: {stats.get('total_images', 0):,}"""
        else:
            profile_text = f"""👤 **Your Profile**

**Information:**
• Name: {user.first_name or 'N/A'}
• Username: @{user.username or 'N/A'}
• ID: `{user.id}`
• Subscription: {'⭐ Premium' if is_prem else '🆓 Free'}
• Referral Code: `{db_user.get('referral_code', 'N/A')}`

**Today's Usage:**
• Messages used: {usage.get('message_count', 0)}
• Images generated: {usage.get('image_count', 0)}

**Total Statistics:**
• Total messages: {stats.get('total_messages', 0):,}
• Total images: {stats.get('total_images', 0):,}"""
        
        await update.message.reply_text(
            profile_text,
            reply_markup=keyboards.back_to_menu(lang),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Profile handler error: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب ملفك الشخصي")
