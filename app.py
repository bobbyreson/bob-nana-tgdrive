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

print("=== 正在准备启动程序 ===")

# 初始化客户端，增加 ipv6=False 防止部分服务器网络卡死
bot = Client(
    "tg_drive_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    ipv6=False
)

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    print(f"收到 /start 指令，来自用户: {user_id}")
    await message.reply_text(f"🎉 机器人连接成功！你的 User ID 是：`{user_id}`")

async def web_handler(request):
    return web.Response(text="Bot is running!")

async def main():
    print("1. 正在启动 Web 服务...")
    server = web.Server(web_handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("2. Web 服务启动成功！")
    
    print("3. 正在向 Telegram 发起长连接 (bot.start)...")
    try:
        await bot.start()
        print(">>> 4. 成功连接到 Telegram 服务器！机器人已经活了！ <<<")
    except Exception as e:
        print(f"!!! 连接 Telegram 失败，错误原因: {e}")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
