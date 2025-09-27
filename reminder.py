from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests

SUPABASE_URL = "..."
SUPABASE_KEY = "..."
FCM_SERVER_KEY = "YOUR_FIREBASE_SERVER_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_push(token, title, body):
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": token,
        "notification": {"title": title, "body": body}
    }
    requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, json=payload)

def check_and_notify():
    kuwait = pytz.timezone("Asia/Kuwait")
    now = datetime.now(kuwait)

    # 1. Check if global mute is on
    mute_check = supabase.table("settings").select("muted").eq("id", 1).execute()
    if mute_check.data and mute_check.data[0]["muted"]:
        print("🔕 Notifications muted, skipping send.")
        return

    # 2. Get logs + tokens
    logs = supabase.table("logs").select("*").execute().data
    tokens = supabase.table("tokens").select("*").execute().data

    for log in logs:
        last_time = datetime.strptime(log["log_time"], "%Y-%m-%d %H:%M:%S")  # adjust schema
        if now - last_time > timedelta(hours=4):
            msg = f"{log['cat']} ate 4 hours ago, he might be hungry now."
            for t in tokens:
                send_push(t["token"], "Cat Feeding Reminder 🐾", msg)

if __name__ == "__main__":
    check_and_notify()

