import os
import asyncio
import asyncpg
from pyrogram import Client, filters

# ================= 配置区 =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
DATABASE_URL = os.getenv("DATABASE_URL")

# 初始化 Pyrogram Client
bot = Client("tg_drive_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("👋 欢迎使用私人 TG 网盘！\n直接向我发送任何文件，我会将它们记录在 Neon 中。\n发送 /list 查看你的文件。")

@bot.on_message(filters.document | filters.video | filters.audio)
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

@bot.on_message(filters.command("list"))
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

@bot.on_message(filters.command("get") & filters.private)
async def get_file(client, message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ 请提供提取码。例如: `/get file_id`")
        return
    
    file_id = message.command[1]
    try:
        await message.reply_cached_media(file_id)
    except Exception as e:
        await message.reply_text("❌ 文件提取失败，可能 file_id 无效。")

# ================= 主入口 =================
async def main():
    await init_db()
    await bot.start()
    print("Bot is successfully running on Render!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())