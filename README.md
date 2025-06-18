# 🛰️ TeleScanBot

**TeleScanBot** is a Telegram monitoring bot that scans all your group chats (using your user account) for specific keywords and sends real-time alerts to you through a personal bot.

Perfect for tracking job offers, promotions, sales, or any topic you're interested in — across all the groups you're part of.

---

## 🚀 Features

✅ Uses **Telethon** to read messages from all your Telegram groups  
✅ Uses **Bot API** to send alerts and accept your commands  
✅ In-memory **deduplication** — no duplicate alerts per session  
✅ Bot commands to manage keywords and scan intervals  
✅ Lightweight, fast, no database needed  
✅ Customizable with ease

---

## 🛠️ Requirements

- Python 3.8+
- Telegram account
- Telegram Bot (from [@BotFather](https://t.me/BotFather))
- API credentials from [my.telegram.org](https://my.telegram.org)

### 📦 Install dependencies:

```bash
pip install telethon python-telegram-bot --upgrade
python watcher.py
```

## ✅ Commands
| Command               | What it does                           |
| --------------------- | -------------------------------------- |
| `/start`              | Confirms bot is running                |
| `/add <keyword>`      | Adds a keyword to monitor              |
| `/remove <keyword>`   | Removes a keyword                      |
| `/list`               | Shows all active keywords              |
| `/interval <seconds>` | Sets scan interval (default: 3600 sec) |
