from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import os

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет! Я создаю наборы стикеров.\n"
        f"Я мгновенно превращаю фотографии в крутые стикеры.\n"
        f"Отправьте команду /help для получения дополнительной информации."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Чтобы создать стикер:\n"
        "- Отправьте фотографию\n"
        "- Бот автоматически превратит её в круглую картинку\n"
        "- Вы сможете скачать готовый стикер"
    )

async def create_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем фотографию от пользователя
    photo_file = await update.message.photo[-1].get_file()
    
    # Сохраняем временный файл
    temp_photo_path = f"{update.message.chat_id}_temp.jpg"
    await photo_file.download_to_drive(temp_photo_path)
    
    # Обрабатываем изображение
    image = Image.open(temp_photo_path)
    width, height = image.size
    
    # Создаем квадратное изображение
    size = max(width, height)
    square_image = Image.new("RGBA", (size, size))
    
    # Добавляем оригинальное изображение в центр квадрата
    position = ((size-width)//2, (size-height)//2)
    square_image.paste(image, position)
    
    # Круглая маска
    mask = Image.new("L", square_image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Применяем маску
    output = Image.new("RGBA", square_image.size)
    output.paste(square_image, mask=mask)
    
    # Сохраняем временное изображение
    temp_output_path = f"{update.message.chat_id}_output.webp"
    output.save(temp_output_path, "WEBP")
    
    # Отправляем стикер обратно пользователю
    await update.message.reply_document(InputFile(open(temp_output_path, "rb")), caption="Ваш стикер готов!")
    
    # Удаляем временные файлы
    os.remove(temp_photo_path)
    os.remove(temp_output_path)

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    
    # Обработчик фотографий
    application.add_handler(MessageHandler(filters.PHOTO, create_sticker))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()