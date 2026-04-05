import os
import json
import threading
from flask import Flask, render_template, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# ENV Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHANNEL_USERNAME = "@skkmediabd"

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

app = Flask(__name__)

def load_data(file):
    if not os.path.exists(file): return []
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route("/")
def home():
    return "SK Media Bot is Active 🚀"

@app.route("/app")
def webapp():
    return render_template("index.html")

@app.route("/movies")
def movies_api():
    return jsonify(load_data(MOVIE_FILE))

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    users = load_data(USER_FILE)
    if str(user_id) not in users:
        users.append(str(user_id))
        save_data(USER_FILE, users)

    webapp_url = f"{WEB_APP_URL}/app"
    keyboard = [[InlineKeyboardButton("🎬 Movie দেখুন", web_app=WebAppInfo(url=webapp_url))]]
    update.message.reply_text("Welcome to SK Media 🍿", reply_markup=InlineKeyboardMarkup(keyboard))

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
