import json
import random
import os
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8539185338:AAFfeRhe-uGYE_znA5f1QPTSVsTOUtmOY90"
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = "https://gas-bot-4cyt.onrender.com"

decks = {}
stats = {"газ": 0, "полный_газ": 0, "пиздец_газ": 0, "делай": 0}
original_decks = {}
current_player = "Катя"
turn = 0

main_keyboard = ReplyKeyboardMarkup([
    ["ГАЗ", "ПОЛНЫЙ ГАЗ"],
    ["ПИЗДЕЦ ГАЗ", "ДЕЛАЙ"],
    ["РАНДОМ", "СТАТИСТИКА"],
    ["ФИНИШ"]
], resize_keyboard=True)

app = Flask(__name__)


def load_decks():
    global decks, original_decks
    files = {
        "газ": "data/cards_gas.txt",
        "полный_газ": "data/cards_full_gas.txt",
        "пиздец_газ": "data/cards_pizdec_gas.txt",
        "делай": "data/cards_delai.txt"
    }
    for deck_name, filepath in files.items():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            decks[deck_name] = data["cards"][:]
            original_decks[deck_name] = data["cards"][:]


def reset_decks():
    global decks, stats, turn, current_player
    decks = {name: cards[:] for name, cards in original_decks.items()}
    stats = {"газ": 0, "полный_газ": 0, "пиздец_газ": 0, "делай": 0}
    turn = 0
    current_player = "Катя"


def is_x2():
    return random.randint(1, 100) <= 9


def pull_card(deck_name, is_arrow=False):
    global decks, stats, turn, current_player

    if deck_name not in decks or not decks[deck_name]:
        reset_decks()
        return "Колода пуста и сброшена. Тяни снова."

    card = random.choice(decks[deck_name])
    decks[deck_name].remove(card)
    stats[deck_name] += 1

    if not is_arrow:
        turn += 1
        player = current_player
        current_player = "Тимур" if current_player == "Катя" else "Катя"
    else:
        player = current_player

    response = f"🎲 {deck_name.upper()} — ход {turn}\n👤 Тянет: {player}\n\n{card['text']}"

    if card["type"] == "arrow":
        target = card["target"]
        response += f"\n\n➡️ Переход в «{target.upper()}»"
        if target == "рандом":
            target = random.choice(["газ", "полный_газ", "пиздец_газ", "делай"])
            response += f"\n🎯 Выпало: «{target.upper()}»"
        response += "\n\n" + pull_card(target, is_arrow=True)

    if is_x2() and card["type"] != "arrow":
        response += "\n\n🔥 Х2! Карта для обоих!"

    return response


# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text("🔥 ИГРА «ГАЗ» НАЧИНАЕТСЯ!\n\nПервый ход — Катя.", reply_markup=main_keyboard)


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text("🔄 Колоды сброшены! Первый ход — Катя.", reply_markup=main_keyboard)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = "📊 СТАТИСТИКА\n\n"
    for deck, count in stats.items():
        text += f"{deck.upper()}: {count}\n"
    text += f"\nВсего: {total}\nСледующий: {current_player}"
    await update.message.reply_text(text)


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = f"🏁 ИГРА ЗАВЕРШЕНА!\n\nГаз: {stats['газ']}\nПолный газ: {stats['полный_газ']}\nПиздец газ: {stats['пиздец_газ']}\nДелай: {stats['делай']}\n\nВсего: {total}\n\nСпасибо за игру! 🔥"
    await update.message.reply_text(text)
    reset_decks()


async def set_k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player
    current_player = "Катя"
    await update.message.reply_text("👤 Ход — Катя")


async def set_t(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player
    current_player = "Тимур"
    await update.message.reply_text("👤 Ход — Тимур")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()
    deck_map = {"ГАЗ": "газ", "ПОЛНЫЙ ГАЗ": "полный_газ", "ПИЗДЕЦ ГАЗ": "пиздец_газ", "ДЕЛАЙ": "делай"}

    if text in deck_map:
        response = pull_card(deck_map[text])
    elif text == "РАНДОМ":
        deck = random.choice(["газ", "полный_газ", "пиздец_газ", "делай"])
        response = f"🎯 Рандом: «{deck.upper()}»\n\n" + pull_card(deck)
    elif text in ["СТАТИСТИКА", "ФИНИШ"]:
        return
    else:
        response = "Используй кнопки."

    await update.message.reply_text(response)


# Flask route
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200


@app.route("/")
def home():
    return "Bot is live!", 200


if __name__ == "__main__":
    load_decks()
    telegram_app = Application.builder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("restart", restart))
    telegram_app.add_handler(CommandHandler("stats", stats_cmd))
    telegram_app.add_handler(CommandHandler("finish", finish))
    telegram_app.add_handler(CommandHandler("k", set_k))
    telegram_app.add_handler(CommandHandler("t", set_t))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def init():
        await telegram_app.initialize()
        await telegram_app.start()

    import asyncio
    asyncio.run(init())

    # Set webhook
    import requests
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}/webhook")

    app.run(host="0.0.0.0", port=PORT)
