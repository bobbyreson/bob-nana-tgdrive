import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import asyncpg
from pyrogram import Client, filters
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
DATABASE_URL = os.getenv("DATABASE_URL")
PORT = int(os.getenv("PORT", 10000))

# 打印一下看看配置读没读到（注意：不要把敏感信息截图发给别人）
print(f"DEBUG -> API_ID: {API_ID}, BOT_TOKEN length: {len(BOT_TOKEN) if BOT_TOKEN else 0}")

bot = Client("tg_drive_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 基础测试路由（不加 auth 锁）
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    print(f"收到来自用户 {user_id} 的 /start 指令")
    await message.reply_text(f"🎉 机器人连接成功！你的 User ID 是：`{user_id}`")

async def web_handler(request):
    return web.Response(text="Bot is running!")

async def main():
    server = web.Server(web_handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print("正在启动 Telegram 客户端...")
    await bot.start()
    print(">>> Telegram 客户端已成功启动并开始监听消息！<<<")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
