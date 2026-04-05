import os
import json
import threading
from flask import Flask, render_template, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# ========= ENV =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHANNEL_USERNAME = "@skkmediabd"

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

app = Flask(__name__)

# Helper function to read/write JSON safely
def load_json(filename, default=[]):
    if not os.path.exists(filename):
        return default
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ========= FLASK ROUTES =========
@app.route("/")
def home():
    return "SK Media Bot is Running 🚀"

@app.route("/movies")
def movies_api():
    return jsonify(load_json(MOVIE_FILE))

# ========= FORCE JOIN CHECK =========
def is_user_joined(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except Exception:
        return False

# ========= START COMMAND =========
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)

    # Force Join
    if not is_user_joined(context.bot, user_id):
        join_btn = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]
        update.message.reply_text(
            "Mini App ব্যবহার করতে আগে আমাদের চ্যানেলে join করুন 👇",
            reply_markup=InlineKeyboardMarkup(join_btn)
        )
        return

    # Save user effectively
    users = load_json(USER_FILE)
    if user_id_str not in users:
        users.append(user_id_str)
        save_json(USER_FILE, users)

    # Open Mini App Button
    web_app_info = WebAppInfo(url=WEB_APP_URL)
    keyboard = [[InlineKeyboardButton("🎬 Open SK Media", web_app=web_app_info)]]

    update.message.reply_text(
        "Welcome to SK Media 🍿\nনিচের বাটনে ক্লিক করে মুভি এনজয় করুন!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= JOIN CONFIRM BUTTON =========
def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if is_user_joined(context.bot, user_id):
        web_app_info = WebAppInfo(url=WEB_APP_URL)
        keyboard = [[InlineKeyboardButton("🎬 Open SK Media", web_app=web_app_info)]]
        
        query.edit_message_text(
            "ধন্যবাদ! এখন App ব্যবহার করতে পারো ✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        query.answer("আপনি এখনো join করেননি! ❌", show_alert=True)

# ========= ADMIN: ADD MOVIE =========
def add_movie(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID:
        update.message.reply_text("আপনি এডমিন নন! ❌")
        return

    try:
        # Example: /addmovie Inception | https://image.jpg | https://movie.com | Action
        raw_text = update.message.text.split(None, 1)[1]
        parts = [p.strip() for p in raw_text.split("|")]
        
        if len(parts) != 4:
            raise ValueError

        new_movie = {
            "title": parts[0],
            "poster": parts[1],
            "link": parts[2],
            "category": parts[3]
        }

        movies = load_json(MOVIE_FILE)
        movies.append(new_movie)
        save_json(MOVIE_FILE, movies)

        update.message.reply_text("Movie Added Successfully 🎬")
    except:
        update.message.reply_text("সঠিক ফরম্যাট ব্যবহার করুন:\n/addmovie Name | Poster | Link | Category")

# ========= RUN BOT & FLASK =========
def run_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addmovie", add_movie))
    dp.add_handler(CommandHandler("broadcast", broadcast)) # broadcast function definition keeping previous logic
    dp.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Flask thread
    threading.Thread(target=run_bot, daemon=True).start()
    # Flask host config for Render/Replit
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
