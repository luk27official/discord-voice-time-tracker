# Discord voice time-tracker

A Discord bot that tracks total time spent in the voice channels and stores the data in JSON files.

## Installation

1. Create a Discord bot with Administrator permissions
2. Create `.env` file with `DISCORD_TOKEN=<your_token>`
3. Invite the bot to your server with Administrator permissions
4. `pip install discord.py python-dotenv python-dateutil` or `pip install -r requirements.txt`
5. `python bot.py`

## Usage

Type `/ustat` for personal stats or `/gstat` for top10 users in your Discord channel.