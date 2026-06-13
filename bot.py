import os
import sqlite3
import random
import string

from PIL import Image

from telegram import (
    Update,
    InputSticker,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8661575521:AAHD_C0EYhrZPRnYnLxx3zSlsojvt9vp6ic"

BOT_USERNAME = "creaturestck_bot"

os.makedirs("stickers", exist_ok=True)

# ================= FUNNY MESSAGES =================

FUNNY_MESSAGES = [
    "🔥 Готово! Этот стикер теперь будет позорить тебя в чатах.",
    "😂 Уровень кринжа успешно повышен.",
    "💀 Если тебя начнут банить — я не виноват.",
    "⚡️ Новый мем создан. Интернет дрожит.",
    "👀 Я бы это не отправлял... но уже поздно.",
    "🧠 Этот стикер умнее некоторых людей.",
    "📸 Сделано. Теперь это официально мем.",
    "🚀 Стикер улетел в Telegram-вселенную.",
    "☠️ Осторожно: вызывает смех у окружающих.",
]

# ================= DATABASE =================

db = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_path TEXT
)
""")

db.commit()

# ================= HELPERS =================

def random_pack_name(user_id):

    rand = ''.join(
        random.choices(string.ascii_lowercase, k=6)
    )

    return f"pack_{user_id}_{rand}_by_{BOT_USERNAME}"


def add_user(user_id):

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    db.commit()


def add_sticker(user_id, file_path):

    cursor.execute(
        "INSERT INTO stickers (user_id, file_path) VALUES (?, ?)",
        (user_id, file_path)
    )

    db.commit()


def get_user_stickers(user_id):

    cursor.execute(
        "SELECT file_path FROM stickers WHERE user_id=?",
        (user_id,)
    )

    return [row[0] for row in cursor.fetchall()]


def clear_user_stickers(user_id):

    stickers = get_user_stickers(user_id)

    for path in stickers:

        if os.path.exists(path):
            os.remove(path)

    cursor.execute(
        "DELETE FROM stickers WHERE user_id=?",
        (user_id,)
    )

    db.commit()

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    add_user(user_id)

    keyboard = [
        ["🎨 Создать стикеры"],
        ["🗑 Очистить"]
    ]

    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Добро пожаловать на мемный завод.\n\n"
        "📸 Кидай фотки.\n"
        "🔥 Я превращу их в стикеры.\n\n"
        "📦 Отправь стикер — и я создам sticker pack.",
        reply_markup=markup
    )

# ================= PHOTO HANDLER =================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    add_user(user_id)

    photo = update.message.photo[-1]

    file = await photo.get_file()

    input_path = f"stickers/{photo.file_unique_id}.jpg"
    output_path = f"stickers/{photo.file_unique_id}.webp"

    await file.download_to_drive(input_path)

    image = Image.open(input_path).convert("RGBA")

    image.thumbnail((512, 512))

    canvas = Image.new(
        "RGBA",
        (512, 512),
        (0, 0, 0, 0)
    )

    x = (512 - image.width) // 2
    y = (512 - image.height) // 2

    canvas.paste(image, (x, y))

    canvas.save(
        output_path,
        "WEBP",
        quality=100
    )

    os.remove(input_path)

    add_sticker(user_id, output_path)

    with open(output_path, "rb") as sticker_file:

        await update.message.reply_sticker(
            sticker=sticker_file
        )

    await update.message.reply_text(
        random.choice(FUNNY_MESSAGES)
    )

# ================= STICKER HANDLER =================

async def sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    user_id = user.id

    add_user(user_id)

    sticker = update.message.sticker

    file = await sticker.get_file()

    sticker_path = f"stickers/{sticker.file_unique_id}.webp"

    await file.download_to_drive(sticker_path)

    pack_name = random_pack_name(user_id)

    pack_title = f"{user.first_name} MEM PACK"

    try:

        with open(sticker_path, "rb") as f:

            first_sticker = InputSticker(
                sticker=f,
                emoji_list=["🔥"]
            )

            await context.bot.create_new_sticker_set(
                user_id=user_id,
                name=pack_name,
                title=pack_title,
                stickers=[first_sticker]
            )

        pack_link = f"https://t.me/addstickers/{pack_name}"

        await update.message.reply_text(
            f"🎉 Стикерпак создан!\n\n{pack_link}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Ошибка:\n{e}"
        )

# ================= CREATE PACK =================

async def create_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    user_id = user.id

    sticker_paths = get_user_stickers(user_id)

    if not sticker_paths:

        await update.message.reply_text(
            "😢 Нет стикеров"
        )

        return

    pack_name = random_pack_name(user_id)

    pack_title = f"{user.first_name} MEM PACK"

    with open(sticker_paths[0], "rb") as f:

        first = InputSticker(
            sticker=f,
            emoji_list=["😂"]
        )

        await context.bot.create_new_sticker_set(
            user_id=user_id,
            name=pack_name,
            title=pack_title,
            stickers=[first]
        )

    for path in sticker_paths[1:]:

        with open(path, "rb") as f:

            sticker = InputSticker(
                sticker=f,
                emoji_list=["🔥"]
            )

            await context.bot.add_sticker_to_set(
                user_id=user_id,
                name=pack_name,
                sticker=sticker
            )

    await update.message.reply_text(
        f"🎉 Готово!\n\n"
        f"https://t.me/addstickers/{pack_name}"
    )

    clear_user_stickers(user_id)

# ================= CLEAR =================

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    clear_user_stickers(user_id)

    await update.message.reply_text(
        "🗑 Очищено"
    )

# ================= BUTTONS =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎨 Создать стикеры":

        await update.message.reply_text(
            "📸 Отправь фото"
        )

    elif text == "🗑 Очистить":

        await clear(update, context)

# ================= MAIN =================

def main():

    app = (
        Application.builder()
        .token(TOKEN)
        .proxy("socks5://127.0.0.1:10808")
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("createpack", create_pack)
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Sticker.ALL,
            sticker_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )

    print("BOT STARTED")

    app.run_polling()

# ================= START BOT =================

if __name__ == "__main__":
    main()
