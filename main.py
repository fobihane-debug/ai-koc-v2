import os
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = os.environ["TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

CHAT_ID = None

SYSTEM_PROMPT = """
Sen sert disiplinli fitness ve yaşam koçusun.

Kısa, net, motive edici konuş.
Bahane kabul etme.
"""

conn = sqlite3.connect(
    "fitness.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    messages INTEGER,
    streak INTEGER,
    completed_today INTEGER,
    weight REAL,
    water INTEGER
)
""")

conn.commit()

def create_user(user_id, name):

    cursor.execute("""
    INSERT OR IGNORE INTO users
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        0,
        0,
        0,
        0,
        0
    ))

    conn.commit()

def get_user(user_id):

    cursor.execute("""
    SELECT * FROM users
    WHERE user_id = ?
    """, (user_id,))

    return cursor.fetchone()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global CHAT_ID

    CHAT_ID = update.effective_chat.id

    user_id = str(update.effective_user.id)

    create_user(
        user_id,
        update.effective_user.first_name
    )

    await update.message.reply_text(
        "AI Koç aktif.\nSQLite sistemi aktif."
    )

async def gorev(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Görevi Tamamladım",
                callback_data="complete_task"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    mesaj = """
BUGÜNÜN GÖREVLERİ

✅ 3 litre su
✅ Antrenman
✅ Şeker yok
✅ 10 dk yürüyüş
✅ Erken uyku
"""

    await update.message.reply_text(
        mesaj,
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = str(query.from_user.id)

    user = get_user(user_id)

    if not user:
        return

    completed_today = user[4]
    streak = user[3]

    if completed_today:

        await query.message.reply_text(
            "Bugünkü görev zaten tamamlandı."
        )

        return

    streak += 1

    cursor.execute("""
    UPDATE users
    SET completed_today = 1,
        streak = ?
    WHERE user_id = ?
    """, (
        streak,
        user_id
    ))

    conn.commit()

    await query.message.reply_text(
        f"""
🔥 Görev tamamlandı.

🔥 Streak:
{streak} gün

Disiplini bozma.
"""
    )

async def kilo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    try:
        kg = float(context.args[0])

    except:
        await update.message.reply_text(
            "Kullanım:\n/kilo 82"
        )
        return

    cursor.execute("""
    UPDATE users
    SET weight = ?
    WHERE user_id = ?
    """, (
        kg,
        user_id
    ))

    conn.commit()

    await update.message.reply_text(
        f"""
⚖️ Kilo kaydedildi.

Yeni kilo:
{kg} kg
"""
    )

async def su(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    user = get_user(user_id)

    water = user[6] + 1

    cursor.execute("""
    UPDATE users
    SET water = ?
    WHERE user_id = ?
    """, (
        water,
        user_id
    ))

    conn.commit()

    await update.message.reply_text(
        f"""
💧 Su kaydedildi.

Bugünkü su:
{water} bardak
"""
    )

async def durum(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    user = get_user(user_id)

    if not user:
        return

    await update.message.reply_text(
        f"""
📊 DURUM

👤 İsim:
{user[1]}

🔥 Streak:
{user[3]} gün

💬 Mesaj:
{user[2]}

⚖️ Kilo:
{user[5]} kg

💧 Su:
{user[6]} bardak
"""
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user_id = str(update.effective_user.id)

        user = get_user(user_id)

        if not user:

            create_user(
                user_id,
                update.effective_user.first_name
            )

            user = get_user(user_id)

        messages = user[2] + 1

        cursor.execute("""
        UPDATE users
        SET messages = ?
        WHERE user_id = ?
        """, (
            messages,
            user_id
        ))

        conn.commit()

        memory_text = f"""
Kullanıcı adı: {user[1]}
Toplam mesaj: {messages}
Streak: {user[3]}
Kilo: {user[5]}
Su: {user[6]}
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

        await update.message.reply_text(
            f"Hata oluştu:\n{e}"
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gorev", gorev))
app.add_handler(CommandHandler("kilo", kilo))
app.add_handler(CommandHandler("durum", durum))
app.add_handler(CommandHandler("su", su))

app.add_handler(CallbackQueryHandler(button_click))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

scheduler = BackgroundScheduler()

def reset_daily_tasks():

    cursor.execute("""
    UPDATE users
    SET completed_today = 0,
        water = 0
    """)

    conn.commit()

    print("Günlük görevler sıfırlandı.")

scheduler.add_job(
    reset_daily_tasks,
    "cron",
    hour=0,
    minute=0
)

scheduler.start()

print("Bot aktif...")

app.run_polling()