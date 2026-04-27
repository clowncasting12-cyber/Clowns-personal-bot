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

class MyView(discord.ui.View)
    @discord.ui.button(Label="Get role", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the button!", ephemeral=True)

@bot.command()
async def Command(ctx):
    view = MyView()
    await ctx.send("Press the button:", view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
