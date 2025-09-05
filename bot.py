import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- CONFIG ---
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"   
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  
OWNER_ID = 7270006608  

# --- Mongo Setup ---
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# --- Welcome Messages ---
WELCOME_MESSAGES = [
    """🎬 YT Premium चाहिए किसी को exchange में?
📩 Need Instagram old account – DM me asap""",
    """⚡ I need 16-22 Location group – DM fast, high price ☑️
📌 High SMS only 🙀""",
    """🟢 I sell WhatsApp & Telegram accounts:
• Whatsapp: ₹150 / India (Permanent – Never ban)
• Telegram: ₹80 / (Permanent – Never ban)""",
    """✅ 1-1 करके ले सकते हो, proofs available।
💰 Payment first or escrow.""",
    """🔥 Urgent Need!
Baaghi 4 चाहिए भाई, जिसके पास हो तो message करे… 🍿🎥"""
]

# --- When Bot is Added to Group ---
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            title = update.effective_chat.title

            # Save group in MongoDB
            groups_col.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": title}},
                upsert=True
            )

            logging.info(f"✅ Bot added in {title} ({chat_id})")

            # Send all 5 welcome messages
            for msg in WELCOME_MESSAGES:
                await context.bot.send_message(chat_id=chat_id, text=msg)

# --- Broadcast Command (Owner Only) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this command!")

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast your_message")

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
            logging.error(f"❌ Failed to send in {chat_id}: {e}")
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast completed!\n✅ Sent: {success}\n❌ Failed: {failed}"
    )

# --- List Groups Command (Owner Only) ---
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this command!")

    groups = groups_col.find()
    buttons = []
    count = 0

    for g in groups:
        chat_id = g.get("chat_id")
        title = g.get("title", "Unknown")

        try:
            # Generate invite link
            link = await context.bot.create_chat_invite_link(chat_id)
            buttons.append([InlineKeyboardButton(title, url=link.invite_link)])
        except Exception as e:
            logging.error(f"❌ Failed to get link for {chat_id}: {e}")
            buttons.append([InlineKeyboardButton(f"{title} (No Link)", url="https://t.me/")])

        count += 1

    if count == 0:
        return await update.message.reply_text("❌ No groups saved yet.")

    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📌 Saved Groups:", reply_markup=keyboard)

# --- Main Function ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("list", list_groups))  # ✅ Inline button list

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
