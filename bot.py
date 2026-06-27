import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- НАСТРОЙКИ ----------
TOKEN = "8539185338:AAFfeRhe-uGYE_znA5f1QPTSVsTOUtmOY90"  # 

# Хранилище колод и статистики
decks = {}
stats = {"газ": 0, "полный_газ": 0, "пиздец_газ": 0, "делай": 0}
original_decks = {}
current_player = "Катя"  # Катя ходит первой
turn = 0

# ---------- КНОПКИ ----------
main_keyboard = ReplyKeyboardMarkup([
    ["ГАЗ", "ПОЛНЫЙ ГАЗ"],
    ["ПИЗДЕЦ ГАЗ", "ДЕЛАЙ"],
    ["РАНДОМ", "СТАТИСТИКА"],
    ["ФИНИШ"]
], resize_keyboard=True)


# ---------- ЗАГРУЗКА КАРТ ----------
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


# ---------- СБРОС КОЛОД ----------
def reset_decks():
    global decks, stats, turn, current_player
    decks = {name: cards[:] for name, cards in original_decks.items()}
    stats = {"газ": 0, "полный_газ": 0, "пиздец_газ": 0, "делай": 0}
    turn = 0
    current_player = "Катя"


# ---------- X2 МЕХАНИКА ----------
def is_x2():
    return random.randint(1, 6) == 6  # ~17% шанс


# ---------- ВЫБОР КАРТЫ ----------
def pull_card(deck_name):
    global decks, stats, turn, current_player

    if deck_name not in decks or not decks[deck_name]:
        return "🃏 Колода пуста! Используй /restart для сброса."

    card = random.choice(decks[deck_name])
    decks[deck_name].remove(card)
    stats[deck_name] += 1

    turn += 1
    player = current_player
    # Меняем игрока для следующего хода
    current_player = "Тимур" if current_player == "Катя" else "Катя"

    # Формируем ответ
    response = f"🎲 {deck_name.upper()} — ход {turn}\n"
    response += f"👤 Тянет: {player}\n\n"
    response += f"{card['text']}"

    # Обработка стрелок
    if card["type"] == "arrow":
        target = card["target"]
        response += f"\n\n➡️ Переход в «{target.upper()}»"
        if target == "рандом":
            target = random.choice(["газ", "полный_газ", "пиздец_газ", "делай"])
            response += f"\n🎯 Выпало: «{target.upper()}»"
        response += "\n\n" + pull_card(target)

    # X2
    if is_x2() and card["type"] != "arrow":
        response += "\n\n🔥 Х2! Карта для обоих!"
        if card["type"] == "question":
            response += f"\nОтвечают оба по очереди."
        elif card["type"] == "action":
            response += f"\nВыполняют оба одновременно."
        elif card["type"] == "brudershaft":
            response += f"\nПьют оба и целуются."

    return response


# ---------- ОБРАБОТЧИКИ КОМАНД ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text(
        "🔥 ИГРА «ГАЗ» НАЧИНАЕТСЯ!\n\n"
        "Первый ход — Катя.\n"
        "Выбирай колоду на кнопках:\n\n"
        "Команды:\n"
        "/start — перезапуск\n"
        "/restart — сброс колод\n"
        "/stats — статистика\n"
        "/finish — завершить игру\n"
        "/k — ход Кати\n"
        "/t — ход Тимура",
        reply_markup=main_keyboard
    )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_decks()
    await update.message.reply_text(
        "🔄 Колоды сброшены! Игра началась заново.\nПервый ход — Катя.",
        reply_markup=main_keyboard
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = "📊 СТАТИСТИКА\n\n"
    for deck, count in stats.items():
        bar = "█" * count if count > 0 else "—"
        text += f"{deck.upper()}: {count} карт\n{bar}\n\n"
    text += f"Всего вытянуто: {total} карт\n"
    text += f"Следующий ход: {current_player}"
    await update.message.reply_text(text)


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(stats.values())
    text = "🏁 ИГРА ЗАВЕРШЕНА!\n\n"
    text += f"Всего вытянуто карт: {total}\n"
    text += f"Газ: {stats['газ']}\n"
    text += f"Полный газ: {stats['полный_газ']}\n"
    text += f"Пиздец газ: {stats['пиздец_газ']}\n"
    text += f"Делай: {stats['делай']}\n\n"
    text += "Спасибо за игру! 🔥\n"
    text += "Для новой игры нажми /start"
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


# ---------- ОБРАБОТЧИК ТЕКСТА (КНОПКИ) ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()

    if text == "ГАЗ":
        response = pull_card("газ")
    elif text == "ПОЛНЫЙ ГАЗ":
        response = pull_card("полный_газ")
    elif text == "ПИЗДЕЦ ГАЗ":
        response = pull_card("пиздец_газ")
    elif text == "ДЕЛАЙ":
        response = pull_card("делай")
    elif text == "РАНДОМ":
        deck = random.choice(["газ", "полный_газ", "пиздец_газ", "делай"])
        response = f"🎯 Рандом выбрал: «{deck.upper()}»\n\n"
        response += pull_card(deck)
    elif text == "СТАТИСТИКА":
        await stats_cmd(update, context)
        return
    elif text == "ФИНИШ":
        await finish(update, context)
        return
    else:
        response = "Используй кнопки или команды: /start, /restart, /stats, /finish, /k, /t"

    await update.message.reply_text(response)


# ---------- ЗАПУСК ----------
def main():
    load_decks()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("finish", finish))
    app.add_handler(CommandHandler("k", set_k))
    app.add_handler(CommandHandler("t", set_t))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()