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

TOKEN = os.environ["TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

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
    users = load_users()

    user_id = str(update.effective_user.id)

    if user_id not in users:
        users[user_id] = {
            "name": update.effective_user.first_name,
            "messages": 0
        }

        save_users(users)

    await update.message.reply_text(
        "AI Koç aktif.\nHedefini yaz."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        users = load_users()

        user_id = str(update.effective_user.id)

        if user_id not in users:
            users[user_id] = {
                "name": update.effective_user.first_name,
                "messages": 0
            }

        users[user_id]["messages"] += 1

        save_users(users)

        user_message = update.message.text

        memory_text = f"""
Kullanıcı adı: {users[user_id]['name']}
Toplam mesaj: {users[user_id]['messages']}
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
                    "content": user_message
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("Bot aktif...")

app.run_polling()