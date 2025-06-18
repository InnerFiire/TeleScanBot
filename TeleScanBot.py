import asyncio
import json
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes


#                        TeleScanBot
#| Feature                    | Status                                        |
#| -------------------------- | --------------------------------------------- |
#| Keyword matching           | Works in all joined groups                  |
#| Only new messages per run  | In-memory deduplication prevents duplicates |
#| Keyword management via bot | `/add`, `/remove`, `/list`                  |
#| Interval control           | `/interval 1800` (30 min) def is 60min                   |
#| No duplicate alerts        | Per session (while script is running)       |


# ---------------- SETTINGS ----------------
api_id = 123456  # ← Replace with your own API ID
api_hash = 'your_api_hash'  # ← Replace with your API hash
bot_token = 'your_bot_token'  # ← Replace with your BotFather token
user_id = 123456789  # ← Your Telegram user ID

message_limit = 100
days_back = 2
keyword_file = 'keywords.json'
settings_file = 'settings.json'


print("🚀 Starting TeleScanBot - Group Keyword Monitor")
client = TelegramClient('session_name', api_id, api_hash)
bot = Bot(token=bot_token)

#In-memory deduplication storage
processed_messages = set()


# ---------------- WORDS ----------------
def load_keywords():
    try:
        with open(keyword_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_keywords(keywords):
    with open(keyword_file, 'w') as f:
        json.dump(keywords, f)


# ---------------- SETTINGS ----------------
def load_settings():
    try:
        with open(settings_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"interval": 3600}

def save_settings(settings):
    with open(settings_file, 'w') as f:
        json.dump(settings, f)


# ---------------- Group Scan ----------------
async def scan_groups():
    keywords = load_keywords()
    if not keywords:
        return

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            messages = await client.get_messages(dialog.id, limit=message_limit)

            for message in messages:
                if not message.text or not message.date:
                    continue
                if message.date < cutoff_date:
                    continue

                msg_key = (dialog.id, message.id)
                if msg_key in processed_messages:
                    continue  # Already alerted
                processed_messages.add(msg_key)

                lower_text = message.text.lower()
                if any(k.lower() in lower_text for k in keywords):
                    link = f"https://t.me/c/{str(dialog.id)[4:]}/{message.id}" if str(dialog.id).startswith('-100') else '🔗 Няма линк'
                    alert = (
                        f"📢 Съвпадение в: {dialog.name}\n"
                        f"🕒 {message.date.strftime('%Y-%m-%d %H:%M')}\n"
                        f"💬 {message.text[:100]}...\n"
                        f"{link}"
                    )
                    await bot.send_message(chat_id=user_id, text=alert)


# ---------------- Periodic check----------------
async def periodic_check():
    while True:
        try:
            await scan_groups()
        except Exception as e:
            await bot.send_message(chat_id=user_id, text=f"❌ Грешка: {str(e)}")
        interval = load_settings().get("interval", 3600)
        print(f"⏱️ Следваща проверка след {interval} секунди.")
        await asyncio.sleep(interval)


# ---------------- Bot Commands ----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != user_id:
        return
    await update.message.reply_text("🤖 Ботът е активен и следи за съвпадения.")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != user_id:
        return
    if not context.args:
        await update.message.reply_text("❗ Използвай: /add <дума>")
        return
    word = context.args[0].lower()
    keywords = load_keywords()
    if word in keywords:
        await update.message.reply_text(f"🔁 '{word}' вече е добавена.")
    else:
        keywords.append(word)
        save_keywords(keywords)
        await update.message.reply_text(f"✅ Добавена: '{word}'")

async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != user_id:
        return
    if not context.args:
        await update.message.reply_text("❗ Използвай: /remove <дума>")
        return
    word = context.args[0].lower()
    keywords = load_keywords()
    if word in keywords:
        keywords.remove(word)
        save_keywords(keywords)
        await update.message.reply_text(f"🗑️ Премахната: '{word}'")
    else:
        await update.message.reply_text(f"❌ Няма такава дума: '{word}'")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != user_id:
        return
    keywords = load_keywords()
    if not keywords:
        await update.message.reply_text("📭 Няма добавени ключови думи.")
    else:
        await update.message.reply_text("📋 Ключови думи:\n- " + "\n- ".join(keywords))

async def interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != user_id:
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ Използвай: /interval <секунди>\nПример: /interval 1800")
        return
    interval = int(context.args[0])
    settings = load_settings()
    settings["interval"] = interval
    save_settings(settings)
    await update.message.reply_text(f"✅ Интервал обновен на {interval} секунди.")


# ---------------- MAIN ----------------
async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Влязъл си като: {me.first_name} ({me.id})")
    await bot.send_message(chat_id=user_id, text="🤖 Ботът стартира и следи за ключови думи.")

    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("remove", remove_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("interval", interval_command))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        await periodic_check()
    finally:
        await app.stop()
        await app.shutdown()


# ---------------- START ----------------
if __name__ == "__main__":
    asyncio.run(main())
