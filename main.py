import os
import requests
import hashlib
import time
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

CHECK_INTERVAL = 600
LAST_HASH_FILE = "last_hash.txt"

KYIV_TZ = pytz.timezone("Europe/Kyiv")


def get_schedule_text():
    url = "https://api.yasno.com.ua/api/v1/schedules?city=kyiv"
    r = requests.get(url, timeout=15)
    data = r.json()

    lines = []

    for g in data.get("groups", []):
        name = g.get("name")
        periods = g.get("periods", [])
        times = ", ".join([f"{p['from']}–{p['to']}" for p in periods])
        lines.append(f"Група {name}: {times}")

    return "\n".join(lines)


def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def load_last_hash():
    if not os.path.exists(LAST_HASH_FILE):
        return None
    with open(LAST_HASH_FILE, "r") as f:
        return f.read().strip()


def save_last_hash(h):
    with open(LAST_HASH_FILE, "w") as f:
        f.write(h)


def send_to_telegram(text):
    now = datetime.now(KYIV_TZ).strftime("%d.%m.%Y %H:%M")

    message = (
        "⚡ <b>Графік відключень Київ</b>\n\n"
        f"{text}\n\n"
        f"🕒 Оновлено: {now}"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "🔎 Яка в мене група?", "url": 
"https://t.me/vmykachsvitlo_bot"}
        ]]
    }

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        },
        timeout=10,
    )


def main():
    while True:
        try:
            text = get_schedule_text()
            new_hash = get_hash(text)
            old_hash = load_last_hash()

            if new_hash != old_hash:
                send_to_telegram(text)
                save_last_hash(new_hash)
                print("UPDATED")
            else:
                print("NO CHANGES")

        except Exception as e:
            print("ERROR:", e)

        time.sleep(CHECK_INTERVAL)


if name == "__main__":
    main()
