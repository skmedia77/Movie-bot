import json
import os
from flask import Flask, jsonify
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

app = Flask(__name__)

MOVIE_DB = "movies.json"
USER_DB = "users.json"

# create db files if not exist
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

def save_user(user_id):
    users = load_json(USER_DB)
    if user_id not in users:
        users.append(user_id)
        save_json(USER_DB, users)

# -------- BOT COMMANDS --------

def start(update, context):
    save_user(update.message.from_user.id)
    update.message.reply_text("🎬 Welcome to SK Media! Open menu to view movies")

def add_movie(update, context):
    if not is_admin(update):
        update.message.reply_text("❌ Admin only!")
        return
    try:
        text = update.message.text.replace("/addmovie ", "")
        name, poster, link = text.split("|")
        movies = load_json(MOVIE_DB)
        movies.append({"name": name.strip(), "poster": poster.strip(), "link": link.strip()})
        save_json(MOVIE_DB, movies)
        update.message.reply_text("✅ Movie Added")
    except:
        update.message.reply_text("Use:\n/addmovie Name | Poster | Link")

def broadcast(update, context):
    if not is_admin(update):
        return
    msg = update.message.text.replace("/broadcast ", "")
    users = load_json(USER_DB)
    sent = 0
    for u in users:
        try:
            context.bot.send_message(chat_id=u, text=msg)
            sent += 1
        except:
            pass
    update.message.reply_text(f"📢 Broadcast sent to {sent} users")

def stats(update, context):
    if not is_admin(update):
        return
    update.message.reply_text(
        f"Users: {len(load_json(USER_DB))}\nMovies: {len(load_json(MOVIE_DB))}"
    )

# -------- START POLLING --------
def start_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addmovie", add_movie))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("stats", stats))

    updater.start_polling()
    updater.idle()

# -------- MINI APP API --------
@app.route("/movies")
def movies():
    return jsonify(load_json(MOVIE_DB))

@app.route("/users")
def users():
    return jsonify({"total_users": len(load_json(USER_DB))})

@app.route("/")
def home():
    return "SK Media Running 🚀"

# Run bot + flask together
if __name__ == "__main__":
    from threading import Thread
    Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=10000)
