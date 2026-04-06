import os
import json
import threading
from flask import Flask, render_template, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# ENV Variables (Render-এর Environment Variables থেকে আসবে)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHANNEL_USERNAME = "@skkmediabd"

MOVIE_FILE = "movies.json"
USER_FILE = "users.json"

app = Flask(__name__)

# ডাটাবেস লোড ও সেভ
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
    return "SK Media Bot is Active 🚀"

@app.route("/app")
def webapp():
    return render_template("index.html")

@app.route("/movies")
def movies_api():
    return jsonify(load_data(MOVIE_FILE))

# ========= BOT LOGIC =========
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    users = load_data(USER_FILE)
    if str(user_id) not in users:
        users.append(str(user_id))
        save_data(USER_FILE, users)

    # ওপেন অ্যাপ বাটন - নিশ্চিত করুন WEB_APP_URL এর শেষে /app যোগ করা হয়েছে
    final_url = f"{WEB_APP_URL}/app"
    keyboard = [[InlineKeyboardButton("🎬 Movie দেখুন", web_app=WebAppInfo(url=final_url))]]
    update.message.reply_text(f"স্বাগতম {update.effective_user.first_name}! 🍿", reply_markup=InlineKeyboardMarkup(keyboard))

# ব্রডকাস্টিং সিস্টেম
def broadcast(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return update.message.reply_text("মেসেজ দিন: /broadcast Hello")
    
    users = load_data(USER_FILE)
    for user in users:
        try: context.bot.send_message(chat_id=user, text=msg)
        except: continue
    update.message.reply_text("Broadcast Done!")

# সার্ভার ও বোট রান করার ইঞ্জিন
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    # v13.15 এর জন্য এই ফরম্যাটটিই সঠিক
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    
    print("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Flask কে আলাদা থ্রেডে চালানো যাতে বোট ব্লক না হয়
    threading.Thread(target=run_flask).start()
    run_bot()
