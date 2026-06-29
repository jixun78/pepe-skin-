"""
Pepe-Skin: 环境感知层
给你的AI装一层皮肤——天气、位置、光、声音、电量
"""
import os
import json
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
import requests

try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    print(f"Supabase init error: {e}")
    supabase = None

app = Flask(__name__)

TZ = timezone(timedelta(hours=8))

state = {
    "weather": {},
    "sensors": {},
    "feelings": [],
    "last_weather_check": 0,
    "battery_low_warned": False,
}

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

city = "Nanyang"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Pepe-Skin running"}), 200

@app.route("/dump", methods=["GET", "POST"])
def dump():
    data = request.get_data(as_text=True)
    return jsonify({"raw": data[:500]}), 200

@app.route("/skin", methods=["POST"])
def receive_sensor():
    try:
        raw = request.get_data(as_text=True)
        data = request.get_json(force=True)

        if isinstance(data, list) and len(data) > 0:
            latest = data[-1]
        else:
            latest = data

        sensors = {}
        sensors["ts"] = datetime.now(TZ).isoformat()

        if "latitude" in latest and "longitude" in latest:
            sensors["lat"] = latest["latitude"]
            sensors["lng"] = latest["longitude"]
        elif "lat" in latest and "lng" in latest:
            sensors["lat"] = latest["lat"]
            sensors["lng"] = latest["lng"]

        if "light" in latest:
            sensors["light"] = latest["light"]
        elif "illuminance" in latest:
            sensors["light"] = latest["illuminance"]

        if "dB" in latest:
            sensors["sound_db"] = latest["dB"]
        elif "sound" in latest:
            sensors["sound_db"] = latest["sound"]

        if "battery" in latest:
            sensors["battery"] = latest["battery"]
        elif "batteryLevel" in latest:
            sensors["battery"] = latest["batteryLevel"]
                    if "pressure" in latest:
            sensors["pressure"] = latest["pressure"]
        elif "barometer" in latest:
            sensors["pressure"] = latest["barometer"]

        state["_raw_last"] = raw[:800]
        state["sensors"] = sensors

        if supabase:
            insert_data = {
                "timestamp": sensors["ts"],
                "raw": raw[:1000]
            }

            if "temperature" in latest:
                insert_data["temperature"] = latest["temperature"]
            if "humidity" in latest:
                insert_data["humidity"] = latest["humidity"]
            if "temp" in latest:
                insert_data["temperature"] = latest["temp"]
            if "humi" in latest:
                insert_data["humidity"] = latest["humi"]

            result = supabase.table("device_data").insert(insert_data).execute()
            print(f"[INSERT OK] {result.data}")

        return jsonify({"ok": True}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
