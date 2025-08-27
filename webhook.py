import os
import requests
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# --- Config từ biến môi trường
BOT_TOKEN = 7558xxxx:AAHhYt2DIj8Ik8dBKZQHgburr5fs2TyjnAM
PAYOS_CLIENT_ID = 6914bbed-7a69-4165-8274-8c4e8823e8ac
PAYOS_API_KEY = 701cc8cf-6c71-4b32-a660-45f70a97b4e7

app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Gọi PayOS tạo QR
def create_payment(amount: int, user_id: int):
    url = "https://api.payos.vn/v2/payment-requests"
    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "orderCode": str(user_id),
        "amount": amount,
        "description": f"Nap_tien_{user_id}",
        "returnUrl": "https://example.com/return",
        "cancelUrl": "https://example.com/cancel"
    }
    res = requests.post(url, json=body, headers=headers).json()
    return res.get("data", {})

# /napbank <số tiền>
async def napbank(update: Update, context):
    parts = update.message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await update.message.reply_text("Cú pháp: /napbank <số tiền>")
        return
    amount = int(parts[1])
    data = create_payment(amount, update.message.chat_id)
    if "qrCode" in data:
        caption = (
            f"🏦 Ngân hàng: VCB\n"
            f"💳 Số tài khoản: {data.get('accountNumber')}\n"
            f"👤 Chủ tài khoản: {data.get('accountName')}\n"
            f"📝 Nội dung: {data.get('description')}\n"
            f"💰 Số tiền: {data.get('amount'):,}đ\n"
        )
        await update.message.reply_photo(photo=data["qrCode"], caption=caption)
    else:
        await update.message.reply_text("Không tạo được QR, thử lại sau.")

# /nap chọn nhanh
async def nap(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💰 50k", callback_data="nap_50000")],
        [InlineKeyboardButton("💰 100k", callback_data="nap_100000")],
        [InlineKeyboardButton("💰 200k", callback_data="nap_200000")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Chọn số tiền muốn nạp:", reply_markup=reply_markup)

# Xử lý khi click nút
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("nap_"):
        amount = int(query.data.split("_")[1])
        data = create_payment(amount, query.from_user.id)
        if "qrCode" in data:
            caption = (
                f"🏦 Ngân hàng: VCB\n"
                f"💳 Số tài khoản: {data.get('accountNumber')}\n"
                f"👤 Chủ tài khoản: {data.get('accountName')}\n"
                f"📝 Nội dung: {data.get('description')}\n"
                f"💰 Số tiền: {data.get('amount'):,}đ\n"
            )
            await query.message.reply_photo(photo=data["qrCode"], caption=caption)
        else:
            await query.message.reply_text("Không tạo được QR, thử lại sau.")

# Webhook PayOS
@app.post("/payos/webhook")
async def payos_webhook(request: Request):
    data = await request.json()
    print("PayOS callback:", data)
    return {"status": "ok"}

# Webhook Telegram
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

telegram_app.add_handler(CommandHandler("napbank", napbank))
telegram_app.add_handler(CommandHandler("nap", nap))
telegram_app.add_handler(CallbackQueryHandler(button))

@app.get("/")
async def root():
    return {"message": "Server running!"}
