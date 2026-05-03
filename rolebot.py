#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from hijri_converter import convert
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8703353514:AAEcMYN3QzZjU8Qz9N53lGu-Ddx_5SKB3FM"
SUPER_ADMIN = [6115157843]

lists = {"معلمة": [], "قراءة": [], "مستمعة": [], "معتذرة": []}
registration_open = True
list_title = ""
teacher_name = ""

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
        [InlineKeyboardButton("📚 معلمة", callback_data="join:معلمة"), InlineKeyboardButton("📝 تسجيل قراءة", callback_data="join:قراءة")],
        [InlineKeyboardButton("🎧 مستمعة", callback_data="join:مستمعة"), InlineKeyboardButton("🌸 معتذرة", callback_data="join:معتذرة")],
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

def format_lists():
    miladi, hijri = get_dates()
    status = "🟢 مفتوحة" if registration_open else "🔴 مغلقة"
    title_line = list_title if list_title else ""
    teacher_line = teacher_name if teacher_name else ""
    readers = lists["قراءة"]
    readers_text = "\n".join(f"  {i+1}. {m.rsplit('[',1)[0].strip()}" for i,m in enumerate(readers)) if readers else ""
    listeners = lists["مستمعة"]
    listeners_text = "\n".join(f"  {i+1}. {m.rsplit('[',1)[0].strip()}" for i,m in enumerate(listeners)) if listeners else ""
    excused = lists["معتذرة"]
    excused_text = "\n".join(f"  {i+1}. {m.rsplit('[',1)[0].strip()}" for i,m in enumerate(excused)) if excused else "لا توجد معتذرات"
    text = f"""📅 {miladi}
          {hijri}
     ❀ ──── ✿ ──── ❀

   عنوان الحلقة : {title_line}
   معلمة الحلقة : {teacher_line}

☜ المسجلات للقراءة:
{readers_text}

🎧 المستمعات :
{listeners_text}

🌸 المعتذرات:
{excused_text}

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
        await update.message.reply_text("👋 أهلاً!\nهذا البوت يعمل فقط بالمجموعة.\nانضمي للمجموعة واضغطي على الأزرار هناك ✅")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    try:
        await update.message.delete()
    except:
        pass
    if "last_msg" in ctx.bot_data:
        try:
            await ctx.bot.delete_message(chat_id, ctx.bot_data["last_msg"])
        except:
            pass
    msg = await ctx.bot.send_message(chat_id, format_lists(), reply_markup=main_keyboard())
    ctx.bot_data["last_msg"] = msg.message_id

async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global registration_open, list_title, teacher_name
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("🚫 هذا الأمر يعمل بالمجموعة فقط!")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    for key in lists:
        lists[key] = []
    registration_open = True
    list_title = ""
    teacher_name = ""
    try:
        await update.message.delete()
    except:
        pass
    if "last_msg" in ctx.bot_data:
        try:
            await ctx.bot.delete_message(chat_id, ctx.bot_data["last_msg"])
        except:
            pass
    msg = await ctx.bot.send_message(chat_id, "🆕 تم فتح قائمة جديدة!\n\n" + format_lists(), reply_markup=main_keyboard())
    ctx.bot_data["last_msg"] = msg.message_id

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("🚫 هذا الأمر يعمل بالمجموعة فقط!")
        return
    if not await is_admin(user_id, chat_id, ctx.bot):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط!")
        return
    await update.message.reply_text(format_lists(), reply_markup=main_keyboard())

async def handle_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global registration_open, list_title, teacher_name
    query = update.callback_query
    user = query.from_user
    name = user.full_name
    user_id = user.id
    chat_id = query.message.chat.id
    data = query.data
    await query.answer()
    if data == "set_title":
        if not await is_admin(user_id, chat_id, ctx.bot):
            await query.answer("🚫 للمشرفين فقط!", show_alert=True)
            return
        ctx.bot_data["waiting_title_chat"] = chat_id
        ctx.bot_data["waiting_title_msg"] = query.message.message_id
        ctx.bot_data["waiting_title_user"] = user_id
        await ctx.bot.send_message(chat_id, "✏️ اكتبي عنوان الحلقة:")
        return
    elif data.startswith("join:"):
        if not registration_open:
            await query.answer("🔴 التسجيل مغلق!", show_alert=True)
            return
        role = data.split(":",1)[1]
        for key in lists:
            lists[key] = [m for m in lists[key] if not m.endswith(f"[{user_id}]")]
        lists[role].append(f"{name} [{user_id}]")
        if role == "معلمة":
            teacher_name = name
        await query.edit_message_text(format_lists(), reply_markup=main_keyboard())
    elif data == "remove_me":
        for key in lists:
            lists[key] = [m for m in lists[key] if not m.endswith(f"[{user_id}]")]
        await query.edit_message_text(format_lists(), reply_markup=main_keyboard())
    elif data.startswith("admin:"):
        if not await is_admin(user_id, chat_id, ctx.bot):
            await query.answer("🚫 للمشرفين فقط!", show_alert=True)
            return
        action = data.split(":",1)[1]
        if action == "close":
            registration_open = False
            await query.answer("🔴 تم الغلق", show_alert=True)
        elif action == "open":
            registration_open = True
            await query.answer("🟢 تم الفتح", show_alert=True)
        await query.edit_message_text(format_lists(), reply_markup=main_keyboard())

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global list_title
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if ctx.bot_data.get("waiting_title_chat") != chat_id:
        return
    if ctx.bot_data.get("waiting_title_user") != user_id:
        return
    list_title = update.message.text
    ctx.bot_data.pop("waiting_title_chat", None)
    ctx.bot_data.pop("waiting_title_user", None)
    try:
        await update.message.delete()
    except:
        pass
    msg_id = ctx.bot_data.get("waiting_title_msg")
    if msg_id:
        try:
            await ctx.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=format_lists(), reply_markup=main_keyboard())
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
