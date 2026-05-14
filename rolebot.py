#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from hijridate import Hijri, Gregorian
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 🔐 التوكن من Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

SUPER_ADMIN = [6115157843]

DATA_FILE = "data.json"


# ----------------- حفظ و تحميل البيانات -----------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


chats = load_data()


# ----------------- بيانات المجموعة -----------------

def get_chat_data(chat_id):
    chat_id = str(chat_id)

    if chat_id not in chats:
        chats[chat_id] = {
            "lists": {"معلمة": [], "تسجيل": [], "مستمعة": [], "قرأت": []},
            "registration_open": True,
            "list_title": "",
            "teacher_name": "",
            "last_msg": None,
        }
    return chats[chat_id]


async def is_admin(user_id, chat_id, bot):
    if user_id in SUPER_ADMIN:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ----------------- الأزرار -----------------

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 معلمة", callback_data="join:معلمة"),
            InlineKeyboardButton("📝 تسجيل", callback_data="join:تسجيل"),
        ],
        [
            InlineKeyboardButton("🎧 مستمعة", callback_data="join:مستمعة"),
            InlineKeyboardButton("✅ قرأت", callback_data="mark_read"),
        ],
        [
            InlineKeyboardButton("❌ حذف نفسي", callback_data="remove_me"),
        ],
        [
            InlineKeyboardButton("🔒 غلق", callback_data="admin:close"),
            InlineKeyboardButton("🔓 فتح", callback_data="admin:open"),
        ],
    ])


# ----------------- التاريخ -----------------

def get_dates():
    now = datetime.now()

    days = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
    months_m = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
    months_h = ["محرم","صفر","ربيع الأول","ربيع الآخر","جمادى الأولى","جمادى الآخرة","رجب","شعبان","رمضان","شوال","ذو القعدة","ذو الحجة"]

    day = days[now.weekday()]
    miladi = f"{day} {now.day} {months_m[now.month-1]} {now.year}"

    h = convert.Gregorian(now.year, now.month, now.day).to_hijri()
    hijri = f"{h.day} {months_h[h.month-1]} {h.year}"

    return miladi, hijri


# ----------------- عرض القائمة -----------------

def format_lists(chat_id):
    d = get_chat_data(chat_id)
    lists = d["lists"]

    miladi, hijri = get_dates()

    status = "🟢 مفتوحة" if d["registration_open"] else "🔴 مغلقة"

    title = d["list_title"]
    teacher = d["teacher_name"]

    readers = lists["تسجيل"]

    read_ids = [m.rsplit('[',1)[1].rstrip(']') for m in lists["قرأت"]]

    readers_text = "\n".join(
        f"{i+1}. {m.rsplit('[',1)[0]} {'✅' if m.rsplit('[',1)[1].rstrip(']') in read_ids else ''}"
        for i, m in enumerate(readers)
    ) if readers else "—"

    listeners = lists["مستمعة"]

    listeners_text = "\n".join(
        f"{i+1}. {m.rsplit('[',1)[0]}"
        for i, m in enumerate(listeners)
    ) if listeners else "—"

    return f"""
📅 {miladi}
{hijri}

📌 عنوان الحلقة: {title}
👩‍🏫 المعلمة: {teacher}

☜ المسجلات:
{readers_text}

🎧 المستمعات:
{listeners_text}

📌 الحالة: {status}
"""


# ----------------- START -----------------

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("هذا البوت يعمل داخل المجموعة فقط")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("للمشرفين فقط")
        return

    d = get_chat_data(chat_id)

    msg = await ctx.bot.send_message(
        chat_id,
        format_lists(chat_id),
        reply_markup=main_keyboard()
    )

    d["last_msg"] = msg.message_id
    save_data(chats)


# ----------------- RESET (قائمة جديدة) -----------------

async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)

    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 للمشرف فقط")
        return

    chats[chat_id]["lists"] = {
        "معلمة": [],
        "تسجيل": [],
        "مستمعة": [],
        "قرأت": []
    }

    chats[chat_id]["list_title"] = ""
    chats[chat_id]["teacher_name"] = ""

    save_data(chats)

    await update.message.reply_text("🧹 تم إنشاء قائمة جديدة")


# ----------------- الأزرار -----------------

async def handle_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    name = user.full_name
    chat_id = str(query.message.chat.id)

    d = get_chat_data(chat_id)
    lists = d["lists"]

    if query.data.startswith("join:"):
        role = query.data.split(":")[1]

        for k in lists:
            if k != "قرأت":
                lists[k] = [m for m in lists[k] if not m.endswith(f"[{user_id}]")]

        lists[role].append(f"{name} [{user_id}]")

    elif query.data == "remove_me":
        for k in lists:
            lists[k] = [m for m in lists[k] if not m.endswith(f"[{user_id}]")]

    elif query.data == "mark_read":
        if not any(m.endswith(f"[{user_id}]") for m in lists["تسجيل"]):
            await query.answer("سجلي نفسك أولاً", show_alert=True)
            return

        if not any(m.endswith(f"[{user_id}]") for m in lists["قرأت"]):
            lists["قرأت"].append(f"{name} [{user_id}]")

    elif query.data == "admin:close":
        if not await is_admin(user_id, chat_id, ctx.bot):
            return
        d["registration_open"] = False

    elif query.data == "admin:open":
        if not await is_admin(user_id, chat_id, ctx.bot):
            return
        d["registration_open"] = True

    save_data(chats)

    await query.edit_message_text(
        format_lists(chat_id),
        reply_markup=main_keyboard()
    )


# ----------------- تشغيل -----------------

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("🤖 البوت شغال")

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
