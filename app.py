from flask import Flask, request, jsonify
from supabase import create_client
import os
import json
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
TZ = timezone(timedelta(hours=8))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

state = {"_raw_last": "", "sensors": {}}

@app.route('/')
def home():
    return "SensorLogger -> Supabase ✅"

@app.route('/dump', methods=['GET','POST'])
def dump():
    return f"<pre>{request.get_data(as_text=True)}</pre>", 200

@app.route('/skin', methods=['POST'])
def receive_sensor():
    try:
        raw = request.get_data(as_text=True)
        data = request.get_json(force=True)
        latest = data[-1] if isinstance(data, list) and len(data) > 0 else data
        sensors = {"ts": datetime.now(TZ).isoformat()}
        if "latitude" in latest: sensors["lat"] = latest["latitude"]
        elif "lat"["lat"] = latest["lat"]
        if "longitude"[" = latest["longitude"]
        elif "lng" in latest: sensors["l = latest["lng"]
        if "light" in latest: sensors["light"] = latest["light"]
        elif "illuminance" in latest: sensors["light"] = latest["illuminance"]
        if "dB" in latest: sensors["sound_db"] =dB"]
        if "battery" in latest: sensors["battery"] = latest["battery"]
        elif "batteryLevel" in latest: sensors["battery"] = latest["batteryLevel"]
        state["_raw_last"] = raw[:800]
        state["sensors"] = sensors
        if supabase:
            supabase.table("device_data").insert({"timestamp": sensors["ts"], "raw": raw[:1000]}).execute()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
