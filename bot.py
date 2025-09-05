import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

# =============== CONFIG ===============
BOT_TOKEN = "8250718066:AAEA0w45WBRtPhPjcr-A3lhGLheHNNM4qUw"
OWNER_ID = 7270006608   # <- yaha apna Telegram ID daalo

MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # apna Mongo URI
DB_NAME = "broadcast_bot"
COLLECTION = "chats"
# ======================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
chats_col = db[COLLECTION]


# ✅ jab bhi bot add hoga /start ya group me -> save karo
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or update.effective_chat.first_name

    if not chats_col.find_one({"chat_id": chat_id}):
        chats_col.insert_one({"chat_id": chat_id, "title": chat_title})
        logging.info(f"Saved chat: {chat_title} ({chat_id})")

    await update.message.reply_text("✅ Bot is active here!")


# ✅ Broadcast sirf Owner ke liye
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not authorized!")

    if not context.args:
        return await update.message.reply_text("⚠ Usage: /broadcast Your Message")

    text = " ".join(context.args)

    chats = list(chats_col.find())
    success = 0
    fail = 0

    for chat in chats:
        try:
            await context.bot.send_message(chat_id=chat["chat_id"], text=text)
            success += 1
        except Exception as e:
            logging.warning(f"Failed to send to {chat['chat_id']}: {e}")
            fail += 1

    await update.message.reply_text(f"📢 Broadcast done!\n✅ Sent: {success}\n❌ Failed: {fail}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("🤖 Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
