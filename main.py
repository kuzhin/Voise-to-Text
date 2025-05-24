import os
import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.client.bot import Bot as AiogramBot
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Установка правильного Event Loop Policy для Windows
# если линукс - можно избежать этого (какая-то проблема с конфликтом винды)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Инициализация
router = Router()

def convert_format(input_path, output_path):
    """
    Конвертирует .ogg в .mp3

    Args:
        input_path: in
        output_path: out

    Returns: .mp3
    """
    try:
        audio = AudioSegment.from_ogg(input_path)
        audio.export(output_path, format="mp3")
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации: {e}")

def transcribe_audio_with_openai(file_path):
    """Расшифровка через OpenAI Whisper"""
    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcription
    except Exception as e:
        raise RuntimeError(f"Ошибка расшифровки: {e}")

@router.message(F.content_type == "voice")
async def handle_voice(message: Message):
    try:
        # Скачивание файла
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        await message.bot.download_file(file_path, "voice.ogg")

        convert_format("voice.ogg", "voice.mp3")

        # Расшифровка
        text = transcribe_audio_with_openai("voice.mp3")
        # await message.reply(f"Расшифровка: {text}")
        await message.reply(text)

        os.remove("voice.ogg")
        os.remove("voice.mp3")

    except Exception as e:
        await message.reply("Ошибка расшифровки. Попробуйте еще раз.")
        logging.error(e)

# Запуск бота
async def main():
    bot = AiogramBot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())