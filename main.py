import os
import requests
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
    await ctx.send(f"🛰️ Connecting to Xbox Live for **{gamertag}**...")

    # OpenXBL endpoints to find XUID (Xbox User ID) from Gamertag
    headers = {"X-Authorization": os.getenv("OPENXBL_KEY")}
    
    try:
        # Step 1: Convert Gamertag to Xbox User ID (XUID)
        profile_url = f"https://xbl.io{gamertag}"
        profile_res = requests.get(profile_url, headers=headers).json()
        
        # Grab the profile data block
        profile_data = profile_res.get("profileUsers", [{}])[0]
        xuid = profile_data.get("id")
        
        if not xuid:
            await ctx.send("❌ Gamertag not found. Double check the spelling.")
            return

        # Step 2: Query Title History for Halo: MCC (Title ID: 1144039928)
        title_url = f"https://xbl.io{xuid}"
        title_res = requests.get(title_url, headers=headers).json()
        
        # Look through titles for Halo MCC achievements/time
        titles = title_res.get("titles", [])
        mcc_data = next((t for t in titles if t.get("titleId") == "1144039928"), None)

        if not mcc_data:
            await ctx.send("❌ This player hasn't played Halo: MCC on this Xbox account.")
            return

        # Step 3: Parse and present the data block
        embed = discord.Embed(
            title=f"Spartan Record: {gamertag}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=profile_data.get("settings", [{}])[2].get("value")) # Gamercard image
        embed.add_field(name="GamerScore Earned", value=mcc_data.get("achievement", {}).get("currentGamerscore"), inline=True)
        embed.add_field(name="Progress", value=f"{mcc_data.get('achievement', {}).get('progressPercentage')}% Completed", inline=True)
        
        await ctx.send(embed=embed)

except Exception as e:
        print(f"Error occurred: {e}")
        await ctx.send("❌ Failed to contact UNSC relay. Please try again later.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
