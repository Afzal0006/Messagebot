import logging, random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# ====== CONFIG ======
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "broadcast_db"
OWNER_ID = 7270006608  # Change to your Telegram ID
# ====================

logging.basicConfig(level=logging.INFO)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
groups_col = db["groups"]

# जब bot किसी group में add हो
async def group_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        groups_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"title": chat.title}},
            upsert=True
        )

        messages = [
            "✅ Bot activated for this group!",
            "🤖 Hello everyone! I'm here to help manage and broadcast messages.",
            "📢 Use /broadcast <message> to send announcements to all groups.",
            "⚙️ Only the owner can use /broadcast command.",
            "💾 Group saved successfully in my database.",
            f"👥 Group Name: {chat.title}"
        ]

        for msg in messages:
            await update.message.reply_text(msg)

        logging.info(f"Group saved: {chat.title} ({chat.id})")

# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("⛔ Only owner can use this command!")

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")

    message = " ".join(context.args)

    groups = groups_col.find()
    success, fail = 0, 0
    for g in groups:
        try:
            await context.bot.send_message(chat_id=g["chat_id"], text=message)
            success += 1
        except Exception as e:
            logging.warning(f"Failed: {g['chat_id']} ({e})")
            fail += 1

    await update.message.reply_text(f"✅ Sent: {success} | ❌ Failed: {fail}")


# 🔄 Auto 24h Random Message Sender
RANDOM_MESSAGES = [
    "🌞 Good Morning! Stay positive today!",
    "💡 Tip of the day: Consistency beats motivation.",
    "🌙 Good Night! Sleep well and recharge.",
    "🔥 Stay focused and keep pushing forward!",
    "📢 Reminder: Use /broadcast <msg> to reach all groups instantly.",
    "🤖 I’m your helpful bot – always active here!"
]

async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    groups = groups_col.find()
    for g in groups:
        try:
            msg = random.choice(RANDOM_MESSAGES)
            await context.bot.send_message(chat_id=g["chat_id"], text=msg)
            logging.info(f"Sent random msg to {g['chat_id']}: {msg}")
        except Exception as e:
            logging.warning(f"Failed random msg to {g['chat_id']} ({e})")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_added))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Auto 24h random message
    job_queue = app.job_queue
    job_queue.run_repeating(send_random_message, interval=86400, first=10)  
    # 86400 sec = 24h | "first=10" means start after 10 sec when bot runs

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
