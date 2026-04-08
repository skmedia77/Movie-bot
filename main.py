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

# ---------------- WEB SERVER (For Render Port Binding) ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Perfectly on Render!"

def run_flask():
    # Render-এর পোর্ট বাইন্ডিং ঠিক রাখতে এটি জরুরি
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7396254196
CHANNEL_USERNAME = "@skkmediabd"
# এনভায়রনমেন্টে WEB_APP_URL বা APP_URL যা-ই থাকুক তা খুঁজে নেবে
APP_URL = os.environ.get("WEB_APP_URL") or os.environ.get("APP_URL")
MOVIE_APP_URL = "https://skmedia77.github.io/Movie-bot/"
FIREBASE_DB_URL = "https://skmedia-146ca-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_CREDS = os.environ.get("FIREBASE_CREDENTIALS")

REFERRAL_COUNT_NEEDED = 1 

# ---------------- FIREBASE SETUP ----------------
user_ref = None
movie_ref = None

if not firebase_admin._apps:
    try:
        # JSON কি যদি মাল্টি-লাইন থাকে তবে সেটি ক্লিন করে এক লাইনে করার চেষ্টা করবে
        clean_creds = FIREBASE_CREDS.replace('\n', '').strip()
        cred_dict = json.loads(clean_creds)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
        user_ref = db.reference('users')
        movie_ref = db.reference('movies')
        print("✅ Firebase Initialized Successfully!")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")

# ---------------- HELPERS ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def progress_bar(count, total=REFERRAL_COUNT_NEEDED):
    filled = "█" * min(count, total)
    empty = "░" * max(0, total - count)
    percent = int((min(count, total) / total) * 100)
    return f"[{filled}{empty}] {percent}%"

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_ref:
        try:
            if not user_ref.child(user_id).get():
                ref_by = context.args[0] if context.args else None
                user_ref.child(user_id).set({"referrals": 0, "coins": 0, "ref_by": ref_by})
                if ref_by and ref_by != user_id:
                    r = user_ref.child(ref_by).get() or {"referrals": 0, "coins": 0}
                    user_ref.child(ref_by).update({
                        "referrals": r.get("referrals", 0) + 1,
                        "coins": r.get("coins", 0) + 100
                    })
        except: pass

    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined", callback_data="check_join")]]
        await update.message.reply_text("❌ মুভি দেখতে হলে আগে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb = [[InlineKeyboardButton("🎬 Open Movie App", callback_data="open_app")]]
        await update.message.reply_text("🎬 Viral Movie Hub এ স্বাগতম!", reply_markup=InlineKeyboardMarkup(kb))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    refs = 0
    if user_ref:
        user = user_ref.child(user_id).get() or {"referrals": 0}
        refs = user.get("referrals", 0)
    
    bot_me = await context.bot.get_me()
    text = f"📊 **আপনার স্ট্যাটাস**\n\n👥 মোট রেফার: {refs}/{REFERRAL_COUNT_NEEDED}\n📈 অগ্রগতি: {progress_bar(refs)}\n\n🔗 লিংক: `https://t.me/{bot_me.username}?start={user_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    
    if query.data == "check_join":
        if await is_subscribed(context.bot, user_id):
            await query.edit_message_text("✅ ধন্যবাদ! এখন মুভি অ্যাপ ওপেন করতে পারবেন।", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Open App", callback_data="open_app")]]))
        else:
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)
            
    elif query.data == "open_app":
        refs = 0
        if user_ref:
            user = user_ref.child(user_id).get() or {}
            refs = user.get("referrals", 0)
        
        if refs < REFERRAL_COUNT_NEEDED:
            await query.edit_message_text(f"🔒 {REFERRAL_COUNT_NEEDED} জন রেফার লাগবে। আপনার আছে: {refs}/{REFERRAL_COUNT_NEEDED}\n{progress_bar(refs)}", parse_mode=ParseMode.MARKDOWN)
        else:
            kb = [[InlineKeyboardButton("🚀 Launch Mini App", web_app=WebAppInfo(url=APP_URL))]]
            await query.edit_message_text("✅ রেফার পূর্ণ হয়েছে! নিচের বাটনে ক্লিক করুন:", reply_markup=InlineKeyboardMarkup(kb))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ মেসেজের ওপর রিপ্লাই দিয়ে /broadcast লিখুন।")
        return

    reply_msg = update.message.reply_to_message
    all_users = user_ref.get() if user_ref else {}
    total_users = len(all_users)
    status_msg = await update.message.reply_text(f"⏳ ব্রডকাস্ট শুরু...")
    
    success, removed = 0, 0
    for uid in all_users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)
            success += 1
            await asyncio.sleep(0.05)
        except:
            if user_ref: user_ref.child(str(uid)).delete()
            removed += 1
            
    await status_msg.edit_text(f"✅ সম্পন্ন!\n🚀 সফল: {success}\n🗑 ডিলিট: {removed}")

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data = [i.strip() for i in " ".join(context.args).split("|")]
    if len(data) < 3:
        await update.message.reply_text("❌ ফরম্যাট: /post নাম | ইমেজ URL | মুভি লিঙ্ক")
        return

    movie_name, image_url, movie_link = data[0], data[1], data[2]
    if movie_ref: movie_ref.push({"title": movie_name, "image_url": image_url, "video_url": movie_link})
    
    bot_me = await context.bot.get_me()
    kb = [[InlineKeyboardButton("🎬 Watch Movie", url=f"https://t.me/{bot_me.username}")]]
    await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo=image_url, caption=f"🎬 **{movie_name}**\n\nমুভিটি দেখতে নিচের বাটনে ক্লিক করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text("✅ পোস্ট সফল!")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    u = len(user_ref.get() or {}) if user_ref else 0
    m = len(movie_ref.get() or {}) if movie_ref else 0
    await update.message.reply_text(f"📊 **রিপোর্ট**\n👤 মোট ইউজার: {u}\n🎬 মোট মুভি: {m}")

async def post_init(application):
    try:
        await application.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="ভিডিও দেখুন", web_app=WebAppInfo(url=MOVIE_APP_URL)))
    except: pass

# ---------------- RUN BOT (Render Fixed) ----------------
if __name__ == "__main__":
    # ১. Flask সার্ভার ব্যাকগ্রাউন্ডে চালু করা
    threading.Thread(target=run_flask, daemon=True).start()
    
    # ২. টেলিগ্রাম অ্যাপ্লিকেশন তৈরি
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    # ৩. সব হ্যান্ডলার রেজিস্টার করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("post", post))
    application.add_handler(CommandHandler("users", admin_stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Bot is starting and polling...")
    # ৪. পোলিং চালু (Render-এ এটিই সঠিক পদ্ধতি)
    application.run_polling(drop_pending_updates=True)
