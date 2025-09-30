from flask import Flask, request, jsonify
from datetime import datetime
import os
import pytz
from flask_cors import CORS
from supabase import create_client, Client

# --- Supabase setup (use env vars on Railway) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://dieappiptenklzrihyud.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRpZWFwcGlwdGVua2x6cmloeXVkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDUwNTExOCwiZXhwIjoyMDY2MDgxMTE4fQ.89d1zJbt2PSk9xR9F009C5chlwXxfpf6IScDbReK0nU")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Flask setup ---
app = Flask(__name__)
CORS(app)  # allow Firebase/any origin to hit this API

CATS = ["Bu3teqa", "Salbokh", "Cruella"]
TZ = pytz.timezone("Asia/Kuwait")

def now_kw():
    return datetime.now(TZ)

def today_str():
    return now_kw().strftime("%Y-%m-%d")

@app.route("/")
def root():
    return {"status": "ok", "message": "Backend is running"}, 200

# Create a new log row (append, don't overwrite)
@app.route("/log", methods=["POST"])
def log_action():
    data = request.get_json(force=True)
    cat = data.get("cat")
    action = data.get("action")
    value = data.get("value")

    if cat not in CATS or action not in ("meal", "treat"):
        return jsonify({"error": "bad payload"}), 400

    ts = now_kw().strftime("%I:%M %p")
    entry = f"{action}: {value} ({ts})"

    # ✅ properly indented
    supabase.table("logs").upsert({
        "date": today_str(),
        "cat": cat,
        "log": entry
    }).execute()

    return jsonify({"status": "ok", "cat": cat, "log": entry})

def add_log(cat, action, value):
    today = get_today()
    current_time = datetime.now(pytz.timezone("Asia/Kuwait")).strftime("%I:%M %p")

    log_entry = f"{action}: {value} ({current_time})"

    response = supabase.table("logs").upsert({
        "date": today,
        "cat": cat,
        "log": log_entry
    }).execute()
    return response


# Return all logs for today merged per cat (for page refresh)
@app.route("/logs_today", methods=["GET"])
def logs_today():
    r = supabase.table("logs").select("*").eq("date", today_str()).order("created_at", desc=False).execute()
    merged = {cat: "" for cat in CATS}
    for row in r.data or []:
        c = row.get("cat")
        if c in merged:
            merged[c] = (merged[c] + "\n" if merged[c] else "") + (row.get("log") or "")
    return jsonify({"date": today_str(), "data": merged})

# Edit the *latest* log for a cat; if none exists, create one
@app.route("/edit_time", methods=["POST"])
def edit_time():
    data = request.get_json(force=True)
    cat = data.get("cat")
    new_log = data.get("new_log", "").strip()
    if cat not in CATS or not new_log:
        return "", 400

    # find latest row for this cat today
    r = supabase.table("logs").select("id,created_at").eq("date", today_str()).eq("cat", cat)\
        .order("created_at", desc=True).limit(1).execute()

    if r.data:
        latest_id = r.data[0]["id"]
        supabase.table("logs").update({"log": new_log}).eq("id", latest_id).execute()
    else:
      supabase.table("logs").upsert({
    "date": today_str(),
    "cat": cat,
    "log": entry
}).execute()


    return "", 204

# Download (plain text)
@app.route("/download")
def download_logs():
    r = supabase.table("logs").select("*").eq("date", today_str()).order("created_at", desc=False).execute()
    out = [f"🐾 Feeding Log - {today_str()}", ""]
    for row in r.data or []:
        out.append(f"{row['cat']}: {row['log']}")
    body = "\n".join(out)
    return body, 200, {
        "Content-Type": "text/plain",
        "Content-Disposition": f'attachment; filename="cat_log_{today_str()}.txt"'
    }

# Notifications: store device tokens
@app.route("/register_token", methods=["POST"])
def register_token():
    token = (request.get_json(force=True) or {}).get("token")
    if not token:
        return jsonify({"error": "no token"}), 400
    supabase.table("tokens").upsert({"token": token}).execute()
    return jsonify({"status": "ok"})

# Global mute toggle
@app.route("/toggle_global_mute", methods=["POST"])
def toggle_global_mute():
    res = supabase.table("settings").select("muted").eq("id", 1).execute()
    current = res.data[0]["muted"] if res.data else False
    new_state = not current
    supabase.table("settings").upsert({"id": 1, "muted": new_state}).execute()
    return jsonify({"muted": new_state})

@app.route("/get_global_mute", methods=["GET"])
def get_global_mute():
    res = supabase.table("settings").select("muted").eq("id", 1).execute()
    return jsonify({"muted": res.data[0]["muted"] if res.data else False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
