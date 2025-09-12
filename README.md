<h1 align="center">🤖 SCP: Roleplay Server Startup Discord Bot</h1>

<p align="center">
  <a href="https://github.com/UZOMPAZ/SCP-Roleplay-Server-Startup-Discord-Bot/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-VOSL%202.3-7b42f6?style=flat&logoColor=white" alt="License">
  </a>
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/discord.py-2.3.2-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord.py">
  <img src="https://img.shields.io/badge/Bot%20Version-2.1.3-brightgreen?style=flat&logo=github" alt="Bot Version">
  <img src="https://img.shields.io/github/stars/zompazy/SCP-Roleplay-Server-Startup-Discord-Bot?style=flat&logo=github" alt="Stars">
  <img src="https://img.shields.io/github/issues/zompazy/SCP-Roleplay-Server-Startup-Discord-Bot?style=flat&logo=github" alt="Issues">
</p>

<p align="center">
  A feature-rich Discord bot to display <b>Server Start Ups</b>, <b>Shutdowns</b>, and <b>Startup Polls</b> for a custom SCP:Roleplay Server.<br>
  Built with <a href="https://discordpy.readthedocs.io">discord.py</a>.
</p>

---

## 📑 Table of Contents

* [✨ Features](#-features)
* [📦 Installation](#-installation)
* [⚙️ Configuration](#️-configuration)
* [🛠️ Commands](#️-commands)
* [📝 Notes](#-notes)
* [🚀 Roadmap](#-roadmap)
* [📜 License](#-license)
* [💡 Credits](#-credits)

---

## ✨ Features

* 🟢 **SSU Command** – Start and log server startups with rich embeds.
* 🔴 **SSD Command** – Safely shut down the currently running server.
* 📊 **SSUP Polls** – Create timed startup polls with automatic updates.
* ⏳ **Auto-updating countdowns** (refreshes every minute).
* 📂 **Persistent storage** for SSU history and active polls.
* ⚙️ **In-Discord configuration** (`!config`) for channels and roles.
* 🛡️ **Role-based permissions** to restrict sensitive commands.

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ZOMPAZY/SCP-Roleplay-Server-Startup-Discord-Bot.git
cd SCP-Roleplay-Server-Startup-Discord-Bot
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> If `requirements.txt` doesn’t exist:

```bash
pip install discord.py
```

### 4. Configure the Bot

Run the bot once to auto-generate `config.json`, then edit it:

```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "ssu_channel_id": null,
  "ssd_channel_id": null,
  "ssup_channel_id": null,
  "guild_id": null,
  "allowed_roles": []
}
```

### 5. Run the Bot

```bash
python main.py
```

---

## ⚙️ Configuration

* `!config` → View current settings in an embed.
* `!config ssu_channel <channel_id>` or `!config ssu_channel #channel_name` → Set SSU channel.
* `!config ssd_channel <channel_id>` → Set SSD channel.
* `!config ssup_channel <channel_id>` → Set SSUP channel.
* `!config add_role @RoleName` → Allow role to use commands.
* `!config remove_role @RoleName` → Remove role access.
* `!config clear_roles` → Allow everyone to use commands.

---

## 🛠️ Commands

| Command                                            | Description                      | Example                                                       |
| -------------------------------------------------- | -------------------------------- | ------------------------------------------------------------- |
| `!SSU [server_name] [@host] [@ping] [description]` | Start a server and log it        | `!SSU [Test Server] [@john] [@everyone] [Restart for update]` |
| `!SSD`                                             | Shut down the current server     | `!SSD`                                                        |
| `!SSUP [server_name] [time] [@role] [description]` | Create a server startup poll     | `!SSUP [Test Server] [45min] [@everyone] [Update rollout]`    |
| `!USSUP <message_id>`                              | Manually refresh a poll          | `!USSUP 123456789`                                            |
| `!config`                                          | Configure channels/roles         | `!config ssu_channel 123456789`                               |
| `!help`                                            | Display all commands in an embed | -                                                             |

---

## 📝 Notes

* Always use **square brackets `[ ]`** for arguments.
* Time formats supported: `45min`, `1d30min`, `1w`, `1mo`, `1y3mo2w6d25min`.
* Logs are stored in `logs/` and last session data in `last_ssu.json`.

---

## 🚀 Roadmap

Coming soon...

---

## 📜 License

Distributed under the **VOSL 2.3 / Veilaris Open Source License 2.3**. See [`LICENSE`](LICENSE) for details.

---

## 💡 Credits

Veilaris / zюяатн zуяяан
Developed for **SCP: Roleplay Custom Server Community**
Built with ❤️ using **Python** + **discord.py**
