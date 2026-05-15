import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import anthropic

app = Flask(__name__)

# --- Config from Environment Variables ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# In-memory conversation history (per user, max 10 turns)
conversation_history = {}

SYSTEM_PROMPT = """คุณคือผู้ช่วย AI ที่เป็นมิตรและมีประโยชน์ ตอบภาษาไทยเป็นหลัก 
ให้คำตอบที่กระชับ ชัดเจน และเป็นประโยชน์ต่อผู้ใช้"""

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    # Build conversation history
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Keep only last 10 turns (20 messages)
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

        # Save assistant reply to history
        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply_text
        })

    except Exception as e:
        reply_text = f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/", methods=["GET"])
def health():
    return "LINE Claude Bot is running! ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
