import os
import json
import threading
import asyncio
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update, 
    WebAppInfo, 
    MenuButtonWebApp 
)
from telegram.constants import ParseMode 
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- WEB SERVER (For Render) ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7396254196
CHANNEL_USERNAME = "@skkmediabd"
# আপনার এনভায়রনমেন্টে যদি WEB_APP_URL থাকে তবে সেটি এখানে দিন
APP_URL = os.environ.get("WEB_APP_URL") or os.environ.get("APP_URL")
MOVIE_APP_URL = "https://skmedia77.github.io/Movie-bot/"
FIREBASE_DB_URL = "https://skmedia-146ca-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_CREDS = os.environ.get("FIREBASE_CREDENTIALS")

REFERRAL_COUNT_NEEDED = 1 

# ---------------- FIREBASE SETUP (Fixed) ----------------
user_ref = None
movie_ref = None

if not firebase_admin._apps:
    try:
        # JSON কি-কে এক লাইনে পড়ার জন্য রিপ্রেস করা হলো
        clean_creds = FIREBASE_CREDS.replace('\n', '').strip()
        cred_dict = json.loads(clean_creds)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
        user_ref = db.reference('users')
        movie_ref = db.reference('movies')
        print("✅ Firebase Connected!")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")
        # যদি ফায়ারবেজ ফেইল করে তবুও যাতে বট না থামে
        user_ref = None

# ---------------- HELPERS ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # ডাটাবেস চেক (যদি কানেক্টেড থাকে)
    if user_ref:
        try:
            if not user_ref.child(user_id).get():
                ref_by = context.args[0] if context.args else None
                user_ref.child(user_id).set({"referrals": 0, "coins": 0, "ref_by": ref_by})
        except:
            pass
    
    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined", callback_data="check_join")]]
        await update.message.reply_text("❌ মুভি দেখতে আগে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb = [[InlineKeyboardButton("🎬 Open Movie App", callback_data="open_app")]]
        await update.message.reply_text("🎬 Viral Movie Hub এ স্বাগতম!", reply_markup=InlineKeyboardMarkup(kb))

# (বাকি হ্যান্ডলারগুলো যেমন status, broadcast ইত্যাদি আপনার কোড থেকে এখানে থাকবে)
# ... [এখানে আপনার আগের কোডের অন্য ফাংশনগুলো বসান] ...

async def post_init(application):
    try:
        await application.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="ভিডিও দেখুন", web_app=WebAppInfo(url=MOVIE_APP_URL)))
    except: pass

# ---------------- RUN BOT (Render Optimized) ----------------
if __name__ == "__main__":
    # Flask থ্রেড চালু করা
    threading.Thread(target=run_flask, daemon=True).start()
    
    # টেলিগ্রাম অ্যাপ্লিকেশন
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", start))
    # অন্য হ্যান্ডলারগুলো এখানে যোগ করুন...
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True) 
