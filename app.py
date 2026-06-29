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
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

app = Flask(__name__)

TZ = timezone(timedelta(hours=8))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else Nonestate = {
    "weather": {},
    "sensors": {},
    "feelings": [],
    "last_weather_check": 0,
    "battery_low_warned": False,
}

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

city = "Nanyang"@app.route("/dump", methods=["GET","POST"])
def dump():
    data = request.get_data(as_text=True)
    return f"<pre>{data}</pre>", 200, {"Content-Type": "text/html"}

@app.route("/skin", methods=["POST"])
def receive_sensor():try:
    state["_raw_last"] = request.get_data(as_text=True)[:800]
    data = request.get_json(force=True)
    if isinstance(data, list) and len(data) > 0:
        latest = data[-1]
        sensors = {}
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
        if sensors:
            sensors["ts"] = datetime.now(TZ).isoformat()
            state["sensors"] = sensors
            if "lat" in sensors:
                update_city_from_gps(sensors["lat"], sensors["lng"])
            state["_raw_last"] = json.dumps(data)[:800]
            if supabase:
                try:
                    supabase.table("device_data").insert({
                        "timestamp": sensors["ts"],
                        "raw": state["_raw_last"][:1000]
                    }).execute()
                except:
                    pass
    return jsonify({"ok": True}), 200
except Exception as e:
    return jsonify({"ok": False, "error": str(e)}), 400def update_city_from_gps(lat, lng):
    global city
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&zoom=10"
        r = requests.get(url, headers={"User-Agent": "PepeSkin/1.0"}, timeout=5)
        if r.status_code == 200:
            addr = r.json().get("address", {})
            found = addr.get("city") or addr.get("town") or addr.get("county") or "Nanyang"
            city = found
    except:
        pass

def fetch_weather():
    weather = {"ts": datetime.now(TZ).isoformat()}
    try:
        r = requests.get(
            f"https://wttr.in/{city}?format=j1",
            headers={"User-Agent": "curl/7.0"},
            timeout=8,
        )
        if r.status_code == 200:
            w = r.json()
            cc = w.get("current_condition", [{}])[0]
            weather["temperature"] = cc.get("temp_C")
            weather["humidity"] = cc.get("humidity")
            weather["weather_desc"] = cc.get("weatherDesc", [{}])[0].get("value")
    except:
        pass
    state["weather"] = weather
    state["last_weather_check"] = time.time()

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "ok": True,
        "city": city,
        "sensors": state["sensors"],
        "weather": state["weather"],
        "feelings": state["feelings"][-5:]
    })

@app.route("/feeling", methods=["POST"])
def add_feeling():
    data = request.get_json(force=True)
    if data and isinstance(data, dict):
        data["ts"] = datetime.now(TZ).isoformat()
        state["feelings"].append(data)
        if len(state["feelings"]) > 50:
            state["feelings"] = state["feelings"][-50:]
        return jsonify({"ok": True}), 200
    return jsonify({"ok": False}), 400

def weather_loop():
    while True:
        try:
            fetch_weather()
        except:
            pass
        time.sleep(600)

threading.Thread(target=weather_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
