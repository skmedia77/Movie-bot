import json
import os
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler

# ENV VARIABLES (Render থেকে আসবে)
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# ---------------- DATABASE FILES ----------------
MOVIE_DB = "movies.json"
USER_DB = "users.json"

# create files if not exist
for file in [MOVIE_DB, USER_DB]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(update):
    return update.message.from_user.id == ADMIN_ID

# ---------------- USER SAVE SYSTEM ----------------
def save_user(user_id):
    users = load_json(USER_DB)
    if user_id not in users:
        users.append(user_id)
        save_json(USER_DB, users)

# ---------------- BOT COMMANDS ----------------

# /start
def start(update, context):
    user_id = update.message.from_user.id
    save_user(user_id)

    update.message.reply_text(
        "🎬 Welcome to SK Media!\n\n"
        "Mini App খুলতে নিচের বাটনে ক্লিক করো 👇"
    )

# /addmovie (Admin only)
def add_movie(update, context):
    if not is_admin(update):
        update.message.reply_text("❌ You are not authorized!")
        return

    try:
        text = update.message.text.replace("/addmovie ", "")
        name, poster, link = text.split("|")

        movies = load_json(MOVIE_DB)
        movies.append({
            "name": name.strip(),
            "poster": poster.strip(),
            "link": link.strip()
        })
        save_json(MOVIE_DB, movies)

        update.message.reply_text("✅ Movie Added!")

    except:
        update.message.reply_text("Format:\n/addmovie Name | Poster | Link")

# /broadcast (Admin only)
def broadcast(update, context):
    if not is_admin(update):
        update.message.reply_text("❌ Admin only!")
        return

    message = update.message.text.replace("/broadcast ", "")
    users = load_json(USER_DB)

    sent = 0
    for user in users:
        try:
            bot.send_message(chat_id=user, text=message)
            sent += 1
        except:
            pass

    update.message.reply_text(f"📢 Broadcast sent to {sent} users!")

# /stats (Admin only)
def stats(update, context):
    if not is_admin(update):
        return

    users = load_json(USER_DB)
    movies = load_json(MOVIE_DB)

    update.message.reply_text(
        f"👥 Users: {len(users)}\n🎬 Movies: {len(movies)}"
    )

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("addmovie", add_movie))
dispatcher.add_handler(CommandHandler("broadcast", broadcast))
dispatcher.add_handler(CommandHandler("stats", stats))

# ---------------- WEBHOOK ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# ---------------- MINI APP API ----------------

# get movie list
@app.route("/movies")
def get_movies():
    return jsonify(load_json(MOVIE_DB))

# user count
@app.route("/users")
def user_count():
    users = load_json(USER_DB)
    return jsonify({"total_users": len(users)})

# home
@app.route("/")
def home():
    return "SK Media Bot Running 🚀"

# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
