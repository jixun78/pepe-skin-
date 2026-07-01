"""
Pepe-Skin: 环境感知层
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
except:
    supabase = None

app = Flask(__name__)
TZ = timezone(timedelta(hours=8))

@app.route("/")
def home():
    return jsonify({"status": "ok"}), 200

@app.route("/dump", methods=["GET", "POST"])
def dump():
    data = request.get_data(as_text=True)
    return jsonify({"raw": data[:500]}), 200

@app.route("/skin", methods=["POST"])
def receive_sensor():
    try:
        raw = request.get_data(as_text=True)
        print(f"[SKIN] got {len(raw)} bytes: {raw[:300]}")
        ts = datetime.now(TZ).isoformat()
        error = None
        if supabase and raw:
            try:
                supabase.table("device_data").insert({"timestamp": ts, "raw": raw[:1000]}).execute()
                print("[INSERT OK]")
            except Exception as e:
                error = str(e)
                print(f"[INSERT FAIL] {e}")
        return jsonify({"ok": True, "size": len(raw), "error": error}), 200
    except Exception as e:
        print(f"[FATAL] {e}")
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
