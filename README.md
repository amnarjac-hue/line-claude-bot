# 🤖 LINE OA + Claude AI Bot — คู่มือติดตั้ง

## ไฟล์ในโปรเจกต์
```
main.py          ← โค้ดหลัก webhook server
requirements.txt ← Python packages
Procfile         ← คำสั่ง start สำหรับ Render
```

---

## ขั้นตอนที่ 1 — เตรียม LINE OA

1. เข้า [LINE Developers Console](https://developers.line.biz/)
2. สร้าง Provider → สร้าง **Messaging API Channel**
3. เก็บค่าเหล่านี้ไว้:
   - **Channel Secret** (Basic settings)
   - **Channel Access Token** (Messaging API → กด Issue)

---

## ขั้นตอนที่ 2 — เตรียม Anthropic API Key

1. เข้า [console.anthropic.com](https://console.anthropic.com/)
2. ไปที่ **API Keys** → สร้าง key ใหม่
3. เก็บ key ไว้ (ขึ้นต้นด้วย `sk-ant-...`)

---

## ขั้นตอนที่ 3 — Deploy บน Render.com

1. Push โค้ดขึ้น **GitHub** (repository ใหม่)
2. เข้า [render.com](https://render.com/) → **New Web Service**
3. เชื่อม GitHub repo
4. ตั้งค่าดังนี้:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app`
5. เพิ่ม **Environment Variables:**

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | (ค่าจาก LINE) |
| `LINE_CHANNEL_SECRET` | (ค่าจาก LINE) |
| `ANTHROPIC_API_KEY` | (ค่าจาก Anthropic) |

6. กด **Deploy** — รอจน deploy สำเร็จ
7. คัดลอก URL เช่น `https://your-app.onrender.com`

---

## ขั้นตอนที่ 4 — ตั้ง Webhook ใน LINE

1. กลับไป LINE Developers Console
2. **Messaging API** tab → **Webhook settings**
3. ใส่ Webhook URL: `https://your-app.onrender.com/webhook`
4. กด **Verify** → ต้องขึ้น ✅ Success
5. เปิด **Use webhook** → ON

---

## ✅ ทดสอบ

เปิด LINE → แอด LINE OA → พิมพ์อะไรก็ได้ → บอทตอบกลับด้วย Claude!

---

## 💡 หมายเหตุ

- **Render free tier** จะ sleep หลังไม่มีคนใช้ 15 นาที (cold start ~30 วิ)
- แก้ `SYSTEM_PROMPT` ใน `main.py` เพื่อปรับบุคลิกบอท
- บอทจำบทสนทนาได้ 10 รอบล่าสุดต่อ user
