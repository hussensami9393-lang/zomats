"""
AI Chat Service - Powers the main conversational AI
Supports GPT-4o, Claude 3.5, and fallback models
"""
import openai
import httpx
from typing import List, Dict, Optional, AsyncGenerator
from loguru import logger
from config.settings import config


class AIService:
    """
    Multi-model AI service supporting OpenAI GPT-4o and Claude
    with streaming, vision, and code capabilities
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        
    def _get_system_prompt(self, language: str = "ar") -> str:
        """Get system prompt based on user language"""
        if language == "ar":
            return """أنت NexusAI، مساعد ذكاء اصطناعي متطور ومتعدد المهام.
            
قدراتك:
- الإجابة على أي سؤال بدقة عالية
- كتابة وشرح وتصحيح الأكواد البرمجية بجميع اللغات
- تحليل الصور والملفات
- كتابة المحتوى الإبداعي والتسويقي
- الترجمة بين جميع اللغات
- تلخيص النصوص والمستندات
- إنشاء أفكار المشاريع والواجهات

أسلوبك:
- احترافي وودود في نفس الوقت
- تجيب باللغة التي يكتب بها المستخدم
- تستخدم الرموز التعبيرية بشكل مناسب
- تقدم إجابات منظمة ومفيدة
- صادق وتقول عندما لا تعرف شيئاً"""
        else:
            return """You are NexusAI, an advanced multi-purpose AI assistant.

Capabilities:
- Answer any question with high accuracy
- Write, explain, and debug code in all programming languages
- Analyze images and files
- Create creative and marketing content
- Translate between all languages
- Summarize texts and documents
- Generate project ideas and UI concepts

Style:
- Professional yet friendly
- Respond in the user's language
- Use emojis appropriately
- Provide organized, helpful responses
- Honest about limitations"""
    
    async def chat(
        self, 
        user_message: str,
        conversation_history: List[Dict] = None,
        language: str = "ar",
        image_url: str = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> str:
        """
        Send a message to the AI and get a response
        Supports text, images (vision), and conversation history
        """
        if not self.openai_client:
            return "⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to your environment."
        
        max_tokens = max_tokens or config.FREE_MAX_TOKENS
        
        # Build messages array
        messages = [{"role": "system", "content": self._get_system_prompt(language)}]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-config.MAX_CONTEXT_MESSAGES:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Build current message content
        if image_url:
            # Vision message
            message_content = [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url, "detail": "high"}
                }
            ]
            messages.append({"role": "user", "content": message_content})
        else:
            messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=config.OPENAI_VISION_MODEL if image_url else config.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except openai.RateLimitError:
            logger.warning("OpenAI Rate limit hit, trying fallback...")
            return await self._fallback_response(user_message, language)
        except openai.AuthenticationError:
            return "❌ خطأ في مفتاح API. يرجى التحقق من الإعدادات."
        except Exception as e:
            logger.error(f"AI Chat error: {e}")
            return await self._fallback_response(user_message, language)
    
    async def _fallback_response(self, message: str, language: str) -> str:
        """Fallback response when primary API fails"""
        try:
            # Try Anthropic as fallback if available
            if config.ANTHROPIC_API_KEY:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
                response = await client.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    max_tokens=1024,
                    system=self._get_system_prompt(language),
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text
        except Exception as e:
            logger.error(f"Fallback AI error: {e}")
        
        if language == "ar":
            return "⚠️ عذراً، خدمة الذكاء الاصطناعي غير متاحة مؤقتاً. يرجى المحاولة مرة أخرى."
        return "⚠️ Sorry, AI service is temporarily unavailable. Please try again."
    
    async def analyze_code(self, code: str, language_pref: str = "ar") -> str:
        """Analyze and explain code"""
        prompt = f"""قم بتحليل هذا الكود وشرحه بالتفصيل:
        
```
{code}
```

المطلوب:
1. شرح ما يفعله الكود
2. تحديد اللغة البرمجية
3. نقاط القوة والضعف
4. اقتراحات للتحسين
5. تصحيح أي أخطاء إن وجدت""" if language_pref == "ar" else f"""Analyze this code in detail:

```
{code}
```

Please provide:
1. What the code does
2. Programming language identification
3. Strengths and weaknesses
4. Improvement suggestions
5. Bug fixes if any"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=2000)
    
    async def generate_code(self, description: str, programming_language: str, language_pref: str = "ar") -> str:
        """Generate code from description"""
        prompt = f"""اكتب كود {programming_language} للمهمة التالية:

{description}

المتطلبات:
- كود نظيف ومنظم
- تعليقات توضيحية
- معالجة الأخطاء
- أفضل الممارسات
- مثال على الاستخدام""" if language_pref == "ar" else f"""Write {programming_language} code for the following task:

{description}

Requirements:
- Clean and organized code
- Explanatory comments
- Error handling
- Best practices
- Usage example"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=3000)
    
    async def translate_text(self, text: str, target_language: str, source_language: str = "auto") -> str:
        """Translate text to target language"""
        lang_names = {
            "ar": "العربية", "en": "English", "fr": "Français",
            "es": "Español", "de": "Deutsch", "it": "Italiano",
            "pt": "Português", "ru": "Русский", "zh": "中文",
            "ja": "日本語", "ko": "한국어", "tr": "Türkçe"
        }
        
        target_name = lang_names.get(target_language, target_language)
        
        prompt = f"""Translate the following text to {target_name}. 
Provide ONLY the translation, nothing else:

{text}"""
        
        return await self.chat(prompt, language="en", max_tokens=2000)
    
    async def summarize_text(self, text: str, language_pref: str = "ar") -> str:
        """Summarize long text"""
        prompt = f"""لخص النص التالي بشكل واضح ومنظم:

{text[:4000]}

المطلوب:
- ملخص شامل في نقاط
- الأفكار الرئيسية
- أهم المعلومات""" if language_pref == "ar" else f"""Summarize the following text clearly:

{text[:4000]}

Please provide:
- Comprehensive bullet-point summary
- Main ideas
- Key information"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=1500)
    
    async def create_social_content(self, topic: str, platform: str, language_pref: str = "ar") -> str:
        """Create social media content"""
        platform_guides = {
            "instagram": "مميز بصرياً، هاشتاقات، كابشن جذاب",
            "twitter": "مختصر وقوي، أقل من 280 حرف، هاشتاقات",
            "linkedin": "احترافي، مفيد، للبيزنس",
            "tiktok": "ترفيهي، خطافي، ترند",
            "youtube": "عنوان جذاب، وصف SEO، نقاط الفيديو",
        }
        
        guide = platform_guides.get(platform.lower(), "عام")
        
        prompt = f"""أنشئ محتوى {platform} احترافي عن: {topic}

أسلوب {platform}: {guide}

المطلوب:
1. عنوان/هوك جذاب
2. النص الرئيسي
3. دعوة للتفاعل (CTA)
4. هاشتاقات مناسبة
5. وقت النشر المثالي""" if language_pref == "ar" else f"""Create professional {platform} content about: {topic}

{platform} style: {guide}

Please provide:
1. Catchy title/hook
2. Main content
3. Call to action (CTA)
4. Relevant hashtags
5. Best posting time"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=1500)
    
    async def generate_project_idea(self, description: str, language_pref: str = "ar") -> str:
        """Generate project and UI ideas"""
        prompt = f"""أنشئ فكرة مشروع متكاملة بناءً على:

{description}

المطلوب:
1. 🎯 وصف المشروع والمشكلة التي يحلها
2. 🛠️ التقنيات المقترحة (Frontend/Backend/DB)
3. 🗂️ هيكل قاعدة البيانات
4. 📱 اقتراحات تصميم الواجهة
5. 🚀 خطة التطوير (Roadmap)
6. 💰 نموذج الربح (إن أمكن)
7. 📊 الميزات الرئيسية (MVP)
8. 🔧 الميزات المستقبلية""" if language_pref == "ar" else f"""Generate a complete project idea based on:

{description}

Please provide:
1. 🎯 Project description and problem it solves
2. 🛠️ Suggested technologies (Frontend/Backend/DB)
3. 🗂️ Database structure
4. 📱 UI/UX design suggestions
5. 🚀 Development roadmap
6. 💰 Revenue model (if applicable)
7. 📊 Core features (MVP)
8. 🔧 Future features"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=3000)
    
    async def debug_code(self, code: str, error_message: str, language_pref: str = "ar") -> str:
        """Debug code and fix errors"""
        prompt = f"""صحح الخطأ في هذا الكود:

**الكود:**
```
{code}
```

**رسالة الخطأ:**
```
{error_message}
```

المطلوب:
1. سبب الخطأ
2. الكود المُصحح
3. شرح التعديلات
4. نصائح لتجنب هذا الخطأ مستقبلاً""" if language_pref == "ar" else f"""Debug and fix this code:

**Code:**
```
{code}
```

**Error:**
```
{error_message}
```

Please provide:
1. Root cause of the error
2. Fixed code
3. Explanation of changes
4. Tips to avoid this error in the future"""
        
        return await self.chat(prompt, language=language_pref, max_tokens=2500)


# Global AI service instance
ai_service = AIService()
