import os
import json
import threading
from flask import Flask, render_template, jsonify

from telegram import (
    Update, WebAppInfo,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Updater, CommandHandler,
    CallbackContext, CallbackQueryHandler
)

# ========= ENV =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHANNEL_USERNAME = "@skkmediabd"

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

app = Flask(__name__)

# ========= FLASK ROUTES =========

@app.route("/")
def home():
    return "SK Media Bot Running"

@app.route("/app")
def webapp():
    return render_template("index.html")

@app.route("/movies")
def movies_api():
    if not os.path.exists(MOVIE_FILE):
        return jsonify([])
    with open(MOVIE_FILE) as f:
        return jsonify(json.load(f))


# ========= FORCE JOIN CHECK =========

def is_user_joined(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False


# ========= START COMMAND =========

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Force Join
    if not is_user_joined(context.bot, user_id):
        join_btn = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/skkmediabd")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]
        update.message.reply_text(
            "Mini App ব্যবহার করতে আগে Channel join করুন 👇",
            reply_markup=InlineKeyboardMarkup(join_btn)
        )
        return

    # Save user
    user_id_str = str(user_id)
    if os.path.exists(USER_FILE):
        users = json.load(open(USER_FILE))
    else:
        users = []

    if user_id_str not in users:
        users.append(user_id_str)
        json.dump(users, open(USER_FILE, "w"))

    # Open Mini App Button
    webApp = WebAppInfo(url=WEB_APP_URL)
    keyboard = [[InlineKeyboardButton("🎬 Open SK Media", web_app=webApp)]]

    update.message.reply_text(
        "Welcome to SK Media 🍿",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ========= JOIN CONFIRM BUTTON =========

def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if is_user_joined(context.bot, user_id):
        webApp = WebAppInfo(url=WEB_APP_URL)
        keyboard = [[InlineKeyboardButton("🎬 Open SK Media", web_app=webApp)]]

        query.message.reply_text(
            "ধন্যবাদ! এখন App ব্যবহার করতে পারো ✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        query.answer("এখনো join করো নাই ❌", show_alert=True)


# ========= ADD MOVIE =========

def add_movie(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != ADMIN_ID:
        update.message.reply_text("Admin only ❌")
        return

    try:
        data = update.message.text.replace("/addmovie ", "")
        title, poster, link, category = data.split("|")

        new_movie = {
            "title": title.strip(),
            "poster": poster.strip(),
            "link": link.strip(),
            "category": category.strip()
        }

        if os.path.exists(MOVIE_FILE):
            movies = json.load(open(MOVIE_FILE))
        else:
            movies = []

        movies.append(new_movie)
        json.dump(movies, open(MOVIE_FILE, "w"))

        update.message.reply_text("Movie Added Successfully 🎬")

    except:
        update.message.reply_text(
            "Use:\n/addmovie Name | Poster | Link | Category"
        )


# ========= BROADCAST =========

def broadcast(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != ADMIN_ID:
        return

    msg = update.message.text.replace("/broadcast ", "")

    if not os.path.exists(USER_FILE):
        update.message.reply_text("No users found")
        return

    users = json.load(open(USER_FILE))

    for user in users:
        try:
            context.bot.send_message(chat_id=user, text=msg)
        except:
            pass

    update.message.reply_text("Broadcast sent ✅")


# ========= RUN BOT =========

def run_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addmovie", add_movie))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    updater.start_polling()
    updater.idle()


# Run bot in background thread
threading.Thread(target=run_bot).start()


# ========= RUN FLASK =========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
