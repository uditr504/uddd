import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789  # 👈 Apna Telegram ID daalo

MONGO_URL = "mongodb+srv://premashilarana681_db_user:GMucI9xhkmvNUOX2@cluster0.8mlerkv.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
users_collection = db["users"]
blocked_collection = db["blocked"]

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


# ---------------------------
# AUTO JOIN REQUEST APPROVE
# ---------------------------
@bot.chat_join_request_handler()
def approve_request(request):
    bot.approve_chat_join_request(request.chat.id, request.from_user.id)

    if not users_collection.find_one({"user_id": request.from_user.id}):
        users_collection.insert_one({"user_id": request.from_user.id})


# ---------------------------
# START COMMAND WITH BUTTONS
# ---------------------------
@bot.message_handler(commands=['start'])
def start(message):
    if blocked_collection.find_one({"user_id": message.from_user.id}):
        return

    if not users_collection.find_one({"user_id": message.from_user.id}):
        users_collection.insert_one({"user_id": message.from_user.id})

    markup = InlineKeyboardMarkup()
    
    add_channel_btn = InlineKeyboardButton(
        "➕ ADD TO CHANNEL",
        url=f"https://t.me/{bot.get_me().username}?startchannel=true"
    )
    
    join_update_btn = InlineKeyboardButton(
        "📢 JOIN UPDATE CHANNEL",
        url="https://t.me/YOUR_UPDATE_CHANNEL"
    )

    markup.add(add_channel_btn)
    markup.add(join_update_btn)

    bot.send_message(
        message.chat.id,
        "🤖 Bot Active Hai!\n\nNeeche buttons ka use karein:",
        reply_markup=markup
    )


# ---------------------------
# BROADCAST (OWNER ONLY)
# ---------------------------
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
            except:
                pass

    bot.reply_to(message, f"✅ Broadcast Sent To {success} Users")


# ---------------------------
# BLOCK USER
# ---------------------------
@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        user_id = int(message.text.split()[1])
        if not blocked_collection.find_one({"user_id": user_id}):
            blocked_collection.insert_one({"user_id": user_id})
            bot.reply_to(message, "🚫 User Blocked")
    except:
        bot.reply_to(message, "Use: /block USER_ID")


# ---------------------------
# UNBLOCK USER
# ---------------------------
@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        user_id = int(message.text.split()[1])
        blocked_collection.delete_one({"user_id": user_id})
        bot.reply_to(message, "✅ User Unblocked")
    except:
        bot.reply_to(message, "Use: /unblock USER_ID")


# ---------------------------
# BOT INFO
# ---------------------------
@bot.message_handler(commands=['info'])
def info(message):
    if message.from_user.id != OWNER_ID:
        return

    total_users = users_collection.count_documents({})
    blocked_users = blocked_collection.count_documents({})

    bot.reply_to(message,
        f"""
📊 Bot Info

👥 Total Users: {total_users}
🚫 Blocked Users: {blocked_users}
        """
    )


# ---------------------------
# CHANNEL MEMBER COUNT
# ---------------------------
@bot.message_handler(commands=['members'])
def members(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        chat_id = message.text.split()[1]
        count = bot.get_chat_members_count(chat_id)
        bot.reply_to(message, f"👥 Members: {count}")
    except:
        bot.reply_to(message, "Use: /members @channelusername")


print("Bot Running...")
bot.infinity_polling()
