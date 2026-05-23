"""
Keyboard Layouts and Menus for the AI Bot
All inline keyboards and reply keyboards
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


class Keyboards:
    """All bot keyboards"""
    
    @staticmethod
    def main_menu(language: str = "ar") -> InlineKeyboardMarkup:
        """Main menu with all features"""
        if language == "ar":
            keyboard = [
                [
                    InlineKeyboardButton("🤖 محادثة ذكية", callback_data="mode_chat"),
                    InlineKeyboardButton("🎨 إنشاء صورة", callback_data="mode_image_gen"),
                ],
                [
                    InlineKeyboardButton("✂️ إزالة الخلفية", callback_data="mode_bg_remove"),
                    InlineKeyboardButton("✨ تحسين الصورة", callback_data="mode_enhance"),
                ],
                [
                    InlineKeyboardButton("👗 تغيير الملابس", callback_data="mode_tryon"),
                    InlineKeyboardButton("🔍 تحليل الصورة", callback_data="mode_analyze"),
                ],
                [
                    InlineKeyboardButton("💻 مساعد البرمجة", callback_data="mode_code"),
                    InlineKeyboardButton("🌍 ترجمة النصوص", callback_data="mode_translate"),
                ],
                [
                    InlineKeyboardButton("📝 تلخيص النص", callback_data="mode_summarize"),
                    InlineKeyboardButton("📱 محتوى سوشيال", callback_data="mode_social"),
                ],
                [
                    InlineKeyboardButton("💡 أفكار مشاريع", callback_data="mode_projects"),
                    InlineKeyboardButton("🎤 تحويل صوت", callback_data="mode_voice"),
                ],
                [
                    InlineKeyboardButton("⭐ ترقية للبريميوم", callback_data="premium"),
                    InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
                ],
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🤖 Smart Chat", callback_data="mode_chat"),
                    InlineKeyboardButton("🎨 Generate Image", callback_data="mode_image_gen"),
                ],
                [
                    InlineKeyboardButton("✂️ Remove Background", callback_data="mode_bg_remove"),
                    InlineKeyboardButton("✨ Enhance Image", callback_data="mode_enhance"),
                ],
                [
                    InlineKeyboardButton("👗 Virtual Try-On", callback_data="mode_tryon"),
                    InlineKeyboardButton("🔍 Analyze Image", callback_data="mode_analyze"),
                ],
                [
                    InlineKeyboardButton("💻 Code Assistant", callback_data="mode_code"),
                    InlineKeyboardButton("🌍 Translate", callback_data="mode_translate"),
                ],
                [
                    InlineKeyboardButton("📝 Summarize", callback_data="mode_summarize"),
                    InlineKeyboardButton("📱 Social Content", callback_data="mode_social"),
                ],
                [
                    InlineKeyboardButton("💡 Project Ideas", callback_data="mode_projects"),
                    InlineKeyboardButton("🎤 Voice Convert", callback_data="mode_voice"),
                ],
                [
                    InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                ],
            ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu(language: str = "ar") -> InlineKeyboardMarkup:
        text = "🏠 القائمة الرئيسية" if language == "ar" else "🏠 Main Menu"
        return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data="main_menu")]])
    
    @staticmethod
    def code_options(language: str = "ar") -> InlineKeyboardMarkup:
        if language == "ar":
            keyboard = [
                [
                    InlineKeyboardButton("✍️ كتابة كود", callback_data="code_write"),
                    InlineKeyboardButton("🔍 شرح كود", callback_data="code_explain"),
                ],
                [
                    InlineKeyboardButton("🐛 تصحيح خطأ", callback_data="code_debug"),
                    InlineKeyboardButton("⚡ تحسين كود", callback_data="code_optimize"),
                ],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("✍️ Write Code", callback_data="code_write"),
                    InlineKeyboardButton("🔍 Explain Code", callback_data="code_explain"),
                ],
                [
                    InlineKeyboardButton("🐛 Debug Code", callback_data="code_debug"),
                    InlineKeyboardButton("⚡ Optimize Code", callback_data="code_optimize"),
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def translate_languages() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="translate_ar"),
                InlineKeyboardButton("🇺🇸 English", callback_data="translate_en"),
                InlineKeyboardButton("🇫🇷 Français", callback_data="translate_fr"),
            ],
            [
                InlineKeyboardButton("🇩🇪 Deutsch", callback_data="translate_de"),
                InlineKeyboardButton("🇪🇸 Español", callback_data="translate_es"),
                InlineKeyboardButton("🇮🇹 Italiano", callback_data="translate_it"),
            ],
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="translate_ru"),
                InlineKeyboardButton("🇨🇳 中文", callback_data="translate_zh"),
                InlineKeyboardButton("🇯🇵 日本語", callback_data="translate_ja"),
            ],
            [
                InlineKeyboardButton("🇰🇷 한국어", callback_data="translate_ko"),
                InlineKeyboardButton("🇹🇷 Türkçe", callback_data="translate_tr"),
                InlineKeyboardButton("🇵🇹 Português", callback_data="translate_pt"),
            ],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def social_platforms(language: str = "ar") -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📸 Instagram", callback_data="social_instagram"),
                InlineKeyboardButton("🐦 Twitter/X", callback_data="social_twitter"),
            ],
            [
                InlineKeyboardButton("💼 LinkedIn", callback_data="social_linkedin"),
                InlineKeyboardButton("🎵 TikTok", callback_data="social_tiktok"),
            ],
            [
                InlineKeyboardButton("▶️ YouTube", callback_data="social_youtube"),
                InlineKeyboardButton("📘 Facebook", callback_data="social_facebook"),
            ],
            [InlineKeyboardButton("🏠 القائمة الرئيسية" if language == "ar" else "🏠 Main Menu", 
                                   callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def image_model_selection(language: str = "ar") -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🆓 Pollinations (مجاني)", callback_data="img_pollinations"),
                InlineKeyboardButton("🎨 DALL-E 3", callback_data="img_dalle"),
            ],
            [
                InlineKeyboardButton("⚡ Stability AI", callback_data="img_stability"),
                InlineKeyboardButton("🔮 Replicate", callback_data="img_replicate"),
            ],
            [InlineKeyboardButton("🏠 القائمة الرئيسية" if language == "ar" else "🏠 Main Menu",
                                   callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def premium_plans(language: str = "ar") -> InlineKeyboardMarkup:
        if language == "ar":
            keyboard = [
                [InlineKeyboardButton("⭐ شهري - $4.99", callback_data="buy_monthly")],
                [InlineKeyboardButton("🌟 سنوي - $39.99 (وفر 33%)", callback_data="buy_yearly")],
                [InlineKeyboardButton("📊 مقارنة الخطط", callback_data="compare_plans")],
                [InlineKeyboardButton("🏠 العودة", callback_data="main_menu")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("⭐ Monthly - $4.99", callback_data="buy_monthly")],
                [InlineKeyboardButton("🌟 Yearly - $39.99 (Save 33%)", callback_data="buy_yearly")],
                [InlineKeyboardButton("📊 Compare Plans", callback_data="compare_plans")],
                [InlineKeyboardButton("🏠 Back", callback_data="main_menu")],
            ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu(language: str = "ar") -> InlineKeyboardMarkup:
        if language == "ar":
            keyboard = [
                [
                    InlineKeyboardButton("🌐 اللغة", callback_data="setting_language"),
                    InlineKeyboardButton("🤖 نموذج AI", callback_data="setting_model"),
                ],
                [
                    InlineKeyboardButton("🎤 الردود الصوتية", callback_data="setting_voice"),
                    InlineKeyboardButton("🗑️ مسح المحادثة", callback_data="clear_history"),
                ],
                [
                    InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
                    InlineKeyboardButton("🔑 بياناتي", callback_data="my_profile"),
                ],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🌐 Language", callback_data="setting_language"),
                    InlineKeyboardButton("🤖 AI Model", callback_data="setting_model"),
                ],
                [
                    InlineKeyboardButton("🎤 Voice Responses", callback_data="setting_voice"),
                    InlineKeyboardButton("🗑️ Clear History", callback_data="clear_history"),
                ],
                [
                    InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
                    InlineKeyboardButton("🔑 My Profile", callback_data="my_profile"),
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def language_selection() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="settings")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cancel_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
        text = "❌ إلغاء" if language == "ar" else "❌ Cancel"
        return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data="main_menu")]])
    
    @staticmethod
    def tryon_guide(language: str = "ar") -> InlineKeyboardMarkup:
        if language == "ar":
            keyboard = [
                [InlineKeyboardButton("📤 إرسال صورة الشخص أولاً", callback_data="tryon_start")],
                [InlineKeyboardButton("🏠 العودة", callback_data="main_menu")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("📤 Send Person Photo First", callback_data="tryon_start")],
                [InlineKeyboardButton("🏠 Back", callback_data="main_menu")],
            ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod  
    def admin_panel() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 المستخدمون", callback_data="admin_users"),
            ],
            [
                InlineKeyboardButton("🚫 الحظر", callback_data="admin_ban"),
                InlineKeyboardButton("📢 إرسال جماعي", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton("⭐ منح بريميوم", callback_data="admin_grant_premium"),
                InlineKeyboardButton("📋 السجلات", callback_data="admin_logs"),
            ],
            [
                InlineKeyboardButton("🌐 لوحة الويب", callback_data="admin_web_panel"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)


keyboards = Keyboards()
