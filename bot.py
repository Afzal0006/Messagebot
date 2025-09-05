import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from pymongo import MongoClient

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- CONFIG ---
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = 6998916494  # Owner ID

# --- Mongo Setup ---
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# === Pagination Helper ===
GROUPS_PER_PAGE = 15


def build_list_page(groups, page: int):
    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE
    text = f"📌 Saved Groups (Page {page+1}):\n\n"

    for i, g in enumerate(groups[start:end], start=1 + start):
        title = g.get("title", "Unknown")
        link = g.get("invite_link")
        if link:
            text += f"{i}. [{title}]({link})\n"
        else:
            text += f"{i}. {title} ❌ (No Link)\n"

    nav_buttons = []
    if page > 0:
        nav_buttons.append(f"⬅ Prev|list:{page-1}")
    if end < len(groups):
        nav_buttons.append(f"➡ Next|list:{page+1}")

    return text, nav_buttons


# === When Bot is Added to Group ===
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            title = update.effective_chat.title

            # Export invite link (agar bot ke paas admin rights hain)
            invite_link = None
            try:
                invite_link = await context.bot.export_chat_invite_link(chat_id)
            except Exception:
                pass

            # Save group
            groups_col.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": title, "invite_link": invite_link}},
                upsert=True
            )
            logging.info(f"✅ Bot added in {title} ({chat_id})")


# === /list Command ===
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this command!")

    groups = list(groups_col.find())
    if not groups:
        return await update.message.reply_text("❌ No groups saved yet.")

    text, nav = build_list_page(groups, 0)

    keyboard = []
    if nav:
        row = []
        for btn in nav:
            label, data = btn.split("|")
            row.append({"text": label, "callback_data": data})
        keyboard.append(row)

    await update.message.reply_text(
        text, parse_mode="Markdown", disable_web_page_preview=True,
        reply_markup={"inline_keyboard": keyboard} if keyboard else None
    )


# === Pagination Callback ===
async def list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("list:"):
        return

    page = int(data.split(":")[1])
    groups = list(groups_col.find())
    text, nav = build_list_page(groups, page)

    keyboard = []
    if nav:
        row = []
        for btn in nav:
            label, d = btn.split("|")
            row.append({"text": label, "callback_data": d})
        keyboard.append(row)

    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup={"inline_keyboard": keyboard} if keyboard else None
    )


# === /broadcast Command ===
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this command!")

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <your message>")

    message = " ".join(context.args)
    success, failed = 0, 0

    for group in groups_col.find():
        chat_id = group.get("chat_id")
        if not chat_id:
            continue
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            success += 1
        except Exception as e:
            logging.error(f"Failed in {chat_id}: {e}")
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast finished!\n✅ Sent: {success}\n❌ Failed: {failed}"
    )


# === Main ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added))
    app.add_handler(CommandHandler("list", list_groups))
    app.add_handler(CallbackQueryHandler(list_callback, pattern="^list:"))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("🤖 Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
