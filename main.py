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

    headers = {"X-Authorization": os.getenv("OPENXBL_KEY", "")}
    
    try:
        # Step 1: Use the precise URL encoding for OpenXBL Gamertag Search
        # Clean up any accidental spaces from user input
        cleaned_gt = gamertag.strip()
        profile_url = f"https://xbl.io{cleaned_gt}"
        
        response = requests.get(profile_url, headers=headers)
        profile_res = response.json()
        
        profile_users = profile_res.get("profileUsers", [])
        if not profile_users:
            await ctx.send("❌ Gamertag not found. Double check the spelling.")
            return
            
        user_data = profile_users[0] # Grab the first matched user profile array block
        xuid = user_data.get("id")
        
        # Step 2: Query Title History for Halo: MCC (Title ID: 1144039928)
        title_url = f"https://xbl.io{xuid}"
        title_res = requests.get(title_url, headers=headers).json()
        
        titles = title_res.get("titles", [])
        mcc_data = next((t for t in titles if str(t.get("titleId")) == "1144039928"), None)

        if not mcc_data:
            await ctx.send("❌ This player hasn't played Halo: MCC on this Xbox account.")
            return

        # Step 3: Extract profile image and achievement stats safely
        settings = user_data.get("settings", [])
        avatar_url = next((s.get("value") for s in settings if s.get("id") == "AppDisplayPicRaw"), None)

        achieve_info = mcc_data.get("achievement", {})
        gamerscore = achieve_info.get("currentGamerscore", 0)
        progress = achieve_info.get("progressPercentage", 0)

        # Step 4: Construct and send the card
        embed = discord.Embed(
            title=f"Spartan Record: {cleaned_gt}",
            color=discord.Color.green()
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
            
        embed.add_field(name="GamerScore Earned", value=f"{gamerscore:,}", inline=True)
        embed.add_field(name="Total Progress", value=f"{progress}% Completed", inline=True)
        embed.set_footer(text="Data retrieved via OpenXBL Relay")
        
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"Error occurred: {e}")
        await ctx.send("❌ Failed to process statistics data. Check server logs.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
