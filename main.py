import json
import os
from flask import Flask, send_file
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"


def load_movies():
    try:
        with open(MOVIES_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_movies(data):
    with open(MOVIES_FILE, "w") as f:
        json.dump(data, f)


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)


# ওয়েব হোম
@app.route("/")
def home():
    return "SK MEDIA BOT RUNNING"


@app.route("/app")
def mini_app():
    return send_file("index.html")


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        save_users(users)

    await update.message.reply_text("Welcome to SK Media 🎬")


# movie add
async def addmovie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if text == "":
        await update.message.reply_text("Use: /addmovie Movie Name")
        return

    movies = load_movies()
    movies.append(text)
    save_movies(movies)

    await update.message.reply_text("Movie Added ✅")


# movie list
async def movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies = load_movies()

    if not movies:
        await update.message.reply_text("No movies yet")
        return

    msg = "🎬 Movie List:\n\n"
    for m in movies:
        msg += f"• {m}\n"

    await update.message.reply_text(msg)


# broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != int(os.environ.get("ADMIN_ID")):
        return

    text = " ".join(context.args)
    users = load_users()

    for user in users:
        try:
            await context.bot.send_message(user, text)
        except:
            pass

    await update.message.reply_text("Broadcast sent ✅")


def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addmovie", addmovie))
    application.add_handler(CommandHandler("movies", movies))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.run_polling()


if __name__ == "__main__":
    run_bot()
