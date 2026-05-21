import os
import random
import string
from PIL import Image
from telegram import Update, InputSticker
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "8661575521:AAHD_C0EYhrZPRnYnLxx3zSlsojvt9vp6ic"

# Хранилище пользователей
users_data = {}

os.makedirs("stickers", exist_ok=True)


def random_pack_name(user_id):
    rand = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f"pack_{user_id}_{rand}_by_creaturestick_bot"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_data[update.effective_user.id] = []

    await update.message.reply_text(
        "Отправляй фото для будущего стикерпака.\n"
        "Когда закончишь — напиши /createpack"
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users_data:
        users_data[user_id] = []

    photo = update.message.photo[-1]
    file = await photo.get_file()

    input_path = f"stickers/{photo.file_unique_id}.jpg"
    output_path = f"stickers/{photo.file_unique_id}.webp"

    await file.download_to_drive(input_path)

    image = Image.open(input_path).convert("RGBA")

    image.thumbnail((512, 512))

    sticker = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

    x = (512 - image.width) // 2
    y = (512 - image.height) // 2

    sticker.paste(image, (x, y))

    sticker.save(output_path, "WEBP")

    users_data[user_id].append(output_path)

    await update.message.reply_text(
        f"Фото добавлено! Сейчас в паке: {len(users_data[user_id])}"
    )

    os.remove(input_path)


async def create_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in users_data or len(users_data[user_id]) == 0:
        await update.message.reply_text("Ты ещё не отправил фото.")
        return

    sticker_paths = users_data[user_id]

    pack_name = random_pack_name(user_id)
    pack_title = f"{user.first_name}'s Pack"

    stickers = []

    for path in sticker_paths:
        sticker_file = open(path, "rb")

        stickers.append(
            InputSticker(
                sticker=sticker_file,
                emoji_list=["🔥"]
            )
        )

    # Создание пака
    success = await context.bot.create_new_sticker_set(
        user_id=user_id,
        name=pack_name,
        title=pack_title,
        stickers=[stickers[0]],
        sticker_format="static"
    )

    if not success:
        await update.message.reply_text("Ошибка создания стикерпака.")
        return

    # Добавление остальных
    for sticker in stickers[1:]:
        await context.bot.add_sticker_to_set(
            user_id=user_id,
            name=pack_name,
            sticker=sticker
        )

    # Удаляем временные файлы
    for path in sticker_paths:
        if os.path.exists(path):
            os.remove(path)

    users_data[user_id] = []

    pack_link = f"https://t.me/addstickers/{pack_name}"

    await update.message.reply_text(
        f"Стикерпак создан!\n{pack_link}"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createpack", create_pack))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("Бот запущен")

    app.run_polling()


if __name__ == "__main__":
    main()
