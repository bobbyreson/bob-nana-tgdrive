# 🌟 必须加在最顶部的补丁，解决 Python 3.14 触发的事件循环报错
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import asyncpg
from pyrogram import Client, filters
from aiohttp import web

# ================= 配置区 =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
DATABASE_URL = os.getenv("DATABASE_URL")
PORT = int(os.getenv("PORT", 10000))
OWNER_ID = int(os.getenv("OWNER_ID", 0))

bot = Client("tg_drive_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
auth = filters.user(OWNER_ID)

# ================= 数据库操作 =================
async def init_db():
    print("Connecting to Neon DB...")
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            file_name TEXT,
            file_id TEXT UNIQUE,
            file_size INT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.close()
    print("Database initialized.")

# ================= Bot 逻辑 =================
@bot.on_message(filters.command("start") & auth)
async def start_cmd(client, message):
    await message.reply_text("👋 欢迎主人！安全锁已激活，现在我只为你一个人服务。\n发送 /list 查看你的文件。")

@bot.on_message((filters.document | filters.video | filters.audio) & auth)
async def handle_file(client, message):
    file_obj = getattr(message, message.media.value)
    file_name = getattr(file_obj, 'file_name', f"Unnamed_{message.media.value}")
    file_id = file_obj.file_id
    file_size = file_obj.file_size

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            'INSERT INTO files (file_name, file_id, file_size) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING',
            file_name, file_id, file_size
        )
        await message.reply_text(f"✅ 文件已入库！\n**文件名:** `{file_name}`\n**大小:** `{file_size / 1024 / 1024:.2f} MB`")
    except Exception as e:
        await message.reply_text(f"❌ 存储失败: {e}")
    finally:
        await conn.close()

@bot.on_message(filters.command("list") & auth)
async def list_files(client, message):
    conn = await asyncpg.connect(DATABASE_URL)
    records = await conn.fetch('SELECT id, file_name, file_id FROM files ORDER BY id DESC LIMIT 10')
    await conn.close()

    if not records:
        await message.reply_text("📭 你的网盘是空的。")
        return

    text = "📂 **你最近上传的文件:**\n\n"
    for r in records:
        text += f"📄 {r['file_name']}\n提取码: `/get {r['file_id']}`\n\n"
    
    await message.reply_text(text)

@bot.on_message(filters.command("get") & filters.private & auth)
async def get_file(client, message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ 请提供提取码。例如: `/get file_id`")
        return
    
    file_id = message.command[1]
    try:
        await message.reply_cached_media(file_id)
    except Exception as e:
        await message.reply_text("❌ 文件提取失败，可能 file_id 无效。")

# ================= Web 服务 (应付 Render) =================
async def web_handler(request):
    return web.Response(text="✅ Telegram Drive Bot is running perfectly with Python 3.14 patch!")

# ================= 主入口 =================
async def main():
    print("--- 正在初始化数据库 ---")
    await init_db()
    
    print("--- 正在启动 Web 服务 ---")
    server = web.Server(web_handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print("--- 正在连接 Telegram 服务器 (Bot.start) ---")
    await bot.start()
    print("--- Bot 启动成功，正在等待消息 ---")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"!!! 致命错误: {e}")
        # 为了防止程序因为这个错误立刻关闭，我们让它睡一会儿
        import time
        time.sleep(300)
