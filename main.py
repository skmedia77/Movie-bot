import os
import json
import threading
from flask import Flask, render_template, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# ========= কনফিগারেশন (ENV) =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # এটি স্ট্রিং হিসেবে আসবে
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHANNEL_USERNAME = "@skkmediabd"

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

app = Flask(__name__)

# --- ডাটাবেস ফাংশন ---
def load_data(file):
    if not os.path.exists(file): return []
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ========= FLASK ROUTES (ওয়েবসাইট) =========
@app.route("/")
def home():
    return "SK Media Bot is Running 🚀"

@app.route("/app")
def webapp():
    return render_template("index.html")

@app.route("/movies")
def movies_api():
    return jsonify(load_data(MOVIE_FILE))

# ========= BOT LOGIC =========
def is_user_joined(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except: return False

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # ইউজার সেভ
    users = load_data(USER_FILE)
    if str(user_id) not in users:
        users.append(str(user_id))
        save_data(USER_FILE, users)

    if not is_user_joined(context.bot, user_id):
        join_btn = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]
        update.message.reply_text("Mini App ব্যবহার করতে আগে Channel join করুন 👇", reply_markup=InlineKeyboardMarkup(join_btn))
        return

    # ওপেন অ্যাপ বাটন (সরাসরি /app রাউটে পাঠাবে)
    webapp_final_url = f"{WEB_APP_URL}/app"
    keyboard = [[InlineKeyboardButton("🎬 Movie দেখুন", web_app=WebAppInfo(url=webapp_final_url))]]
    update.message.reply_text(f"Welcome to SK Media 🍿", reply_markup=InlineKeyboardMarkup(keyboard))

def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    if is_user_joined(context.bot, query.from_user.id):
        webapp_final_url = f"{WEB_APP_URL}/app"
        query.edit_message_text("ধন্যবাদ! এখন মুভি দেখুন ✅", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Open App", web_app=WebAppInfo(url=webapp_final_url))]]))
    else:
        query.answer("এখনো join করো নাই ❌", show_alert=True)

def add_movie(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID: return
    try:
        data = update.message.text.replace("/addmovie ", "")
        parts = [p.strip() for p in data.split("|")]
        movie = {"title": parts[0], "poster": parts[1], "link": parts[2], "category": parts[3]}
        movies = load_data(MOVIE_FILE)
        movies.append(movie)
        save_data(MOVIE_FILE, movies)
        update.message.reply_text("Movie Added Successfully 🎬")
    except: update.message.reply_text("Use: /addmovie Name | Poster | Link | Category")

# ========= RUNNING ENGINE =========
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addmovie", add_movie))
    dp.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
