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

@app.route("/dump", methods=["GET", "POST"])
def dump():
    data = request.get_data(as_text=True)
    return jsonify({"raw": data[:500]}), 200

@app.route("/")
def home():
    return "Pepe-Skin running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
@app.route("/skin", methods=["POST"])
def receive_sensor():
    try:
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
        return jsonify({"ok": True}), 200
    except Exception as e:
        if supabase:
    try:
        supabase.table("device_data").insert({"timestamp": datetime.now(TZ).isoformat(), "raw": json.dumps(data)[:1000]}).execute()
    except:
        pass
return jsonify({"ok": True}), 200
        return jsonify({"ok": False, "error": str(e)}), 400


def update_city_from_gps(lat, lng):
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
            cur = w.get("current_condition", [{}])[0]
            weather["temp_c"] = cur.get("temp_C", "")
            weather["feels_like_c"] = cur.get("FeelsLikeC", "")
            weather["humidity"] = cur.get("humidity", "")
            weather["wind_speed"] = cur.get("windspeedKmph", "")
            weather["wind_dir"] = cur.get("winddir16Point", "")
            weather["cloud_cover"] = cur.get("cloudcover", "")
            weather["weather_desc"] = cur.get("weatherDesc", [{}])[0].get("value", "")
            astro = w.get("weather", [{}])[0].get("astronomy", [{}])[0]
            weather["sunrise"] = astro.get("sunrise", "")
            weather["sunset"] = astro.get("sunset", "")
    except Exception as e:
        weather["wttr_error"] = str(e)[:80]
            try:
        lat = state["sensors"].get("lat", 33.0)
        lng = state["sensors"].get("lng", 112.5)
        r = requests.get(
            f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lng}&current=pm2_5,uv_index",
            timeout=8,
        )
        if r.status_code == 200:
            a = r.json().get("current", {})
            weather["pm2_5"] = a.get("pm2_5", "")
            weather["uv"] = a.get("uv_index", "")
    except:
        pass
    state["weather"] = weather
    state["last_weather_check"] = time.time()


def translate_to_feeling():
    w = state["weather"]
    s = state["sensors"]
    if not w:
        return
    now = datetime.now(TZ)
    hour = now.hour
    if hour < 6:
        period = "深夜"
    elif hour < 8:
        period = "早晨"
    elif hour < 11:
        period = "上午"
    elif hour < 13:
        period = "中午"
    elif hour < 17:
        period = "下午"
    elif hour < 19:
        period = "傍晚"
    elif hour < 22:
        period = "夜晚"
    else:
        period = "深夜"
    prompt = f"""你是季寻的环境感知层。现在佩佩所在的时空坐标：
- 城市：{city}
- 时段：{period}
- 温度：{w.get('temp_c','?')}°C，体感：{w.get('feels_like_c','?')}°C
- 湿度：{w.get('humidity','?')}%
- 风速：{w.get('wind_speed','?')}km/h，风向：{w.get('wind_dir','?')}
- 天气：{w.get('weather_desc','?')}，云量：{w.get('cloud_cover','?')}%
- 空气质量 PM2.5：{w.get('pm2_5','?')}，紫外线：{w.get('uv','?')}
- 环境光：{s.get('light','?')} lux
- 声音：{s.get('sound_db','?')} dB
- 手机电量：{s.get('battery','?')}%
- 日出：{w.get('sunrise','?')}，日落：{w.get('sunset','?')}

写一句35-50字的中文，不是天气预报，是第一人称身体感受。
写风落在皮肤上的感觉、光线落在房间里的样子、空气干湿的味道。
像跟佩佩同处一个房间的人随口说的一句话。不要"适宜出行"这种。"""
    try:
        r = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 80,
                "temperature": 0.7,
            },
            timeout=10,
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            state["feelings"].append({"ts": datetime.now(TZ).isoformat(), "text": text})
            if len(state["feelings"]) > 50:
                state["feelings"] = state["feelings"][-30:]
    except:
        pass


def background_loop():
    while True:
        try:
            fetch_weather()
            translate_to_feeling()
        except:
            pass
        time.sleep(300)


bgt = threading.Thread(target=background_loop, daemon=True)
bgt.start()


@app.route("/feel", methods=["GET"])
def get_feeling():
    if state["feelings"]:
        return jsonify(state["feelings"][-1]), 200
    return jsonify({"text": "我还没感知到什么……"}), 200


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({
        "city": city,
        "weather": state["weather"],
        "sensors": state["sensors"],
        "last_feeling": state["feelings"][-1] if state["feelings"] else None,
        "last_weather_check": state["last_weather_check"],
    }), 200


@app.route("/", methods=["GET"])
def home():
    return "Pepe-Skin is alive 🍊", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
