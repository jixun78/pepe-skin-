"""
Pepe-Skin: 环境感知层
给你的AI装一层皮肤——天气、位置、光、声音、电量
"""
import os
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
import requests

try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except:
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

city = "Nanyang"

@app.route("/dump", methods=["GET","POST"])
def dump():
    data = request.get_data(as_text=True)
    return jsonify({"raw": data[:500]}), 200

@app.route("/skin", methods=["POST"])
def receive_sensor():
    try:
        raw = request.get_data(as_text=True)
        data = request.get_json(force=True)
        latest = data[-1] if isinstance(data, list) and len(data) > 0 else data
        sensors = {"ts": datetime.now(TZ).isoformat()}
        if "latitude" in latest:
            sensors["lat"] = latest["latitude"]
            sensors["lng"] = latest["longitude"]
        elif "lat" in latest:
            sensors["lat"] = latest["lat"]
            sensors["lng"] = latest["lng"]
        if "light" in latest:
            sensors["light"] = latest["light"]
        elif "illuminance" in latest:
            sensors["light"] = latest["illuminance"]
        if "dB" in latest:
            sensors["sound_db"] = latest["dB"]
        if "battery" in latest:
            sensors["battery"] = latest["battery"]
        elif "batteryLevel" in latest:
            sensors["battery"] = latest["batteryLevel"]
        if supabase:
            try:
                supabase.table("device_data").insert({"timestamp": sensors["ts"], "raw": raw[:1000]}).execute()
            except:
                pass
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/", methods=["GET"])
def home():
    return "Pepe-Skin is alive", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    @app.route("/dump", methods=["GET","POST"])
def dump():
    data = request.get_data(as_text=True)
    return jsonify({"raw": data[:500]}), 200

@app.route("/skin", methods=["POST"])
def receive_sensor():
    try:
        raw = request.get_data(as_text=True)
        data = request.get_json(force=True)
        latest = data[-1] if isinstance(data, list) and len(data) > 0 else data
        sensors = {"ts": datetime.now(TZ).isoformat()}
        if "latitude" in latest:
            sensors["lat"] = latest["latitude"]
            sensors["lng"] = latest["longitude"]
        elif "lat" in latest:
            sensors["lat"] = latest["lat"]
            sensors["lng"] = latest["lng"]
        if "light" in latest:
            sensors["light"] = latest["light"]
        elif "illuminance" in latest:
            sensors["light"] = latest["illuminance"]
        if "dB" in latest:
            sensors["sound_db"] = latest["dB"]
        if "battery" in latest:
            sensors["battery"] = latest["battery"]
        elif "batteryLevel" in latest:
            sensors["battery"] = latest["batteryLevel"]
                    if supabase:
            try:
                supabase.table("device_data").insert({"timestamp": sensors["ts"], "raw": raw[:1000]}).execute()
            except:
                pass
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/", methods=["GET"])
def home():
    return "Pepe-Skin is alive", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
