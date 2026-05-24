import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = int(os.environ.get("PORT", 8080))

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
web_app = web.Application()
file_map = {}

async def handle_stream(request):
    file_id = request.match_info.get('file_id')
    path = file_map.get(file_id)
    if not path or not os.path.exists(path):
        return web.Response(status=404, text="Not found")
    return web.FileResponse(path)

web_app.router.add_get('/file/{file_id}', handle_stream)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Send any file (up to 2GB) and I'll give a direct link.")

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    m = await message.reply("Downloading...")
    file = message.document or message.video or message.audio
    path = f"temp/{file.file_id}"
    await client.download_media(message, file_name=path)
    file_id = file.file_id
    file_map[file_id] = path
    url = f"{BASE_URL}/file/{file_id}"
    await m.edit(f"Link: {url}")

async def main():
    await app.start()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Bot started. Web on {BASE_URL}")
    await asyncio.Event().wait()  # keep running

if __name__ == "__main__":
    asyncio.run(main())
