import os
import asyncio
from telethon import TelegramClient, events
from aiohttp import web

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
BASE_URL = os.environ["BASE_URL"]   # например, https://mybot.onrender.com

bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
app = web.Application()
file_map = {}

async def stream(request):
    file_id = request.match_info.get('file_id')
    path = file_map.get(file_id)
    if not path or not os.path.exists(path):
        return web.Response(status=404, text="Not found")
    return web.FileResponse(path)

app.router.add_get('/file/{file_id}', stream)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(e):
    await e.reply("Send me any file (up to 2GB) - I'll give a direct link.")

@bot.on(events.NewMessage(func=lambda e: e.document or e.video or e.audio))
async def file_handler(e):
    m = await e.reply("⏳ Uploading...")
    f = e.document or e.video or e.audio
    path = f"temp/{e.id}_{f.id}"
    await bot.download_file(f, path)
    file_id = str(f.id)
    file_map[file_id] = path
    url = f"{BASE_URL}/file/{file_id}"
    await m.edit(f"✅ Link: {url} (valid 1 hour)")

async def main():
    await bot.start()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()
    print(f"Bot ready. Web server on {BASE_URL}")
    await bot.run_until_disconnected()

asyncio.run(main())
