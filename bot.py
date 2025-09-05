import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- CONFIG ---
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"   # <-- अपना BotFather token डालें
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # <-- MongoDB URI डालें (Mongo Atlas भी चला सकते हो)
OWNER_ID = 7363327309  # <-- अपना Telegram User ID डालें

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
            chat_id = update.message.chat_id
            title = update.message.chat.title

            # Save group in MongoDB
            groups_col.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": title}},
                upsert=True
            )

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

    # Send to all saved groups
    success, failed = 0, 0
    for group in groups_col.find():
        try:
            await context.bot.send_message(chat_id=group["chat_id"], text=message)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 Broadcast done!\n✅ Success: {success}\n❌ Failed: {failed}")

# --- Main Function ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
