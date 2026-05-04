#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from hijri_converter import convert
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8703353514:AAEcMYN3QzZjU8Qz9N53lGu-Ddx_5SKB3FM"
SUPER_ADMIN = [6115157843]

chats = {}

def get_chat_data(chat_id):
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

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 معلمة", callback_data="join:معلمة"), InlineKeyboardButton("📝 تسجيل اسمي", callback_data="join:تسجيل")],
        [InlineKeyboardButton("🎧 مستمعة", callback_data="join:مستمعة"), InlineKeyboardButton("✅ قرأت", callback_data="mark_read")],
        [InlineKeyboardButton("✏️ عنوان", callback_data="set_title"), InlineKeyboardButton("❌ حذف", callback_data="remove_me")],
        [InlineKeyboardButton("🔒 غلق", callback_data="admin:close"), InlineKeyboardButton("🔓 فتح", callback_data="admin:open")],
    ]
    return InlineKeyboardMarkup(keyboard)

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

def format_lists(chat_id):
    d = get_chat_data(chat_id)
    lists = d["lists"]
    miladi, hijri = get_dates()
    status = "🟢 مفتوحة" if d["registration_open"] else "🔴 مغلقة"
    title_line = f"*__{d['list_title']}__*" if d["list_title"] else ""
    teacher_line = f"*__{d['teacher_name']}__*" if d["teacher_name"] else ""

    readers = lists["تسجيل"]
    read_ids = [m.rsplit('[',1)[1].rstrip(']') for m in lists["قرأت"]]
    readers_text = "\n".join(
        f"  {i+1}\\. {m.rsplit('[',1)[0].strip()} {'✅' if m.rsplit('[',1)[1].rstrip(']') in read_ids else ''}"
        for i,m in enumerate(readers)
    ) if readers else ""

    listeners = lists["مستمعة"]
    listeners_text = "\n".join(f"  {i+1}\\. {m.rsplit('[',1)[0].strip()}" for i,m in enumerate(listeners)) if listeners else ""

    text = f"""📅 {miladi}
          {hijri}
     ❀ ──── ✿ ──── ❀

   عنوان الحلقة : {title_line}
   معلمة الحلقة : {teacher_line}

☜ المسجلات للقراءة:
{readers_text}

🎧 المستمعات :
{listeners_text}

   ·:·:·:·:·:·:·:·
   اللّهمَّ صلِّ وسلِّمْ
   وبَارِكْ على نبيِّنَا
          محمد ﷺ

📌 الحالة: {status}"""
    return text

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("👋 أهلاً!\nهذا البوت يعمل فقط بالمجموعة")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    d = get_chat_data(chat_id)
    try:
        await update.message.delete()
    except:
        pass
    if d["last_msg"]:
        try:
            await ctx.bot.delete_message(chat_id, d["last_msg"])
        except:
            pass
    msg = await ctx.bot.send_message(chat_id, format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")
    d["last_msg"] = msg.message_id

async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("🚫 هذا الأمر يعمل بالمجموعة فقط!")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    d = get_chat_data(chat_id)
    for key in d["lists"]:
        d["lists"][key] = []
    d["registration_open"] = True
    d["list_title"] = ""
    d["teacher_name"] = ""
    try:
        await update.message.delete()
    except:
        pass
    if d["last_msg"]:
        try:
            await ctx.bot.delete_message(chat_id, d["last_msg"])
        except:
            pass
    msg = await ctx.bot.send_message(chat_id, format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")
    d["last_msg"] = msg.message_id

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("🚫 هذا الأمر يعمل بالمجموعة فقط!")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    await update.message.reply_text(format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")

async def handle_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    name = user.full_name
    user_id = user.id
    chat_id = query.message.chat.id
    data = query.data
    d = get_chat_data(chat_id)
    lists = d["lists"]
    await query.answer()

    if data == "set_title":
        if not await is_admin(user_id, chat_id, ctx.bot):
            await query.answer("🚫 للمشرفين فقط!", show_alert=True)
            return
        ctx.bot_data[f"waiting_{chat_id}"] = {"msg": query.message.message_id, "user": user_id}
        await ctx.bot.send_message(chat_id, "✏️ اكتبي عنوان الحلقة:")
        return

    elif data.startswith("join:"):
        if not d["registration_open"]:
            await query.answer("🔴 التسجيل مغلق!", show_alert=True)
            return
        role = data.split(":",1)[1]
        for key in lists:
            if key != "قرأت":
                lists[key] = [m for m in lists[key] if not m.endswith(f"[{user_id}]")]
        lists[role].append(f"{name} [{user_id}]")
        if role == "معلمة":
            d["teacher_name"] = name
        await query.edit_message_text(format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")

    elif data == "mark_read":
        if not any(m.endswith(f"[{user_id}]") for m in lists["تسجيل"]):
            await query.answer("سجّلي نفسك أولاً!", show_alert=True)
            return
        if not any(m.endswith(f"[{user_id}]") for m in lists["قرأت"]):
            lists["قرأت"].append(f"{name} [{user_id}]")
        await query.answer("✅ تم تسجيل قراءتك!", show_alert=True)
        await query.edit_message_text(format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")

    elif data == "remove_me":
        for key in lists:
            lists[key] = [m for m in lists[key] if not m.endswith(f"[{user_id}]")]
        await query.edit_message_text(format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")

    elif data.startswith("admin:"):
        if not await is_admin(user_id, chat_id, ctx.bot):
            await query.answer("🚫 للمشرفين فقط!", show_alert=True)
            return
        action = data.split(":",1)[1]
        if action == "close":
            d["registration_open"] = False
            await query.answer("🔴 تم الغلق", show_alert=True)
        elif action == "open":
            d["registration_open"] = True
            await query.answer("🟢 تم الفتح", show_alert=True)
        await query.edit_message_text(format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    key = f"waiting_{chat_id}"
    if key not in ctx.bot_data:
        return
    if ctx.bot_data[key]["user"] != user_id:
        return
    d = get_chat_data(chat_id)
    d["list_title"] = update.message.text
    msg_id = ctx.bot_data.pop(key)["msg"]
    try:
        await update.message.delete()
    except:
        pass
    try:
        await ctx.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=format_lists(chat_id), reply_markup=main_keyboard(), parse_mode="MarkdownV2")
    except:
        pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 البوت شغّال!")
    app.run_polling()

if __name__ == "__main__":
    main()
