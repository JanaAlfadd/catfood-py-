from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
import pytz
from flask_cors import CORS
from supabase import create_client, Client

# --- Supabase setup ---
SUPABASE_URL = "https://dieappiptenklzrihyud.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRpZWFwcGlwdGVua2x6cmloeXVkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA1MDUxMTgsImV4cCI6MjA2NjA4MTExOH0._6YNeKIaze4sDJuDE3oWgMOgjD9xvz6lFwjkgTn7UVY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Flask setup ---
app = Flask(__name__)
CORS(app)   # <-- allow Firebase frontend to talk to Render backend

CATS = ["Bu3teqa", "Salbokh", "Cruella"]

# --- Helpers ---
def get_today():
    return datetime.now(pytz.timezone("Asia/Kuwait")).strftime("%Y-%m-%d")

def get_logs_for_today():
    today = get_today()
    result = supabase.table("logs").select("*").eq("date", today).execute()

    logs = {cat: {"log": ""} for cat in CATS}
    for row in result.data:
        logs[row["cat"]]["log"] += row["log"] + "\n"
    return logs


def add_log(cat, action, value):
    today = get_today()
    current_time = datetime.now(pytz.timezone("Asia/Kuwait")).strftime("%I:%M %p")

    log_entry = f"{action}: {value} ({current_time})"

    response = supabase.table("logs").insert({
        "date": today,
        "cat": cat,
        "log": log_entry
    }).execute()
    return response

@app.route("/log", methods=["POST"])
def log_action():
    data = request.get_json()
    cat = data["cat"]
    action = data["action"]
    value = data["value"]

    add_log(cat, action, value)
    return {"status": "ok"}


@app.route("/")
def root():
    return {"status": "ok", "message": "Backend is running"}


@app.route("/edit_time", methods=["POST"])
def edit_time():
    data = request.get_json()
    cat = data["cat"]
    new_log = data["new_log"]
    today = get_today()

    supabase.table("logs").upsert({
        "date": today,
        "cat": cat,
        "log": new_log
    }).execute()

    return ("", 204)

@app.route("/download")
def download_logs():
    today = get_today()
    result = supabase.table("logs").select("*").eq("date", today).execute()
    
    output = f"🐾 Feeding Log - {today}\n\n"
    for row in result.data:
        output += f"{row['cat']}: {row['log']}\n"

    return output, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': f'attachment; filename="cat_log_{today}.txt"'
    }

@app.route("/register_token", methods=["POST"])
def register_token():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "no token"}), 400

    # Save token in Supabase (tokens table)
    supabase.table("tokens").upsert({"token": token}).execute()

    return jsonify({"status": "ok"})

@app.route("/toggle_global_mute", methods=["POST"])
def toggle_global_mute():
    # We'll use a single-row "settings" table in Supabase for this
    result = supabase.table("settings").select("muted").eq("id", 1).execute()

    current_muted = False
    if result.data:
        current_muted = result.data[0]["muted"]

    new_muted = not current_muted

    supabase.table("settings").upsert({
        "id": 1,   # single row only
        "muted": new_muted
    }).execute()

    return jsonify({"muted": new_muted})
@app.route("/get_global_mute", methods=["GET"])
def get_global_mute():
    result = supabase.table("settings").select("muted").eq("id", 1).execute()
    muted = False
    if result.data:
        muted = result.data[0]["muted"]
    return jsonify({"muted": muted})

# --- Run app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
