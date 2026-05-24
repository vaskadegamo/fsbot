import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web

# Переменные окружения
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = int(os.environ.get("PORT", 8080))

# Папка для временных файлов
os.makedirs("temp", exist_ok=True)

# Клиент Pyrogram
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Веб-сервер для отдачи файлов
web_app = web.Application()
file_map = {}  # file_id -> путь

async def stream_handler(request):
    file_id = request.match_info.get('file_id')
    path = file_map.get(file_id)
    if not path or not os.path.exists(path):
        return web.Response(status=404, text="File not found")
    return web.FileResponse(path)

web_app.router.add_get('/file/{file_id}', stream_handler)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("Send me any file (up to 2GB), I'll give a direct link.")

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_document(client, message):
    msg = await message.reply("⏳ Downloading...")
    file = message.document or message.video or message.audio
    file_id = file.file_id
    path = f"temp/{file_id}"
    await client.download_media(message, file_name=path)
    file_map[file_id] = path
    url = f"{BASE_URL}/file/{file_id}"
    await msg.edit_text(f"✅ Link: {url}\n(valid 1 hour)")

async def main():
    # Запускаем бота
    await app.start()
    # Запускаем веб-сервер
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Bot ready, web server on {BASE_URL}")
    # Держим приложение работающим
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
