import os
import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Настройки
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
FILES_ROOT = os.environ.get("FILES_ROOT", "temp")

# Создаем папку для временных файлов
os.makedirs(FILES_ROOT, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context):
    update.message.reply_text("Send any file (up to 2GB) and I'll give a direct link.")

def handle_file(update: Update, context):
    if not (update.message.document or update.message.video or update.message.audio):
        return

    msg = update.message.reply_text("⏳ Processing...")
    try:
        file_obj = update.message.document or update.message.video or update.message.audio
        # Скачиваем файл на сервер
        file = context.bot.get_file(file_obj.file_id)
        file_path = os.path.join(FILES_ROOT, f"{file_obj.file_id}")
        file.download(file_path)
        # Формируем прямую ссылку
        public_url = f"{BASE_URL}/file/{file_obj.file_id}"
        msg.edit_text(f"✅ Link:\n{public_url}")
    except Exception as e:
        logger.exception("Error")
        msg.edit_text(f"❌ {e}")

def main():
    bot = Bot(token=BOT_TOKEN)
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.attachment, handle_file))
    
    # Используем вебхуки вместо polling для стабильности
    if WEBHOOK_URL:
        updater.start_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 8080)), url_path=BOT_TOKEN)
        updater.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
        logger.info(f"Webhook started on {WEBHOOK_URL}")
    else:
        updater.start_polling()
        logger.info("Polling started")
    
    updater.idle()

if __name__ == '__main__':
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set")
    main()
