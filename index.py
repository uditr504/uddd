import os
from flask import Flask, request
import telebot
from pymongo import MongoClient

# ===== Environment Variables =====
TOKEN = os.getenv("8258736243:AAHW-3sRw-Xll94C0LouNEQFM1T9S50T318")
OWNER_ID = int(os.getenv("7342896170"))
MONGO_URL = os.getenv("mongodb+srv://premashilarana681_db_user:GMucI9xhkmvNUOX2@cluster0.8mlerkv.mongodb.net/?appName=Cluster0")
UPDATE_CHANNEL = os.getenv("https://t.me/UD_Botz")  # Telegram update channel link

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
users_collection = db["users"]
blocked_collection = db["blocked"]

app = Flask(__name__)

# ===== Auto Join Request Approve =====
@bot.chat_join_request_handler()
def approve_request(request):
    bot.approve_chat_join_request(request.chat.id, request.from_user.id)
    if not users_collection.find_one({"user_id": request.from_user.id}):
        users_collection.insert_one({"user_id": request.from_user.id})

# ===== /start Command =====
@bot.message_handler(commands=['start'])
def start(message):
    if blocked_collection.find_one({"user_id": message.from_user.id}):
        return
    if not users_collection.find_one({"user_id": message.from_user.id}):
        users_collection.insert_one({"user_id": message.from_user.id})

    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ ADD TO CHANNEL", url=f"https://t.me/{bot.get_me().username}?startchannel=true"))
    markup.add(InlineKeyboardButton("📢 JOIN UPDATE CHANNEL", url=UPDATE_CHANNEL))
    bot.send_message(message.chat.id, "🤖 Bot Active!\nUse buttons below:", reply_markup=markup)

# ===== Broadcast (Owner Only) =====
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace("/broadcast ", "")
    success = 0
    for user in users_collection.find():
        if not blocked_collection.find_one({"user_id": user["user_id"]}):
            try:
                bot.send_message(user["user_id"], text)
                success += 1
            except: pass
    bot.reply_to(message, f"✅ Broadcast Sent To {success} Users")

# ===== Block / Unblock Users =====
@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id != OWNER_ID: return
    try:
        user_id = int(message.text.split()[1])
        if not blocked_collection.find_one({"user_id": user_id}):
            blocked_collection.insert_one({"user_id": user_id})
            bot.reply_to(message, "🚫 User Blocked")
    except:
        bot.reply_to(message, "Use: /block USER_ID")

@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.from_user.id != OWNER_ID: return
    try:
        user_id = int(message.text.split()[1])
        blocked_collection.delete_one({"user_id": user_id})
        bot.reply_to(message, "✅ User Unblocked")
    except:
        bot.reply_to(message, "Use: /unblock USER_ID")

# ===== Bot Info =====
@bot.message_handler(commands=['info'])
def info(message):
    if message.from_user.id != OWNER_ID: return
    total_users = users_collection.count_documents({})
    blocked_users = blocked_collection.count_documents({})
    bot.reply_to(message, f"📊 Bot Info\n👥 Total Users: {total_users}\n🚫 Blocked Users: {blocked_users}")

# ===== Members Count =====
@bot.message_handler(commands=['members'])
def members(message):
    if message.from_user.id != OWNER_ID: return
    try:
        chat_id = message.text.split()[1]
        count = bot.get_chat_members_count(chat_id)
        bot.reply_to(message, f"👥 Members: {count}")
    except:
        bot.reply_to(message, "Use: /members @channelusername")

# ===== Flask Webhook =====
@app.route("/"+TOKEN, methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running", 200

# ===== Start Server =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR_RENDER_URL/{TOKEN}")  # Replace YOUR_RENDER_URL
    app.run(host="0.0.0.0", port=port)
