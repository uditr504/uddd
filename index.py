import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import os

# ====== Environment Variables ======
TOKEN = os.getenv("8258736243:AAHW-3sRw-Xll94C0LouNEQFM1T9S50T318")
MONGO_URL = os.getenv("mongodb+srv://premashilarana681_db_user:GMucI9xhkmvNUOX2@cluster0.8mlerkv.mongodb.net/?appName=Cluster0")
OWNER_ID = int(os.getenv("7342896170"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== MongoDB Setup ======
client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
users_collection = db["users"]
blocked_collection = db["blocked"]

# ====== Auto Join Request Approver ======
@bot.chat_join_request_handler()
def approve_request(request):
    bot.approve_chat_join_request(request.chat.id, request.from_user.id)
    if not users_collection.find_one({"user_id": request.from_user.id}):
        users_collection.insert_one({"user_id": request.from_user.id})

# ====== /start Command with Buttons ======
@bot.message_handler(commands=['start'])
def start(message):
    if blocked_collection.find_one({"user_id": message.from_user.id}):
        return

    if not users_collection.find_one({"user_id": message.from_user.id}):
        users_collection.insert_one({"user_id": message.from_user.id})

    markup = InlineKeyboardMarkup()
    
    # Add To Channel Button (bot invite link)
    add_channel_btn = InlineKeyboardButton(
        "➕ ADD TO CHANNEL",
        url=f"https://t.me/{bot.get_me().username}?startchannel=true"
    )
    # Join Update Channel Button (replace YOUR_UPDATE_CHANNEL)
    join_update_btn = InlineKeyboardButton(
        "📢 JOIN UPDATE CHANNEL",
        url="https://t.me/UD_Botz"
    )

    markup.add(add_channel_btn)
    markup.add(join_update_btn)

    bot.send_message(
        message.chat.id,
        "🤖 Bot Active Hai!\n\nNeeche buttons ka use karein:",
        reply_markup=markup
    )

# ====== Broadcast (Owner Only) ======
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

# ====== Block User ======
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

# ====== Unblock User ======
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

# ====== Bot Info ======
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

# ====== Channel Members Count ======
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

# ====== Run Bot ======
print("Bot Running...")
bot.infinity_polling()
