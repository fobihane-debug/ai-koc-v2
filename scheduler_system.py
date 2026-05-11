from apscheduler.schedulers.background import BackgroundScheduler
from database import cursor, conn

scheduler = BackgroundScheduler()

def reset_daily_tasks():

    cursor.execute("""
    UPDATE users
    SET completed_today = 0,
        water = 0
    """)

    conn.commit()

    print("Görevler sıfırlandı.")

scheduler.add_job(
    reset_daily_tasks,
    "cron",
    hour=0,
    minute=0
)

scheduler.start()