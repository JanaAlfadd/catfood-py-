from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
import pytz
from supabase import create_client, Client

SUPABASE_URL = "https://dieappiptenklzrihyud.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRpZWFwcGlwdGVua2x6cmloeXVkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA1MDUxMTgsImV4cCI6MjA2NjA4MTExOH0._6YNeKIaze4sDJuDE3oWgMOgjD9xvz6lFwjkgTn7UVY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CATS = ["Bu3teqa", "Salbokh", "Cruella"]

def get_today():
    return datetime.now(pytz.timezone("Asia/Kuwait")).strftime("%Y-%m-%d")

def get_logs_for_today():
    today = get_today()
    result = supabase.table("logs").select("*").eq("date", today).execute()
    logs = {cat: {"log": ""} for cat in CATS}
    for row in result.data:
        logs[row["cat"]] = {"log": row["log"]}
    return logs

def upsert_log(cat, log):
    today = get_today()
    response = supabase.table("logs").upsert({
        "date": today,
        "cat": cat,
        "log": log
    }).execute()
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cat = request.form["cat"]
        action = request.form["action"]
        value = request.form["value"]
        meal_type = request.form.get("type", "")
        current_time = datetime.now(pytz.timezone("Asia/Kuwait")).strftime("%I:%M %p")

        icons = {"raw": "🥩", "wet": "💧", "dry": "🍪"}
        food_icon = icons.get(meal_type, "")
        if action == "treat":
            log_entry = f"treat: {value} ({current_time})"
        elif action == "meal":
            log_entry = f"meal: {value} {food_icon} ({current_time})"
        else:
            log_entry = f"{action}: {current_time}"

        upsert_log(cat, log_entry)
        return redirect("/")

    logs = get_logs_for_today()
    return render_template("index.html", cats=CATS, today=get_today(), data=logs)

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
    
    output = f"🐾 Feeding Log - {today}\\n\\n"
    for row in result.data:
        output += f"{row['cat']}: {row['log']}\\n"

    return output, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': f'attachment; filename=\"cat_log_{today}.txt\"'
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

