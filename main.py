import os
import json

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = os.environ["TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

CHAT_ID = None

SYSTEM_PROMPT = """
Sen sert disiplinli fitness ve yaşam koçusun.

Kısa, net, motive edici konuş.
Bahane kabul etme.
"""

def load_users():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID

    CHAT_ID = update.effective_chat.id

    users = load_users()

    user_id = str(update.effective_user.id)

    if user_id not in users:
        users[user_id] = {
            "name": update.effective_user.first_name,
            "messages": 0,
            "streak": 0,
            "completed_today": False
        }

        save_users(users)

    await update.message.reply_text(
        "AI Koç aktif.\nDisiplin sistemi başlatıldı."
    )

async def gorev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = """
BUGÜNÜN GÖREVLERİ

✅ 3 litre su
✅ Antrenman
✅ Şeker yok
✅ 10 dk yürüyüş
✅ Erken uyku

Bitince:
tamamladım
yaz.
"""

    await update.message.reply_text(mesaj)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        users = load_users()

        user_id = str(update.effective_user.id)

        if user_id not in users:
            users[user_id] = {
                "name": update.effective_user.first_name,
                "messages": 0,
                "streak": 0,
                "completed_today": False
            }

        message_text = update.message.text.lower()

        if "tamamladım" in message_text:

            if users[user_id]["completed_today"]:
                await update.message.reply_text(
                    "Bugünkü görev zaten tamamlandı."
                )
                return

            users[user_id]["completed_today"] = True
            users[user_id]["streak"] += 1

            save_users(users)

            await update.message.reply_text(
                f"""
🔥 Görev tamamlandı.

Streak:
{users[user_id]['streak']} gün

Disiplini bozma.
"""
            )
            return

        users[user_id]["messages"] += 1

        save_users(users)

        memory_text = f"""
Kullanıcı adı: {users[user_id]['name']}
Toplam mesaj: {users[user_id]['messages']}
Streak: {users[user_id]['streak']}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "system",
                    "content": memory_text
                },
                {
                    "role": "user",
                    "content": update.message.text
                },
            ],
            max_tokens=300,
        )

        cevap = response.choices[0].message.content

        await update.message.reply_text(cevap)

    except Exception as e:
        print("HATA:", e)
        await update.message.reply_text(f"Hata oluştu:\n{e}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gorev", gorev))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

scheduler = BackgroundScheduler()

scheduler.start()

print("Bot aktif...")

app.run_polling()