import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from commands import (
    start,
    gorev,
    kilo,
    su,
    durum,
    admin,
    grafik,
    foto,
    button_click,
    chat
)

import scheduler_system

TOKEN = os.environ["TOKEN"]

app = ApplicationBuilder().token(TOKEN).build()

# Komutlar
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gorev", gorev))
app.add_handler(CommandHandler("kilo", kilo))
app.add_handler(CommandHandler("su", su))
app.add_handler(CommandHandler("durum", durum))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("grafik", grafik))
app.add_handler(CommandHandler("foto", foto))

# Buton sistemi
app.add_handler(
    CallbackQueryHandler(button_click)
)

# Fotoğraf sistemi
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        foto
    )
)

# AI sohbet sistemi
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

print("Bot aktif.")

app.run_polling()