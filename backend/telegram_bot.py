# telegram_bot.py

import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

def build_bot():
    app = Application.builder().token(TOKEN).build()

    async def start(update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[
            InlineKeyboardButton(
                "🎮 Play Bingo Game",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]]
        await update.message.reply_text(
            "Welcome to Bingo Bot 🎲\nTap below to play",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    app.add_handler(CommandHandler("start", start))
    return app
