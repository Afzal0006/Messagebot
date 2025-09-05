import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"   # BotFather token
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = 7270006608  # Owner Telegram ID

# --- Mongo Setup ---
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# === Pagination Helper ===
GROUPS_PER_PAGE = 15


def build_page_text(groups, page: int):
    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE
    page_groups = groups[start:end]

    text = f"📌 Saved Groups (Page {page+1}):\n\n"
    for i, g in enumerate(page_groups, start=1 + start):
        title = g.get("title", "Unknown")
        link = g.get("invite_link")
        if link:
            text += f"{i}. [{title}]({link})\n"
        else:
            text += f"{i}. {title} ❌ No Link\n"
    return text


def build_nav_buttons(groups, page: int):
    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅ Prev", callback_data=f"list:{page-1}"))
    if end < len(groups):
        nav_buttons.append(InlineKeyboardButton("➡ Next", callback_data=f"list:{page+1}"))

    if nav_buttons:
        return InlineKeyboardMarkup([nav_buttons])
    return None


# === When Bot is Added to Group ===
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            title = update.effective_chat.title

            # Export invite link (agar bot ke paas admin + invite rights hai)
            invite_link = None
            try:
                invite_link = await context.bot.export_chat_invite_link(chat_id)
            except Exception:
                pass

            # Save group in MongoDB
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

    text = build_page_text(groups, 0)
    nav = build_nav_buttons(groups, 0)

    await update.message.reply_text(
        text,
        reply_markup=nav,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


# === Callback for Pagination ===
async def list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("list:"):
        return

    page = int(data.split(":")[1])
    groups = list(groups_col.find())

    text = build_page_text(groups, page)
    nav = build_nav_buttons(groups, page)

    await query.edit_message_text(
        text=text,
        reply_markup=nav,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


# === Broadcast Command (Owner Only) ===
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this command!")

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast your_message")

    message = " ".join(context.args)

    success, failed = 0, 0
    groups = list(groups_col.find())

    for g in groups:
        chat_id = g.get("chat_id")
        if not chat_id:
            continue
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            success += 1
        except Exception as e:
            logging.error(f"❌ Failed to send in {chat_id}: {e}")
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
