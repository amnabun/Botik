import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8433286201:AAHyMW-gmwgWTRm8kTSEUkOlzmJV-KTkIAU"

# Шрифты
FONT_SEMIBOLD = "fonts/Roboto-SemiBold.ttf"
FONT_REGULAR = "fonts/Roboto-Regular.ttf"
FONT_BOLD = "fonts/SFProDisplay-Bold.ttf"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
    👋 Привет! Я бот для редактирования билетов Avtobys.

    📝 Отправьте мне ТРИ строки:
    1. Номер билета (например: 563BE04)
    2. Дата и время в формате: 28 августа 2025 12:05
    3. Время для второго поля в формате: 12:05

    Например:
    563BE04
    28 августа 2025 12:05
    12:05
    """
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        text = update.message.text.strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) < 3:
            await update.message.reply_text("❌ Пожалуйста, отправьте ТРИ строки:\n1. Номер билета\n2. Дата и время\n3. Время для второго поля")
            return
        
        ticket_number = lines[0]
        date_time_str = lines[1]
        second_time_str = lines[2]  # Второе время

        # Валидация номера билета
        if not re.match(r'^[A-Z0-9]{5,10}$', ticket_number):
            await update.message.reply_text("❌ Неверный формат номера билета. Используйте только буквы и цифры (5-10 символов)")
            return
        
        # Валидация даты и времени (первое время)
        try:
            # Парсим дату в формате "28 августа 2025 12:05"
            date_parts = date_time_str.split()
            if len(date_parts) < 4:
                raise ValueError("Недостаточно частей даты и времени")
            
            day = int(date_parts[0])
            month_str = date_parts[1].lower()
            year = int(date_parts[2])
            first_time_str = date_parts[3]  # Первое время из даты
            
            # Преобразуем название месяца в число
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }
            
            if month_str not in months:
                raise ValueError("Неверное название месяца")
            
            # Валидация первого времени
            if ':' in first_time_str:
                hours1, minutes1 = map(int, first_time_str.split(':'))
                if not (0 <= hours1 <= 23 and 0 <= minutes1 <= 59):
                    raise ValueError("Неверное первое время")
                formatted_first_time = f"{hours1:02d}:{minutes1:02d}"
            else:
                raise ValueError("Неверный формат первого времени")
            
            # Форматируем дату и первое время для отображения
            formatted_date_time = f"{day} {month_str} {year} {formatted_first_time}"
            
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                "❌ Неверный формат даты и времени.\n"
                "Используйте формат: 28 августа 2025 12:05\n"
                "Пример: 15 сентября 2024 14:30"
            )
            return
        
        # Валидация второго времени
        try:
            if ':' in second_time_str:
                hours2, minutes2 = map(int, second_time_str.split(':'))
                if not (0 <= hours2 <= 23 and 0 <= minutes2 <= 59):
                    raise ValueError("Неверное второе время")
                formatted_second_time = f"{hours2:02d}:{minutes2:02d}"
            else:
                raise ValueError("Неверный формат второго времени")
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат второго времени.\n"
                "Используйте формат: 12:05\n"
                "Пример: 14:30"
            )
            return
        
        # Создаем edited_ticket.png
        output_path = edit_ticket_image(ticket_number, formatted_date_time, formatted_second_time)
        
        # Отправляем изображение как ФАЙЛ
        with open(output_path, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=f"ticket_{ticket_number}.png",
                caption=f"✅ Готово!\nНомер: {ticket_number}\nДата и время: {formatted_date_time}\nВторое время: {formatted_second_time}"
            )
        
        # Удаляем временный файл
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз.")

def edit_ticket_image(ticket_number: str, date_time_str: str, second_time_str: str):
    """Редактирование изображения билета"""
    # Загрузка исходного изображения
    base_image = Image.open("proez.png")
    draw = ImageDraw.Draw(base_image)
    
    # Координаты и размеры текста
    coordinates = {
        'ticket_number': (653, 2537),  # x, y для номера билета
        'date_time': (447, 2680),      # x, y для даты и первого времени
        'second_time': (170, 65)       # x, y для второго времени
    }
    
    # Размеры шрифтов
    font_sizes = {
        'ticket_number': 64,
        'date_time': 64,
        'second_time': 66
    }
    
    try:
        # Загрузка шрифтов
        font_semibold = ImageFont.truetype(FONT_SEMIBOLD, font_sizes['ticket_number'])
        font_regular = ImageFont.truetype(FONT_REGULAR, font_sizes['date_time'])
        font_bold = ImageFont.truetype(FONT_BOLD, font_sizes['second_time'])
    except Exception as e:
        logger.error(f"Font error: {e}")
        # Fallback на стандартный шрифт
        font_semibold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()
    
    # Рисуем номер билета
    draw.text(
        coordinates['ticket_number'],
        ticket_number,
        fill="#1F1F1F",
        font=font_semibold,
    )
    
    # Рисуем дату и первое время
    draw.text(
        coordinates['date_time'],
        date_time_str,
        fill="#3F3F3F",
        font=font_regular,
    )

    # Рисуем второе время
    draw.text(
        coordinates['second_time'],
        second_time_str,
        fill="#0E0E0E",
        font=font_bold,
    )
    
    # Сохраняем результат
    output_path = "/home/bbbbuunn/botik/Botik/edited_ticket.png"
    base_image.save(output_path)
    
    return output_path

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()