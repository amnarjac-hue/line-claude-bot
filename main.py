import os
import json
import hmac
import hashlib
import base64
import requests
from flask import Flask, request, abort
import anthropic

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversation_history = {}

SYSTEM_PROMPT = """คุณคือผู้ช่วย AI ที่เป็นมิตรและมีประโยชน์ ตอบภาษาไทยเป็นหลัก 
ให้คำตอบที่กระชับ ชัดเจน และเป็นประโยชน์ต่อผู้ใช้"""

def verify_signature(body, signature):
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash).decode("utf-8")
    return hmac.compare_digest(expected, signature)

def reply_message(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=payload
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    if not verify_signature(body, signature):
        abort(400)

    data = json.loads(body)
    for event in data.get("events", []):
        if event.get("type") != "message":
            continue
        if event["message"].get("type") != "text":
            continue

        user_id = event["source"]["userId"]
        user_message = event["message"]["text"]
        reply_token = event["replyToken"]

        if user_id not in conversation_history:
            conversation_history[user_id] = []

        conversation_history[user_id].append({
            "role": "user",
            "content": user_message
        })

        if len(conversation_history[user_id]) > 20:
            conversation_history[user_id] = conversation_history[user_id][-20:]

        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=conversation_history[user_id]
            )
            reply_text = response.content[0].text

            conversation_history[user_id].append({
                "role": "assistant",
                "content": reply_text
            })

        except Exception as e:
            reply_text = f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"

        reply_message(reply_token, reply_text)

    return "OK"

@app.route("/", methods=["GET"])
def health():
    return "LINE Claude Bot is running! ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
