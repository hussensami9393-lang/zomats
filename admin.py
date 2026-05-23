"""
Admin Handler - Administrative commands and panel
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from database.mongodb import db
from utils.keyboards import keyboards
from config.settings import config


def admin_required(func):
    """Decorator to require admin access"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user.id not in config.ADMIN_IDS:
            await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


@admin_required
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main admin command handler"""
    stats = await db.get_bot_statistics()
    
    admin_text = f"""🔧 **لوحة تحكم المشرف - NexusAI Bot**

📊 **إحصائيات سريعة:**
• إجمالي المستخدمين: **{stats['total_users']:,}**
• مستخدمو البريميوم: **{stats['premium_users']:,}**
• المستخدمون المجانيون: **{stats['free_users']:,}**
• المحظورون: **{stats['banned_users']:,}**
• نشطون اليوم: **{stats['active_today']:,}**
• جدد اليوم: **{stats['new_today']:,}**

اختر من القائمة أدناه:"""
    
    await update.message.reply_text(
        admin_text,
        reply_markup=keyboards.admin_panel(),
        parse_mode="Markdown"
    )


@admin_required
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message to all users"""
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام: /broadcast [الرسالة]")
        return
    
    message = " ".join(context.args)
    
    # Get all users
    users = await db.get_all_users(limit=10000)
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text(f"📢 جاري الإرسال إلى {len(users)} مستخدم...")
    
    for user_data in users:
        try:
            await context.bot.send_message(
                chat_id=user_data["user_id"],
                text=f"📢 **إعلان من NexusAI:**\n\n{message}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1
        
        # Rate limiting - avoid Telegram flood
        import asyncio
        if (sent + failed) % 30 == 0:
            await asyncio.sleep(1)
    
    await status_msg.edit_text(
        f"✅ **اكتمل الإرسال**\n• تم الإرسال: {sent}\n• فشل: {failed}"
    )


@admin_required
async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ الاستخدام: /ban [user_id] [السبب]")
        return
    
    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "لم يذكر سبب"
        
        await db.ban_user(target_id, reason, update.effective_user.id)
        
        # Notify the banned user
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🚫 تم حظر حسابك.\nالسبب: {reason}"
            )
        except Exception:
            pass
        
        await update.message.reply_text(f"✅ تم حظر المستخدم {target_id}\nالسبب: {reason}")
    
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال ID رقمي صحيح")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")


@admin_required
async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام: /unban [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
        await db.unban_user(target_id, update.effective_user.id)
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="✅ تم رفع الحظر عن حسابك. يمكنك استخدام البوت مرة أخرى."
            )
        except Exception:
            pass
        
        await update.message.reply_text(f"✅ تم رفع الحظر عن المستخدم {target_id}")
    
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال ID رقمي صحيح")


@admin_required
async def grant_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant premium to a user"""
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ الاستخدام: /premium_grant [user_id] [أيام]")
        return
    
    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
        
        await db.upgrade_subscription(target_id, "premium", days)
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"⭐ **مبروك! تم تفعيل حساب البريميوم**\n\nمدة الاشتراك: {days} يوم\n\nاستمتع بجميع الميزات المتقدمة!",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        
        await update.message.reply_text(f"✅ تم منح البريميوم للمستخدم {target_id} لمدة {days} يوم")
    
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال قيم صحيحة")


@admin_required
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List recent users"""
    users = await db.get_all_users(limit=10)
    
    if not users:
        await update.message.reply_text("لا يوجد مستخدمون بعد.")
        return
    
    text = "👥 **آخر المستخدمين:**\n\n"
    
    for u in users:
        sub_icon = "⭐" if u.get("subscription", {}).get("type") != "free" else "🆓"
        ban_icon = "🚫" if u.get("is_banned") else ""
        name = u.get("first_name", "") + " " + (u.get("last_name") or "")
        username = f"@{u['username']}" if u.get("username") else "No username"
        
        text += f"{sub_icon}{ban_icon} **{name.strip() or 'N/A'}** | {username}\n"
        text += f"   ID: `{u['user_id']}`\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")
