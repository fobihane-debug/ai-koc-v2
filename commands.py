import os
import base64
import matplotlib.pyplot as plt

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from database import (
    create_user,
    get_user,
    cursor,
    conn
)

from ai_system import (
    ask_ai,
    ask_food_ai,
    ask_voice_ai
)

ADMIN_ID = "7653341950"

CHAT_ID = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global CHAT_ID

    CHAT_ID = update.effective_chat.id

    user_id = str(update.effective_user.id)

    create_user(
        user_id,
        update.effective_user.first_name
    )

    await update.message.reply_text(
        "AI Koç aktif."
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        weight REAL
    )
    """)

    cursor.execute("""
    INSERT INTO weight_history (user_id, weight)
    VALUES (?, ?)
    """, (
        user_id,
        kg
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

    if not user:

        create_user(
            user_id,
            update.effective_user.first_name
        )

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

        create_user(
            user_id,
            update.effective_user.first_name
        )

        user = get_user(user_id)

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

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT COUNT(*) FROM users
    """)

    total_users = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(messages) FROM users
    """)

    total_messages = cursor.fetchone()[0]

    await update.message.reply_text(
        f"""
📊 ADMIN PANEL

👥 Kullanıcı:
{total_users}

💬 Toplam mesaj:
{total_messages}
"""
    )

async def grafik(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    cursor.execute("""
    SELECT weight FROM weight_history
    WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()

    if not rows:

        await update.message.reply_text(
            "Kilo verisi yok."
        )

        return

    kilos = [row[0] for row in rows]

    plt.figure(figsize=(6,4))

    plt.plot(kilos, marker="o")

    plt.title("Kilo Değişimi")
    plt.xlabel("Kayıt")
    plt.ylabel("Kg")

    grafik_path = "grafik.png"

    plt.savefig(grafik_path)

    plt.close()

    await update.message.reply_photo(
        photo=open(grafik_path, "rb")
    )

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        photo = update.message.photo[-1]

        file = await context.bot.get_file(photo.file_id)

        image_bytes = await file.download_as_bytearray()

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        response = ask_food_ai(image_base64)

        await update.message.reply_text(response)

    except Exception as e:

        print("FOTO HATA:", e)

        await update.message.reply_text(
            f"Hata oluştu:\n{e}"
        )

async def voice_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        voice = update.message.voice

        file = await context.bot.get_file(
            voice.file_id
        )

        ogg_path = "voice.ogg"

        await file.download_to_drive(ogg_path)

        with open(ogg_path, "rb") as audio_file:

            transcript = ask_voice_ai(audio_file)

        await update.message.reply_text(
            f"🎤 Sen:\n{transcript}"
        )

        user_id = str(update.effective_user.id)

        user = get_user(user_id)

        if not user:

            create_user(
                user_id,
                update.effective_user.first_name
            )

            user = get_user(user_id)

        cevap = await ask_ai(
            user,
            transcript
        )

        await update.message.reply_text(
            f"🤖 AI Koç:\n{cevap}"
        )

    except Exception as e:

        print("VOICE HATA:", e)

        await update.message.reply_text(
            f"Hata oluştu:\n{e}"
        )

async def liderlik(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("""
    SELECT name, streak
    FROM users
    ORDER BY streak DESC
    LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:

        await update.message.reply_text(
            "Liderlik verisi yok."
        )

        return

    text = "🏆 LİDERLİK TABLOSU\n\n"

    for index, row in enumerate(rows, start=1):

        text += (
            f"{index}. {row[0]} - "
            f"{row[1]} gün streak\n"
        )

    await update.message.reply_text(text)

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

        cevap = await ask_ai(
            user,
            update.message.text
        )

        await update.message.reply_text(cevap)

    except Exception as e:

        print("HATA:", e)

        await update.message.reply_text(
            f"Hata oluştu:\n{e}"
        )