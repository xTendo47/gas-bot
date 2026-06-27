import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8539185338:AAFfeRhe-uGYE_znA5f1QPTSVsTOUtmOY90"
PORT = int(os.environ.get("PORT", 10000))

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
        return "🃏 Колода была пуста и сброшена. Тяни снова."

    card = random.choice(decks[deck_name])
    decks[deck_name].remove(card)
    stats[deck_name] += 1

    if not is_arrow:
        turn += 1
        player = current_player
        current_player = "Тимур" if current_player == "Катя" else "Катя"
    else:
        player = current_player

    response = f"🎲 {deck_name.upper()} — ход {turn}\n"
    response += f"👤 Тянет: {player}\n\n"
    response += f"{card['text']}"

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text(
        "🔥 ИГРА «ГАЗ» НАЧИНАЕТСЯ!\n\nПервый ход — Катя.\nВыбирай колоду:",
        reply_markup=main_keyboard
    )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text("🔄 Колоды сброшены! Первый ход — Катя.", reply_markup=main_keyboard)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = "📊 СТАТИСТИКА\n\n"
    for deck, count in stats.items():
        text += f"{deck.upper()}: {count} карт\n"
    text += f"\nВсего: {total} карт\nСледующий ход: {current_player}"
    await update.message.reply_text(text)


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = "🏁 ИГРА ЗАВЕРШЕНА!\n\n"
    text += f"Газ: {stats['газ']}\nПолный газ: {stats['полный_газ']}\n"
    text += f"Пиздец газ: {stats['пиздец_газ']}\nДелай: {stats['делай']}\n"
    text += f"\nВсего карт: {total}\n\nСпасибо за игру! 🔥"
    await update.message.reply_text(text)
    reset_decks()


async def set_k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player
    current_player = "Катя"
    await update.message.reply_text("👤 Следующий ход — Катя")


async def set_t(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player
    current_player = "Тимур"
    await update.message.reply_text("👤 Следующий ход — Тимур")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()
    deck_map = {"ГАЗ": "газ", "ПОЛНЫЙ ГАЗ": "полный_газ", "ПИЗДЕЦ ГАЗ": "пиздец_газ", "ДЕЛАЙ": "делай"}

    if text in deck_map:
        response = pull_card(deck_map[text])
    elif text == "РАНДОМ":
        deck = random.choice(["газ", "полный_газ", "пиздец_газ", "делай"])
        response = f"🎯 Рандом выбрал: «{deck.upper()}»\n\n" + pull_card(deck)
    elif text == "СТАТИСТИКА":
        await stats_cmd(update, context)
        return
    elif text == "ФИНИШ":
        await finish(update, context)
        return
    else:
        response = "Используй кнопки или команды."

    await update.message.reply_text(response)


# ---------- ЗАПУСК ----------
load_decks()
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("restart", restart))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("finish", finish))
app.add_handler(CommandHandler("k", set_k))
app.add_handler(CommandHandler("t", set_t))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен на Render!")
app.run_polling(drop_pending_updates=True)
