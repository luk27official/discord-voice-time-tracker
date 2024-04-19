#!/usr/bin/env python3

import discord
from discord.ext import tasks
from discord.ext import commands
from dateutil.relativedelta import relativedelta as rd

from dotenv import load_dotenv
from datetime import datetime
import os
import json

# Initialize the Discord client
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/gstat, /ustat"))
    await bot.tree.sync()
    my_background_task.start()


@tasks.loop(seconds=60)
async def my_background_task():
    await bot.wait_until_ready()

    active_members = []
    disconnected_members = []

    print(f"Checking for active members... It is {datetime.now()}")

    # open a file with the current users
    with open("current_users.json", "r+") as f:
        # first, read the users from the JSON
        # looks like this: [{"id": "123", "startTime": "2021-09-01T12:00:00"}]
        file_content = f.read()
        if not file_content:
            current_members = []
        current_members = json.loads(file_content)

        # get the active members
        for guild in bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.voice.deaf or member.voice.self_deaf: # ignore deafened users
                        continue
                    active_members.append(member)

        # check if the user is already in the list
        for member in active_members:
            # if the user is not in the list, add it
            if member.id not in [user["id"] for user in current_members]:
                current_members.append({"id": member.id, "startTime": str(datetime.now())})

        # remove the users that are not in the active_members list (they left the voice channel)
        for user in current_members:
            if user["id"] not in [member.id for member in active_members]:
                current_members.remove(user)
                disconnected_members.append(user)

        # write the users back to the file
        f.seek(0)
        f.truncate()
        json.dump(current_members, f)

    # write the disconnected members to a file, calculate the time spent in the voice channel
    # the final format is [{ "id": "123", "totalTime": 100 }]
    with open("disconnected_users.json", "r+") as f:
        file_content = f.read()
        if not file_content:
            final_users = []
        final_users = json.loads(file_content)

        for member in disconnected_members:
            startTime = datetime.fromisoformat(member["startTime"])
            timeSpent = datetime.now() - startTime
            # find the user in the list and update the time
            found = False

            for user in final_users:
                if user["id"] == member["id"]:
                    user["totalTime"] += timeSpent.total_seconds()
                    found = True
                    break

            if not found:
                final_users.append({"id": member["id"], "totalTime": timeSpent.total_seconds()})

        # write the users back to the file
        f.seek(0)
        f.truncate()
        json.dump(final_users, f)


@bot.tree.command(name="ustat", description="Get user statistics")
async def user_statistics(interaction: discord.Interaction):
    id_to_search = interaction.user.id

    # get the stats for a user given in the command
    with open("disconnected_users.json", "r") as f:
        users = json.load(f)
        for user in users:
            if user["id"] == id_to_search:
                fmt = "{0.days} days {0.hours} hours {0.minutes} minutes"

                await interaction.response.send_message(
                    f"User <@!{id_to_search}> has spent {fmt.format(rd(seconds=int(user["totalTime"])))} in voice channels.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
                return

    await interaction.response.send_message(f"User <@!{id_to_search}> has not spent any time in voice channels.", allowed_mentions=discord.AllowedMentions.none())


@bot.tree.command(name="gstat", description="Get the top10 for the whole server")
async def guild_statistics(interaction: discord.Interaction):
    with open("disconnected_users.json", "r") as f:
        users = json.load(f)

        # sort the users by the total time spent in voice channels
        users = sorted(users, key=lambda x: x["totalTime"], reverse=True)

        # get the top 10 users
        top10 = users[:10]

        # get the top 10 users
        top10_users = []
        fmt = "{0.days} days {0.hours} hours {0.minutes} minutes"
        for user in top10:
            top10_users.append(f'<@!{user["id"]}>: {fmt.format(rd(seconds=int(user["totalTime"])))}')

        final_msg = "Top 10 active users:\n" + "\n".join([f"{i+1}. {user}" for i, user in enumerate(top10_users)])

        await interaction.response.send_message(final_msg, allowed_mentions=discord.AllowedMentions.none())


def main():
    # python3 -m pip install discord.py python-dotenv python-dateutil
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
