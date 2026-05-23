"""
Message Templates - All bot messages in Arabic and English
"""

class Messages:
    """All bot message templates"""
    
    WELCOME = {
        "ar": """🌟 **أهلاً وسهلاً في NexusAI Bot!**

مرحباً {name}! أنا مساعدك الذكي المتطور 🤖

**قدراتي تشمل:**
🎨 إنشاء صور مذهلة من النص
👗 تغيير الملابس بالذكاء الاصطناعي  
✂️ إزالة الخلفية من الصور
💻 كتابة وشرح وتصحيح الأكواد
🌍 ترجمة أي نص لأي لغة
📝 تلخيص النصوص والملفات
📱 إنشاء محتوى السوشيال ميديا
💡 توليد أفكار المشاريع
🎤 تحويل الصوت إلى نص والعكس
🤖 محادثة ذكية بمستوى GPT-4

**حساب مجاني:** {free_messages} رسالة يومياً، {free_images} صورة يومياً

اضغط على الزر أدناه للبدء! 👇""",
        
        "en": """🌟 **Welcome to NexusAI Bot!**

Hello {name}! I'm your advanced AI assistant 🤖

**My capabilities include:**
🎨 Generate stunning images from text
👗 AI Virtual Try-On for clothes
✂️ Remove image backgrounds
💻 Write, explain & debug code
🌍 Translate any text to any language
📝 Summarize texts and files
📱 Create social media content
💡 Generate project ideas
🎤 Speech-to-text and text-to-speech
🤖 Smart chat at GPT-4 level

**Free account:** {free_messages} daily messages, {free_images} daily images

Press the button below to start! 👇"""
    }
    
    RATE_LIMITED = {
        "ar": "⚠️ **لقد تجاوزت الحد اليومي المجاني**\n\n"
               "**الحد المجاني:**\n"
               "• {free_messages} رسالة يومياً\n"
               "• {free_images} صورة يومياً\n\n"
               "🌟 **قم بالترقية للبريميوم للحصول على:**\n"
               "• {premium_messages} رسالة يومياً\n"
               "• {premium_images} صورة يومياً\n"
               "• أولوية المعالجة\n"
               "• جميع نماذج AI المتقدمة",
        
        "en": "⚠️ **You've exceeded your daily free limit**\n\n"
               "**Free limits:**\n"
               "• {free_messages} messages per day\n"
               "• {free_images} images per day\n\n"
               "🌟 **Upgrade to Premium to get:**\n"
               "• {premium_messages} messages per day\n"
               "• {premium_images} images per day\n"
               "• Priority processing\n"
               "• All advanced AI models"
    }
    
    BANNED = {
        "ar": "🚫 **تم حظر حسابك**\n\nإذا كنت تعتقد أن هذا خطأ، تواصل معنا عبر @support",
        "en": "🚫 **Your account has been banned**\n\nIf you think this is a mistake, contact us via @support"
    }
    
    SPAM_WARNING = {
        "ar": "⚠️ **إنذار:** إرسالك رسائل بشكل متكرر جداً!\nالرجاء التباطؤ أو سيتم حظرك.",
        "en": "⚠️ **Warning:** You're sending messages too fast!\nPlease slow down or you'll be blocked."
    }
    
    PROCESSING = {
        "ar": "⏳ جاري المعالجة...",
        "en": "⏳ Processing..."
    }
    
    GENERATING_IMAGE = {
        "ar": "🎨 جاري إنشاء الصورة... قد يستغرق ذلك لحظة",
        "en": "🎨 Generating image... This may take a moment"
    }
    
    REMOVING_BG = {
        "ar": "✂️ جاري إزالة الخلفية...",
        "en": "✂️ Removing background..."
    }
    
    ENHANCING_IMAGE = {
        "ar": "✨ جاري تحسين جودة الصورة...",
        "en": "✨ Enhancing image quality..."
    }
    
    ANALYZING_IMAGE = {
        "ar": "🔍 جاري تحليل الصورة...",
        "en": "🔍 Analyzing image..."
    }
    
    TRANSCRIBING = {
        "ar": "🎤 جاري تحويل الصوت إلى نص...",
        "en": "🎤 Transcribing audio..."
    }
    
    CONVERTING_TTS = {
        "ar": "🔊 جاري تحويل النص إلى صوت...",
        "en": "🔊 Converting text to speech..."
    }
    
    MODE_CHAT = {
        "ar": "🤖 **وضع المحادثة الذكية**\n\nأنا هنا! اكتب سؤالك أو اطلب أي شيء.\nيمكنك أيضاً إرسال صور للتحليل.",
        "en": "🤖 **Smart Chat Mode**\n\nI'm here! Type your question or request anything.\nYou can also send images for analysis."
    }
    
    MODE_IMAGE_GEN = {
        "ar": "🎨 **وضع إنشاء الصور**\n\nصف الصورة التي تريد إنشاءها بالتفصيل.\n\n**مثال:** رجل يمشي في مدينة مستقبلية، أضواء نيون، جودة عالية، واقعي",
        "en": "🎨 **Image Generation Mode**\n\nDescribe the image you want to create in detail.\n\n**Example:** A man walking in a futuristic city, neon lights, high quality, photorealistic"
    }
    
    MODE_BG_REMOVE = {
        "ar": "✂️ **وضع إزالة الخلفية**\n\nأرسل الصورة وسأقوم بإزالة الخلفية منها تلقائياً! 📸",
        "en": "✂️ **Background Removal Mode**\n\nSend me any image and I'll automatically remove its background! 📸"
    }
    
    MODE_ENHANCE = {
        "ar": "✨ **وضع تحسين الصورة**\n\nأرسل صورتك وسأقوم بتحسين جودتها وحدتها! 🖼️",
        "en": "✨ **Image Enhancement Mode**\n\nSend your image and I'll improve its quality and sharpness! 🖼️"
    }
    
    MODE_ANALYZE = {
        "ar": "🔍 **وضع تحليل الصورة**\n\nأرسل أي صورة وسأخبرك بكل ما فيها بالتفصيل!",
        "en": "🔍 **Image Analysis Mode**\n\nSend any image and I'll tell you everything about it in detail!"
    }
    
    MODE_TRYON = {
        "ar": "👗 **وضع تغيير الملابس AI**\n\n**الخطوات:**\n1️⃣ أرسل صورة الشخص أولاً\n2️⃣ ثم أرسل صورة القطعة التي تريد إضافتها\n\n⚠️ يتطلب هذا مفتاح Replicate API",
        "en": "👗 **AI Virtual Try-On Mode**\n\n**Steps:**\n1️⃣ Send the person's photo first\n2️⃣ Then send the garment/clothing photo\n\n⚠️ Requires Replicate API key"
    }
    
    MODE_CODE = {
        "ar": "💻 **وضع مساعد البرمجة**\n\nاختر ما تريد:",
        "en": "💻 **Code Assistant Mode**\n\nChoose what you need:"
    }
    
    MODE_TRANSLATE = {
        "ar": "🌍 **وضع الترجمة**\n\nاختر اللغة التي تريد الترجمة إليها:",
        "en": "🌍 **Translation Mode**\n\nChoose the language to translate to:"
    }
    
    MODE_SUMMARIZE = {
        "ar": "📝 **وضع التلخيص**\n\nأرسل النص أو الملف الذي تريد تلخيصه. يمكنني تلخيص نصوص طويلة جداً!",
        "en": "📝 **Summarization Mode**\n\nSend the text or file you want to summarize. I can handle very long texts!"
    }
    
    MODE_SOCIAL = {
        "ar": "📱 **وضع محتوى السوشيال ميديا**\n\nاختر المنصة:",
        "en": "📱 **Social Media Content Mode**\n\nChoose the platform:"
    }
    
    MODE_PROJECTS = {
        "ar": "💡 **وضع توليد أفكار المشاريع**\n\nصف المجال أو الفكرة التي تريد مشروعاً عنها وسأولد لك فكرة متكاملة!",
        "en": "💡 **Project Ideas Generator Mode**\n\nDescribe the field or idea you want a project about and I'll generate a complete project idea!"
    }
    
    MODE_VOICE = {
        "ar": "🎤 **وضع تحويل الصوت**\n\n• أرسل رسالة صوتية: سأحولها إلى نص\n• اكتب /tts [النص]: سأحوله إلى صوت",
        "en": "🎤 **Voice Conversion Mode**\n\n• Send a voice message: I'll convert it to text\n• Type /tts [text]: I'll convert it to audio"
    }
    
    PREMIUM_INFO = {
        "ar": """⭐ **بريميوم NexusAI**

**الخطة المجانية:**
• {free_messages} رسالة / يوم
• {free_images} صورة / يوم
• الوصول للميزات الأساسية
• نموذج GPT-3.5

**خطة البريميوم ⭐:**
• {premium_messages} رسالة / يوم
• {premium_images} صورة / يوم
• جميع ميزات AI
• GPT-4o + Claude 3.5 + Stability AI
• أولوية المعالجة
• دعم الملفات الكبيرة
• ذاكرة محادثة طويلة
• دعم فوري

اختر خطتك:""",
        
        "en": """⭐ **NexusAI Premium**

**Free Plan:**
• {free_messages} messages / day
• {free_images} images / day
• Access to basic features
• GPT-3.5 model

**Premium Plan ⭐:**
• {premium_messages} messages / day
• {premium_images} images / day
• All AI features
• GPT-4o + Claude 3.5 + Stability AI
• Priority processing
• Large file support
• Extended conversation memory
• Instant support

Choose your plan:"""
    }
    
    SETTINGS_MENU = {
        "ar": "⚙️ **الإعدادات**\n\nاختر ما تريد تغييره:",
        "en": "⚙️ **Settings**\n\nChoose what you want to change:"
    }
    
    HISTORY_CLEARED = {
        "ar": "🗑️ **تم مسح سجل المحادثة**\n\nيمكنك البدء من جديد!",
        "en": "🗑️ **Conversation history cleared**\n\nYou can start fresh!"
    }
    
    ERROR_GENERIC = {
        "ar": "❌ حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.",
        "en": "❌ An unexpected error occurred. Please try again."
    }
    
    ERROR_NO_API = {
        "ar": "⚠️ هذه الميزة تتطلب ضبط مفتاح API. الرجاء التواصل مع الدعم.",
        "en": "⚠️ This feature requires an API key to be configured. Please contact support."
    }
    
    ADMIN_ONLY = {
        "ar": "⛔ هذا الأمر للمشرفين فقط.",
        "en": "⛔ This command is for admins only."
    }

    @classmethod
    def get(cls, key: str, language: str = "ar", **kwargs) -> str:
        """Get a message by key with optional formatting"""
        msg_dict = getattr(cls, key, None)
        if not msg_dict:
            return f"[Missing message: {key}]"
        
        msg = msg_dict.get(language, msg_dict.get("ar", ""))
        
        if kwargs:
            try:
                msg = msg.format(**kwargs)
            except KeyError:
                pass
        
        return msg


messages = Messages()
