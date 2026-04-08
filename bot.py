import os
import json
import datetime
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

# লগার সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Health Check Server (Render Error Fix) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_health_check():
    # রেন্ডার অটোমেটিক একটি PORT এনভায়রনমেন্ট ভেরিয়েবল দেয়
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health check server started on port {port}")
    server.serve_forever()

# --- Environment Variables ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEB_APP_URL = os.getenv("WEB_APP_URL")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY")

# Firebase Initialisation
try:
    key_dict = json.loads(FIREBASE_KEY_JSON)
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    logging.error(f"Firebase Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.collection("users").document(str(user.id)).set({
        "name": user.first_name,
        "username": user.username,
        "date": datetime.datetime.now()
    }, merge=True)

    keyboard = [
        [InlineKeyboardButton("🎬 ওপেন মুভি অ্যাপ", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("📢 জয়েন চ্যানেল", url="https://t.me/skkmediabd")]
    ]
    await update.message.reply_text(
        f"স্বাগতম {user.first_name}!\n\nআমাদের মিনি অ্যাপে আপনি সব লেটেস্ট মুভি, নাটক এবং মিউজিক পাবেন। মুভি আনলক করতে অ্যাপটি ওপেন করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        data = " ".join(context.args).split("|")
        title = data[0].strip()
        category = data[1].strip()
        link = data[2].strip()
        image = data[3].strip() if len(data) > 3 else ""

        db.collection("movies").add({
            "title": title,
            "category": category,
            "link": link,
            "image": image,
            "timestamp": datetime.datetime.now()
        })
        await update.message.reply_text(f"✅ সফলভাবে সেভ হয়েছে:\n📌 নাম: {title}")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট!\nলিখুন: /post নাম | ক্যাটাগরি | লিঙ্ক | ইমেজ লিঙ্ক")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    users = db.collection("users").get()
    await update.message.reply_text(f"📊 বর্তমান ইউজার: {len(users)} জন।")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("মেসেজ দিন।")
        return
    
    users = db.collection("users").get()
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=int(u.id), text=text)
            sent += 1
        except: pass
    await update.message.reply_text(f"📢 {sent} জনের কাছে পাঠানো হয়েছে।")

def main():
    # ১. প্রথমে হেলথ চেক সার্ভারটি একটি আলাদা থ্রেডে চালু করি
    threading.Thread(target=run_health_check, daemon=True).start()

    # ২. বোট অ্যাপ্লিকেশন সেটআপ
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logging.info("বটটি এখন সচল...")
    app.run_polling()

if __name__ == "__main__":
    main()        
