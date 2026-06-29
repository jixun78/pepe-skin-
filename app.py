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
        print(f"[SKIN RAW] {raw[:200]}")
        if supabase:
            supabase.table("device_data").insert({"timestamp": datetime.now(TZ).isoformat(), "raw": raw[:1000]}).execute()
            print("[INSERT OK]")
        return jsonify({"ok": True}), 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
