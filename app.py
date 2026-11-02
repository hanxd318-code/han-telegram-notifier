
import os
import json
import hmac
import hashlib
import threading
import queue
import requests
from flask import Flask, request, abort

app = Flask(__name__)
jobs = queue.Queue()

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": text},
        timeout=10
    )

def worker():
    while True:
        message = jobs.get()
        try:
            send_message(message)
        except Exception:
            pass
        finally:
            jobs.task_done()

threading.Thread(target=worker, daemon=True).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    raw = request.get_data()
    signature = request.headers.get(
        "X-KSIIPRNTECHNOLOGY-Signature", ""
    )

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        raw,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        abort(401)

    event = json.loads(raw)
    name = event.get("event")
    data = event.get("data", {})

    if name == "number.assigned":
        message = "Nomor baru ditambahkan."

    elif name == "number.removed":
        message = "Nomor dihapus dari akun."

    elif name == "earnings.daily":
        message = (
            "Laporan pendapatan harian\n"
            f"Tanggal: {data.get('date')}\n"
            f"Mata uang: {data.get('currency')}\n"
            f"Jumlah pesan: {data.get('messages')}\n"
            f"Pendapatan: {data.get('earnings')}"
        )

    else:
        return "Event diabaikan", 200

    jobs.put(message)
    return "OK", 200

@app.route("/")
def home():
    return "Webhook server aktif", 200
