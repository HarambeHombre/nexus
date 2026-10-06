import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command(name="halostats")
async def get_stats(ctx, *, gamertag: str):
    await ctx.send(f"Searching database for **{gamertag}**...")
    # Add your stat logic here

# Pulls the token safely from Render's Environment Variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
