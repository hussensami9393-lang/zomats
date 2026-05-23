"""
Callback Query Handler - Handles all inline keyboard button presses
Central router for all menu actions
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from database.mongodb import db
from utils.keyboards import keyboards
from utils.messages import Messages
from config.settings import config


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query handler - routes to appropriate handler"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    try:
        db_user = await db.get_user(user.id)
        lang = db_user.get("language_preference", "ar") if db_user else "ar"
        
        # ============================
        # Main Menu
        # ============================
        if data == "main_menu":
            title = "🏠 **القائمة الرئيسية**" if lang == "ar" else "🏠 **Main Menu**"
            await query.edit_message_text(
                title,
                reply_markup=keyboards.main_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Mode Selection
        # ============================
        elif data == "mode_chat":
            context.user_data["mode"] = "chat"
            await query.edit_message_text(
                Messages.get("MODE_CHAT", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_image_gen":
            context.user_data["mode"] = "image_gen"
            await query.edit_message_text(
                Messages.get("MODE_IMAGE_GEN", lang),
                reply_markup=keyboards.image_model_selection(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_bg_remove":
            context.user_data["mode"] = "bg_remove"
            await query.edit_message_text(
                Messages.get("MODE_BG_REMOVE", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_enhance":
            context.user_data["mode"] = "enhance"
            await query.edit_message_text(
                Messages.get("MODE_ENHANCE", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_analyze":
            context.user_data["mode"] = "analyze"
            await query.edit_message_text(
                Messages.get("MODE_ANALYZE", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_tryon":
            context.user_data["mode"] = "tryon"
            context.user_data["tryon_step"] = 1
            await query.edit_message_text(
                Messages.get("MODE_TRYON", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_code":
            context.user_data["mode"] = "code"
            await query.edit_message_text(
                Messages.get("MODE_CODE", lang),
                reply_markup=keyboards.code_options(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_translate":
            context.user_data["mode"] = "translate"
            await query.edit_message_text(
                Messages.get("MODE_TRANSLATE", lang),
                reply_markup=keyboards.translate_languages(),
                parse_mode="Markdown"
            )
        
        elif data == "mode_summarize":
            context.user_data["mode"] = "summarize"
            await query.edit_message_text(
                Messages.get("MODE_SUMMARIZE", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_social":
            context.user_data["mode"] = "social"
            await query.edit_message_text(
                Messages.get("MODE_SOCIAL", lang),
                reply_markup=keyboards.social_platforms(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_projects":
            context.user_data["mode"] = "projects"
            await query.edit_message_text(
                Messages.get("MODE_PROJECTS", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "mode_voice":
            context.user_data["mode"] = "voice"
            await query.edit_message_text(
                Messages.get("MODE_VOICE", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Image Model Selection
        # ============================
        elif data.startswith("img_"):
            model_map = {
                "img_pollinations": "pollinations",
                "img_dalle": "dalle",
                "img_stability": "stability",
                "img_replicate": "replicate",
            }
            model = model_map.get(data, "pollinations")
            context.user_data["image_model"] = model
            context.user_data["mode"] = "image_gen"
            
            model_names = {
                "pollinations": "Pollinations AI (🆓 مجاني)",
                "dalle": "DALL-E 3 (OpenAI)",
                "stability": "Stability AI",
                "replicate": "Replicate"
            }
            
            msg = f"✅ **تم اختيار {model_names[model]}**\n\n" if lang == "ar" else f"✅ **Selected {model_names[model]}**\n\n"
            msg += Messages.get("MODE_IMAGE_GEN", lang)
            
            await query.edit_message_text(
                msg,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Code Sub-options
        # ============================
        elif data.startswith("code_"):
            sub_mode = data.replace("code_", "")
            context.user_data["code_submode"] = sub_mode
            context.user_data["mode"] = "code"
            
            prompts = {
                "write": {
                    "ar": "💻 أخبرني بلغة البرمجة والمهمة التي تريد كتابة كودها:\n\n**مثال:** اكتب كود Python لقراءة ملف CSV وحساب المتوسط",
                    "en": "💻 Tell me the programming language and task you want code for:\n\n**Example:** Write Python code to read a CSV file and calculate the average"
                },
                "explain": {
                    "ar": "🔍 أرسل الكود الذي تريد شرحه:",
                    "en": "🔍 Send the code you want explained:"
                },
                "debug": {
                    "ar": "🐛 أرسل الكود مع رسالة الخطأ:",
                    "en": "🐛 Send the code along with the error message:"
                },
                "optimize": {
                    "ar": "⚡ أرسل الكود الذي تريد تحسينه:",
                    "en": "⚡ Send the code you want optimized:"
                },
            }
            
            prompt = prompts.get(sub_mode, {}).get(lang, prompts.get(sub_mode, {}).get("ar", ""))
            
            await query.edit_message_text(
                prompt,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Translation Language Selection
        # ============================
        elif data.startswith("translate_"):
            target_lang = data.replace("translate_", "")
            context.user_data["translate_to"] = target_lang
            context.user_data["mode"] = "translate_ready"
            
            lang_names = {
                "ar": "العربية 🇸🇦", "en": "English 🇺🇸", "fr": "Français 🇫🇷",
                "de": "Deutsch 🇩🇪", "es": "Español 🇪🇸", "it": "Italiano 🇮🇹",
                "ru": "Русский 🇷🇺", "zh": "中文 🇨🇳", "ja": "日本語 🇯🇵",
                "ko": "한국어 🇰🇷", "tr": "Türkçe 🇹🇷", "pt": "Português 🇵🇹"
            }
            
            target_name = lang_names.get(target_lang, target_lang)
            
            msg = f"🌍 **الترجمة إلى: {target_name}**\n\nأرسل النص الذي تريد ترجمته:" if lang == "ar" else f"🌍 **Translating to: {target_name}**\n\nSend the text you want to translate:"
            
            await query.edit_message_text(
                msg,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Social Media Platform Selection
        # ============================
        elif data.startswith("social_"):
            platform = data.replace("social_", "")
            context.user_data["social_platform"] = platform
            context.user_data["mode"] = "social_ready"
            
            platform_names = {
                "instagram": "Instagram 📸",
                "twitter": "Twitter/X 🐦",
                "linkedin": "LinkedIn 💼",
                "tiktok": "TikTok 🎵",
                "youtube": "YouTube ▶️",
                "facebook": "Facebook 📘",
            }
            
            platform_name = platform_names.get(platform, platform)
            
            msg = f"📱 **محتوى {platform_name}**\n\nأخبرني عن الموضوع الذي تريد إنشاء محتوى عنه:" if lang == "ar" else f"📱 **{platform_name} Content**\n\nTell me the topic you want to create content about:"
            
            await query.edit_message_text(
                msg,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Settings
        # ============================
        elif data == "settings":
            await query.edit_message_text(
                Messages.get("SETTINGS_MENU", lang),
                reply_markup=keyboards.settings_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "setting_language":
            msg = "🌐 **اختر لغتك المفضلة:**" if lang == "ar" else "🌐 **Choose your preferred language:**"
            await query.edit_message_text(
                msg,
                reply_markup=keyboards.language_selection(),
                parse_mode="Markdown"
            )
        
        elif data.startswith("lang_"):
            new_lang = data.replace("lang_", "")
            await db.update_user(user.id, {"language_preference": new_lang, "settings.language": new_lang})
            
            msg = "✅ **تم تغيير اللغة إلى العربية**" if new_lang == "ar" else "✅ **Language changed to English**"
            await query.edit_message_text(
                msg,
                reply_markup=keyboards.main_menu(new_lang),
                parse_mode="Markdown"
            )
        
        elif data == "clear_history":
            await db.clear_conversation(user.id)
            await query.edit_message_text(
                Messages.get("HISTORY_CLEARED", lang),
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        elif data == "my_stats":
            usage = await db.get_daily_usage(user.id)
            db_user = await db.get_user(user.id)
            stats = db_user.get("stats", {}) if db_user else {}
            is_prem = await db.is_premium(user.id)
            
            if lang == "ar":
                limit_msg = config.PREMIUM_DAILY_MESSAGES if is_prem else config.FREE_DAILY_MESSAGES
                img_limit = config.PREMIUM_DAILY_IMAGES if is_prem else config.FREE_DAILY_IMAGES
                stats_text = f"""📊 **إحصائياتك**

**استخدام اليوم:**
• الرسائل: {usage.get('message_count', 0)} / {limit_msg}
• الصور: {usage.get('image_count', 0)} / {img_limit}

**إجمالي كل الوقت:**
• الرسائل: {stats.get('total_messages', 0):,}
• الصور: {stats.get('total_images', 0):,}

**الاشتراك:** {'⭐ بريميوم' if is_prem else '🆓 مجاني'}"""
            else:
                limit_msg = config.PREMIUM_DAILY_MESSAGES if is_prem else config.FREE_DAILY_MESSAGES
                img_limit = config.PREMIUM_DAILY_IMAGES if is_prem else config.FREE_DAILY_IMAGES
                stats_text = f"""📊 **Your Statistics**

**Today's Usage:**
• Messages: {usage.get('message_count', 0)} / {limit_msg}
• Images: {usage.get('image_count', 0)} / {img_limit}

**All-time Total:**
• Messages: {stats.get('total_messages', 0):,}
• Images: {stats.get('total_images', 0):,}

**Subscription:** {'⭐ Premium' if is_prem else '🆓 Free'}"""
            
            await query.edit_message_text(
                stats_text,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Premium
        # ============================
        elif data == "premium":
            await query.edit_message_text(
                Messages.get("PREMIUM_INFO", lang,
                    free_messages=config.FREE_DAILY_MESSAGES,
                    free_images=config.FREE_DAILY_IMAGES,
                    premium_messages=config.PREMIUM_DAILY_MESSAGES,
                    premium_images=config.PREMIUM_DAILY_IMAGES,
                ),
                reply_markup=keyboards.premium_plans(lang),
                parse_mode="Markdown"
            )
        
        elif data == "compare_plans":
            if lang == "ar":
                compare_text = """📊 **مقارنة الخطط**

| الميزة | مجاني | بريميوم |
|--------|-------|---------|
| الرسائل اليومية | 10 | 500 |
| الصور اليومية | 3 | 50 |
| نموذج AI | GPT-3.5 | GPT-4o + Claude |
| تحسين الصور | ❌ | ✅ |
| Virtual Try-On | ❌ | ✅ |
| أولوية المعالجة | ❌ | ✅ |
| ملفات كبيرة | ❌ | ✅ |
| دعم فوري | ❌ | ✅ |"""
            else:
                compare_text = """📊 **Plan Comparison**

| Feature | Free | Premium |
|---------|------|---------|
| Daily Messages | 10 | 500 |
| Daily Images | 3 | 50 |
| AI Model | GPT-3.5 | GPT-4o + Claude |
| Image Enhancement | ❌ | ✅ |
| Virtual Try-On | ❌ | ✅ |
| Priority Processing | ❌ | ✅ |
| Large Files | ❌ | ✅ |
| Instant Support | ❌ | ✅ |"""
            
            await query.edit_message_text(
                compare_text,
                reply_markup=keyboards.premium_plans(lang),
                parse_mode="Markdown"
            )
        
        # ============================
        # Admin Panel
        # ============================
        elif data == "admin_stats" and user.id in config.ADMIN_IDS:
            stats = await db.get_bot_statistics()
            admin_text = f"""📊 **إحصائيات البوت**

👥 إجمالي المستخدمين: {stats['total_users']:,}
⭐ مستخدمو البريميوم: {stats['premium_users']:,}
🆓 المستخدمون المجانيون: {stats['free_users']:,}
🚫 المحظورون: {stats['banned_users']:,}
📈 نشطون اليوم: {stats['active_today']:,}
🆕 جدد اليوم: {stats['new_today']:,}"""
            
            await query.edit_message_text(
                admin_text,
                reply_markup=keyboards.admin_panel(),
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Callback handler error for {data}: {e}")
        try:
            await query.edit_message_text(
                "❌ حدث خطأ. الرجاء المحاولة مرة أخرى.",
                reply_markup=keyboards.back_to_menu("ar"),
                parse_mode="Markdown"
            )
        except Exception:
            pass
