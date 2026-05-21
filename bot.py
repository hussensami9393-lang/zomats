import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8657954193:AAFTn9HiGdHhFc2yw81eNUi9xeJjW5Ecg4s").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "8013589941").split(",")
    if x.strip().isdigit()
}
DB_PATH = Path(os.getenv("DB_PATH", "data/shop.db"))
PAYMENT_INSTRUCTIONS = os.getenv(
    "PAYMENT_INSTRUCTIONS",
    "حوّل رصيد آسياسيل إلى الرقم: 07746782630 ثم أرسل رقم الهاتف أو إثبات التحويل هنا.",
)
SHOP_NAME = os.getenv("SHOP_NAME", "متجر السلع")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ADD_NAME, ADD_DESC, ADD_PRICE, ADD_STOCK = range(4)
ORDER_PAYMENT = 10


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def db_connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(db_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                product_price TEXT NOT NULL,
                buyer_id INTEGER NOT NULL,
                buyer_username TEXT,
                buyer_name TEXT,
                payment_note TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )
        conn.commit()


def add_product(name: str, description: str, price: str, stock: int) -> int:
    now = datetime.utcnow().isoformat()
    with closing(db_connect()) as conn:
        cur = conn.execute(
            "INSERT INTO products(name, description, price, stock, active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (name, description, price, stock, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_active_products() -> list[sqlite3.Row]:
    with closing(db_connect()) as conn:
        return conn.execute(
            "SELECT * FROM products WHERE active = 1 AND stock > 0 ORDER BY id DESC"
        ).fetchall()


def get_all_products() -> list[sqlite3.Row]:
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()


def get_product(product_id: int) -> Optional[sqlite3.Row]:
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def set_product_active(product_id: int, active: int) -> None:
    with closing(db_connect()) as conn:
        conn.execute("UPDATE products SET active = ? WHERE id = ?", (active, product_id))
        conn.commit()


def delete_product(product_id: int) -> None:
    with closing(db_connect()) as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def create_order(product: sqlite3.Row, user, payment_note: str) -> int:
    now = datetime.utcnow().isoformat()
    buyer_name = " ".join(filter(None, [user.first_name, user.last_name])) or str(user.id)
    with closing(db_connect()) as conn:
        cur = conn.execute(
            """
            INSERT INTO orders(
                product_id, product_name, product_price, buyer_id, buyer_username,
                buyer_name, payment_note, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                product["id"],
                product["name"],
                product["price"],
                user.id,
                user.username,
                buyer_name,
                payment_note,
                now,
                now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_pending_orders() -> list[sqlite3.Row]:
    with closing(db_connect()) as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY id DESC"
        ).fetchall()


def get_order(order_id: int) -> Optional[sqlite3.Row]:
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def update_order_status(order_id: int, status: str) -> None:
    now = datetime.utcnow().isoformat()
    with closing(db_connect()) as conn:
        conn.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
        if status == "approved":
            order = conn.execute("SELECT product_id FROM orders WHERE id = ?", (order_id,)).fetchone()
            if order:
                conn.execute(
                    "UPDATE products SET stock = MAX(stock - 1, 0) WHERE id = ?",
                    (order["product_id"],),
                )
        conn.commit()


def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton("🛍 عرض السلع", callback_data="catalog")]]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("⚙️ لوحة المدير", callback_data="admin")])
    return InlineKeyboardMarkup(buttons)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ إضافة سلعة", callback_data="admin_add")],
            [InlineKeyboardButton("📦 إدارة السلع", callback_data="admin_products")],
            [InlineKeyboardButton("🧾 الطلبات المعلقة", callback_data="admin_orders")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = (
        f"أهلًا بك في <b>{SHOP_NAME}</b> 👋\n\n"
        "يمكنك تصفح السلع وطلب الشراء. الدفع يتم يدويًا عبر رصيد آسياسيل، "
        "ثم يراجع المدير الطلب ويقبله أو يرفضه."
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(user_id),
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("هذه الصفحة للمدير فقط.")
        return
    await update.message.reply_text("لوحة المدير:", reply_markup=admin_keyboard())


async def show_catalog(query_or_update, context: ContextTypes.DEFAULT_TYPE) -> None:
    products = get_active_products()
    if not products:
        text = "لا توجد سلع متاحة حاليًا."
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]])
    else:
        text = "اختر السلعة التي تريد شراءها:"
        buttons = []
        for p in products:
            buttons.append([
                InlineKeyboardButton(
                    f"{p['name']} — {p['price']}",
                    callback_data=f"product_{p['id']}",
                )
            ])
        buttons.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
        markup = InlineKeyboardMarkup(buttons)

    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(text, reply_markup=markup)
    else:
        await query_or_update.message.reply_text(text, reply_markup=markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "home":
        await query.edit_message_text(
            f"أهلًا بك في <b>{SHOP_NAME}</b> 👋",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(user_id),
        )
        return ConversationHandler.END

    if data == "catalog":
        await show_catalog(query, context)
        return ConversationHandler.END

    if data.startswith("product_"):
        product_id = int(data.split("_", 1)[1])
        product = get_product(product_id)
        if not product or not product["active"] or product["stock"] <= 0:
            await query.edit_message_text("هذه السلعة غير متاحة حاليًا.")
            return ConversationHandler.END
        text = (
            f"<b>{product['name']}</b>\n\n"
            f"{product['description']}\n\n"
            f"السعر: <b>{product['price']}</b>\n"
            f"الكمية المتاحة: <b>{product['stock']}</b>"
        )
        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ شراء", callback_data=f"buy_{product_id}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data="catalog")],
            ]
        )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    if data.startswith("buy_"):
        product_id = int(data.split("_", 1)[1])
        product = get_product(product_id)
        if not product or not product["active"] or product["stock"] <= 0:
            await query.edit_message_text("هذه السلعة غير متاحة حاليًا.")
            return ConversationHandler.END
        context.user_data["buy_product_id"] = product_id
        await query.edit_message_text(
            f"لشراء: <b>{product['name']}</b>\n"
            f"السعر: <b>{product['price']}</b>\n\n"
            f"تعليمات الدفع:\n{PAYMENT_INSTRUCTIONS}\n\n"
            "بعد التحويل، أرسل هنا رقم الهاتف أو إثبات التحويل أو ملاحظة الدفع.",
            parse_mode=ParseMode.HTML,
        )
        return ORDER_PAYMENT

    if data == "admin":
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        await query.edit_message_text("لوحة المدير:", reply_markup=admin_keyboard())
        return ConversationHandler.END

    if data == "admin_add":
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        context.user_data["new_product"] = {}
        await query.edit_message_text("أرسل اسم السلعة:")
        return ADD_NAME

    if data == "admin_products":
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        await show_admin_products(query)
        return ConversationHandler.END

    if data == "admin_orders":
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        await show_pending_orders(query)
        return ConversationHandler.END

    if data.startswith("toggle_"):
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        product_id = int(data.split("_", 1)[1])
        product = get_product(product_id)
        if product:
            set_product_active(product_id, 0 if product["active"] else 1)
        await show_admin_products(query)
        return ConversationHandler.END

    if data.startswith("delete_"):
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        product_id = int(data.split("_", 1)[1])
        delete_product(product_id)
        await show_admin_products(query)
        return ConversationHandler.END

    if data.startswith("approve_") or data.startswith("reject_"):
        if not is_admin(user_id):
            await query.edit_message_text("هذه الصفحة للمدير فقط.")
            return ConversationHandler.END
        action, raw_id = data.split("_", 1)
        order_id = int(raw_id)
        order = get_order(order_id)
        if not order or order["status"] != "pending":
            await query.edit_message_text("هذا الطلب غير موجود أو تمت معالجته سابقًا.")
            return ConversationHandler.END
        status = "approved" if action == "approve" else "rejected"
        update_order_status(order_id, status)
        await query.edit_message_text(f"تم {'قبول' if status == 'approved' else 'رفض'} الطلب رقم #{order_id}.")
        try:
            await context.bot.send_message(
                chat_id=order["buyer_id"],
                text=(
                    f"تم {'قبول ✅' if status == 'approved' else 'رفض ❌'} طلبك رقم #{order_id}\n"
                    f"السلعة: {order['product_name']}\n"
                    f"السعر: {order['product_price']}"
                ),
            )
        except Exception as exc:
            logger.warning("Could not notify buyer %s: %s", order["buyer_id"], exc)
        return ConversationHandler.END

    return ConversationHandler.END


async def show_admin_products(query) -> None:
    products = get_all_products()
    if not products:
        await query.edit_message_text("لا توجد سلع بعد.", reply_markup=admin_keyboard())
        return
    buttons = []
    lines = ["📦 إدارة السلع:\n"]
    for p in products:
        status = "مفعلة" if p["active"] else "معطلة"
        lines.append(f"#{p['id']} - {p['name']} - {p['price']} - مخزون: {p['stock']} - {status}")
        buttons.append([
            InlineKeyboardButton(
                f"{'تعطيل' if p['active'] else 'تفعيل'} #{p['id']}",
                callback_data=f"toggle_{p['id']}",
            ),
            InlineKeyboardButton(f"حذف #{p['id']}", callback_data=f"delete_{p['id']}"),
        ])
    buttons.append([InlineKeyboardButton("⬅️ لوحة المدير", callback_data="admin")])
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


async def show_pending_orders(query) -> None:
    orders = get_pending_orders()
    if not orders:
        await query.edit_message_text("لا توجد طلبات معلقة.", reply_markup=admin_keyboard())
        return
    buttons = []
    lines = ["🧾 الطلبات المعلقة:\n"]
    for o in orders:
        username = f"@{o['buyer_username']}" if o["buyer_username"] else "بدون يوزر"
        lines.append(
            f"#{o['id']}\n"
            f"السلعة: {o['product_name']}\n"
            f"السعر: {o['product_price']}\n"
            f"المشتري: {o['buyer_name']} ({username})\n"
            f"ملاحظة الدفع: {o['payment_note']}\n"
        )
        buttons.append([
            InlineKeyboardButton(f"قبول #{o['id']}", callback_data=f"approve_{o['id']}"),
            InlineKeyboardButton(f"رفض #{o['id']}", callback_data=f"reject_{o['id']}"),
        ])
    buttons.append([InlineKeyboardButton("⬅️ لوحة المدير", callback_data="admin")])
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.setdefault("new_product", {})["name"] = update.message.text.strip()
    await update.message.reply_text("أرسل وصف السلعة:")
    return ADD_DESC


async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["new_product"]["description"] = update.message.text.strip()
    await update.message.reply_text("أرسل سعر السلعة، مثال: 5000 دينار أو 5$ أو 10000 رصيد آسياسيل:")
    return ADD_PRICE


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["new_product"]["price"] = update.message.text.strip()
    await update.message.reply_text("أرسل كمية المخزون كرقم، مثال: 10")
    return ADD_STOCK


async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    try:
        stock = int(update.message.text.strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("أرسل رقمًا صحيحًا للكمية، مثال: 10")
        return ADD_STOCK

    product = context.user_data.get("new_product", {})
    product_id = add_product(
        product["name"],
        product["description"],
        product["price"],
        stock,
    )
    context.user_data.pop("new_product", None)
    await update.message.reply_text(f"تمت إضافة السلعة بنجاح ✅\nرقم السلعة: #{product_id}", reply_markup=admin_keyboard())
    return ConversationHandler.END


async def receive_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = context.user_data.get("buy_product_id")
    if not product_id:
        await update.message.reply_text("انتهت جلسة الشراء. اختر السلعة مرة أخرى.")
        return ConversationHandler.END
    product = get_product(int(product_id))
    if not product or not product["active"] or product["stock"] <= 0:
        await update.message.reply_text("هذه السلعة غير متاحة حاليًا.")
        return ConversationHandler.END

    payment_note = update.message.text.strip()
    order_id = create_order(product, update.effective_user, payment_note)
    context.user_data.pop("buy_product_id", None)

    await update.message.reply_text(
        f"تم استلام طلبك رقم #{order_id} ✅\n"
        "سيقوم المدير بمراجعة الدفع والرد عليك قريبًا."
    )

    admin_text = (
        f"طلب جديد #{order_id}\n\n"
        f"السلعة: {product['name']}\n"
        f"السعر: {product['price']}\n"
        f"المشتري: {update.effective_user.full_name}\n"
        f"يوزر: @{update.effective_user.username if update.effective_user.username else 'لا يوجد'}\n"
        f"ID: {update.effective_user.id}\n"
        f"ملاحظة الدفع: {payment_note}"
    )
    markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("قبول ✅", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("رفض ❌", callback_data=f"reject_{order_id}"),
        ]]
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup)
        except Exception as exc:
            logger.warning("Could not notify admin %s: %s", admin_id, exc)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=main_menu_keyboard(update.effective_user.id))
    return ConversationHandler.END


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("ضع BOT_TOKEN في ملف .env")
    if not ADMIN_IDS:
        raise RuntimeError("ضع ADMIN_IDS في ملف .env، مثال: ADMIN_IDS=123456789")

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stock)],
            ORDER_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv)

    logger.info("%s started", SHOP_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
