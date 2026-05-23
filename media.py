"""
Media Handler - Handles photos, documents, audio/voice messages
"""
import io
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from database.mongodb import db
from services.ai_service import ai_service
from services.image_service import image_service
from services.voice_service import voice_service
from utils.keyboards import keyboards
from utils.messages import Messages
from middleware.security import security
from config.settings import config


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages based on current mode"""
    user = update.effective_user
    
    # Security check
    allowed, reason = await security.check_user(user.id)
    if not allowed:
        return
    
    # Get user data
    db_user = await db.get_user(user.id)
    lang = db_user.get("language_preference", "ar") if db_user else "ar"
    
    # Get current mode
    mode = context.user_data.get("mode", "analyze")
    
    try:
        # Download the photo
        photo = update.message.photo[-1]  # Get highest resolution
        
        # Check file size
        if photo.file_size and photo.file_size > config.MAX_IMAGE_SIZE_MB * 1024 * 1024:
            size_msg = f"❌ الصورة كبيرة جداً. الحد الأقصى {config.MAX_IMAGE_SIZE_MB}MB" if lang == "ar" else f"❌ Image too large. Maximum size is {config.MAX_IMAGE_SIZE_MB}MB"
            await update.message.reply_text(size_msg)
            return
        
        await update.message.chat.send_action("upload_photo")
        
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        photo_bytes = bytes(photo_bytes)
        
        caption = update.message.caption or ""
        
        # Route based on mode
        if mode == "bg_remove":
            await process_bg_removal(update, context, photo_bytes, lang)
        
        elif mode == "enhance":
            await process_enhancement(update, context, photo_bytes, lang)
        
        elif mode == "tryon":
            await process_tryon(update, context, photo_bytes, lang)
        
        elif mode == "analyze":
            question = caption if caption else None
            await process_image_analysis(update, context, photo_bytes, lang, question)
        
        else:
            # Default: analyze with any caption as question, or just describe
            if caption:
                # Chat about the image with the caption as the question
                await process_image_chat(update, context, photo_bytes, caption, lang)
            else:
                await process_image_analysis(update, context, photo_bytes, lang)
    
    except Exception as e:
        logger.error(f"Photo handler error: {e}")
        await update.message.reply_text(Messages.get("ERROR_GENERIC", lang))


async def process_bg_removal(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               photo_bytes: bytes, lang: str):
    """Process background removal"""
    user = update.effective_user
    
    progress_msg = await update.message.reply_text(Messages.get("REMOVING_BG", lang))
    
    try:
        await update.message.chat.send_action("upload_photo")
        result = await image_service.remove_background(photo_bytes)
        
        if result:
            await update.message.reply_photo(
                photo=result,
                caption="✅ " + ("تم إزالة الخلفية بنجاح!" if lang == "ar" else "Background removed successfully!"),
                reply_markup=keyboards.back_to_menu(lang)
            )
            await db.track_usage(user.id, "image")
        else:
            await update.message.reply_text(
                "❌ " + ("فشل في إزالة الخلفية. الرجاء المحاولة مرة أخرى." if lang == "ar" else "Background removal failed. Please try again."),
                reply_markup=keyboards.back_to_menu(lang)
            )
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def process_enhancement(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                photo_bytes: bytes, lang: str):
    """Process image enhancement"""
    user = update.effective_user
    
    progress_msg = await update.message.reply_text(Messages.get("ENHANCING_IMAGE", lang))
    
    try:
        await update.message.chat.send_action("upload_photo")
        result = await image_service.enhance_image(photo_bytes)
        
        if result:
            await update.message.reply_photo(
                photo=result,
                caption="✨ " + ("تم تحسين جودة الصورة!" if lang == "ar" else "Image quality enhanced!"),
                reply_markup=keyboards.back_to_menu(lang)
            )
            await db.track_usage(user.id, "image")
        else:
            await update.message.reply_text("❌ فشل في تحسين الصورة.")
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def process_tryon(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          photo_bytes: bytes, lang: str):
    """Process virtual try-on"""
    user = update.effective_user
    tryon_step = context.user_data.get("tryon_step", 1)
    
    if tryon_step == 1:
        # First image: person
        context.user_data["tryon_person"] = photo_bytes
        context.user_data["tryon_step"] = 2
        
        msg = "✅ **تم استلام صورة الشخص!**\n\n👗 الآن أرسل صورة الملابس/القطعة التي تريد إضافتها:" if lang == "ar" else "✅ **Person photo received!**\n\n👗 Now send the clothing/garment photo to try on:"
        
        await update.message.reply_text(
            msg,
            reply_markup=keyboards.cancel_keyboard(lang),
            parse_mode="Markdown"
        )
    
    elif tryon_step == 2:
        # Second image: garment
        person_bytes = context.user_data.get("tryon_person")
        
        if not person_bytes:
            context.user_data["tryon_step"] = 1
            await update.message.reply_text(
                "❌ لم يتم العثور على صورة الشخص. ابدأ من جديد." if lang == "ar" else "❌ Person photo not found. Please start over.",
                reply_markup=keyboards.back_to_menu(lang)
            )
            return
        
        progress_msg = await update.message.reply_text(
            "👗 **جاري تغيير الملابس بالذكاء الاصطناعي...**\n⏳ قد يستغرق هذا دقيقة" if lang == "ar" else "👗 **AI Virtual Try-On in progress...**\n⏳ This may take a minute",
            parse_mode="Markdown"
        )
        
        try:
            await update.message.chat.send_action("upload_photo")
            result, error = await image_service.virtual_try_on(person_bytes, photo_bytes)
            
            if result:
                await update.message.reply_photo(
                    photo=result,
                    caption="👗 " + ("تم تغيير الملابس بنجاح!" if lang == "ar" else "Virtual Try-On complete!"),
                    reply_markup=keyboards.back_to_menu(lang)
                )
                await db.track_usage(user.id, "image")
            else:
                await update.message.reply_text(
                    f"❌ فشل في تغيير الملابس: {error}" if lang == "ar" else f"❌ Try-on failed: {error}",
                    reply_markup=keyboards.back_to_menu(lang)
                )
        finally:
            try:
                await progress_msg.delete()
            except Exception:
                pass
            
            # Reset try-on state
            context.user_data["tryon_step"] = 1
            context.user_data.pop("tryon_person", None)


async def process_image_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   photo_bytes: bytes, lang: str, question: str = None):
    """Process image analysis/description"""
    user = update.effective_user
    
    progress_msg = await update.message.reply_text(Messages.get("ANALYZING_IMAGE", lang))
    
    try:
        await update.message.chat.send_action("typing")
        description = await image_service.analyze_image(photo_bytes, question, lang)
        
        header = "🔍 **تحليل الصورة:**\n\n" if lang == "ar" else "🔍 **Image Analysis:**\n\n"
        
        await update.message.reply_text(
            header + description,
            reply_markup=keyboards.back_to_menu(lang),
            parse_mode="Markdown"
        )
        
        await db.track_usage(user.id, "message")
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def process_image_chat(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               photo_bytes: bytes, caption: str, lang: str):
    """Chat about an image using vision"""
    user = update.effective_user
    
    progress_msg = await update.message.reply_text(Messages.get("PROCESSING", lang))
    
    try:
        import base64
        b64 = base64.b64encode(photo_bytes).decode()
        image_url = f"data:image/jpeg;base64,{b64}"
        
        # Get history for context
        history = await db.get_conversation_history(user.id)
        conversation = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["role"] in ["user", "assistant"]
        ]
        
        response = await ai_service.chat(
            caption,
            conversation_history=conversation,
            language=lang,
            image_url=image_url
        )
        
        await update.message.reply_text(
            response,
            reply_markup=keyboards.back_to_menu(lang),
            parse_mode="Markdown"
        )
        
        await db.save_message(user.id, "user", f"[Image] {caption}")
        await db.save_message(user.id, "assistant", response)
        await db.track_usage(user.id, "message")
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - convert to text"""
    user = update.effective_user
    
    # Security check
    allowed, reason = await security.check_user(user.id)
    if not allowed:
        return
    
    db_user = await db.get_user(user.id)
    lang = db_user.get("language_preference", "ar") if db_user else "ar"
    
    # Check limit
    allowed_msg = await db.check_rate_limit(user.id, "message")
    if not allowed_msg:
        await update.message.reply_text(
            Messages.get("RATE_LIMITED", lang,
                free_messages=config.FREE_DAILY_MESSAGES,
                free_images=config.FREE_DAILY_IMAGES,
                premium_messages=config.PREMIUM_DAILY_MESSAGES,
                premium_images=config.PREMIUM_DAILY_IMAGES,
            ),
            reply_markup=keyboards.premium_plans(lang)
        )
        return
    
    progress_msg = await update.message.reply_text(Messages.get("TRANSCRIBING", lang))
    
    try:
        await update.message.chat.send_action("typing")
        
        voice = update.message.voice or update.message.audio
        
        if not voice:
            await update.message.reply_text("❌ لم يتم العثور على الصوت." if lang == "ar" else "❌ No audio found.")
            return
        
        # Check size
        if voice.file_size and voice.file_size > config.MAX_AUDIO_SIZE_MB * 1024 * 1024:
            await update.message.reply_text(
                f"❌ الملف صوتي كبير جداً. الحد الأقصى {config.MAX_AUDIO_SIZE_MB}MB" if lang == "ar" else f"❌ Audio file too large. Max {config.MAX_AUDIO_SIZE_MB}MB"
            )
            return
        
        voice_file = await voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        voice_bytes = bytes(voice_bytes)
        
        # Transcribe
        transcribed_text = await voice_service.speech_to_text(voice_bytes, "ogg")
        
        if transcribed_text:
            # Show transcription
            await update.message.reply_text(
                f"🎤 **النص المحوّل:**\n\n{transcribed_text}" if lang == "ar" else f"🎤 **Transcribed Text:**\n\n{transcribed_text}",
                parse_mode="Markdown"
            )
            
            # Also send to AI for response
            await update.message.chat.send_action("typing")
            
            history = await db.get_conversation_history(user.id)
            conversation = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history
                if msg["role"] in ["user", "assistant"]
            ]
            
            ai_response = await ai_service.chat(
                transcribed_text,
                conversation_history=conversation,
                language=lang
            )
            
            await update.message.reply_text(
                ai_response,
                reply_markup=keyboards.back_to_menu(lang),
                parse_mode="Markdown"
            )
            
            # Save to history
            await db.save_message(user.id, "user", transcribed_text)
            await db.save_message(user.id, "assistant", ai_response)
            await db.track_usage(user.id, "message")
        else:
            await update.message.reply_text(
                "❌ فشل في تحويل الصوت. تأكد من وضوح الصوت." if lang == "ar" else "❌ Failed to transcribe. Make sure the audio is clear."
            )
    
    except Exception as e:
        logger.error(f"Voice handler error: {e}")
        await update.message.reply_text(Messages.get("ERROR_GENERIC", lang))
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files - extract and summarize text"""
    user = update.effective_user
    
    allowed, reason = await security.check_user(user.id)
    if not allowed:
        return
    
    db_user = await db.get_user(user.id)
    lang = db_user.get("language_preference", "ar") if db_user else "ar"
    
    doc = update.message.document
    
    # Check file type
    allowed_types = ["text/plain", "application/pdf", "application/msword", 
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    if doc.mime_type not in allowed_types and not doc.file_name.endswith(('.txt', '.pdf', '.doc', '.docx')):
        msg = "⚠️ نوع الملف غير مدعوم. المدعوم: TXT, PDF, DOC, DOCX" if lang == "ar" else "⚠️ File type not supported. Supported: TXT, PDF, DOC, DOCX"
        await update.message.reply_text(msg)
        return
    
    if doc.file_size and doc.file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        msg = f"❌ الملف كبير جداً. الحد الأقصى {config.MAX_FILE_SIZE_MB}MB" if lang == "ar" else f"❌ File too large. Max {config.MAX_FILE_SIZE_MB}MB"
        await update.message.reply_text(msg)
        return
    
    progress_msg = await update.message.reply_text(
        "📄 " + ("جاري قراءة وتلخيص الملف..." if lang == "ar" else "Reading and summarizing file...")
    )
    
    try:
        doc_file = await doc.get_file()
        doc_bytes = await doc_file.download_as_bytearray()
        doc_bytes = bytes(doc_bytes)
        
        # Extract text based on file type
        extracted_text = ""
        
        if doc.file_name.endswith('.txt') or doc.mime_type == "text/plain":
            extracted_text = doc_bytes.decode('utf-8', errors='ignore')
        elif doc.file_name.endswith('.pdf'):
            extracted_text = await extract_pdf_text(doc_bytes)
        else:
            extracted_text = doc_bytes.decode('utf-8', errors='ignore')[:5000]
        
        if not extracted_text:
            await update.message.reply_text(
                "❌ لا يمكن قراءة هذا الملف." if lang == "ar" else "❌ Cannot read this file."
            )
            return
        
        # Summarize
        summary = await ai_service.summarize_text(extracted_text[:8000], lang)
        
        file_info = f"📄 **ملخص ملف '{doc.file_name}':**\n\n" if lang == "ar" else f"📄 **Summary of '{doc.file_name}':**\n\n"
        
        await update.message.reply_text(
            file_info + summary,
            reply_markup=keyboards.back_to_menu(lang),
            parse_mode="Markdown"
        )
        
        await db.track_usage(user.id, "message")
    
    except Exception as e:
        logger.error(f"Document handler error: {e}")
        await update.message.reply_text(Messages.get("ERROR_GENERIC", lang))
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass


async def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        import tempfile
        import subprocess
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name
        
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        finally:
            os.unlink(pdf_path)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""
