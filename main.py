import os
import discord
import functools
import random
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=1495300890821791824)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild.")
    except Exception as e:
        print(f"Failed to sync: {e}")
    print("Bot Ready")


import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone







bot.run(os.getenv("DISCORD_TOKEN"))