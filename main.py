import os
import urllib.parse
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
    cleaned_gt = gamertag.strip()
    await ctx.send(f"🛰️ Connecting to Xbox Live for **{cleaned_gt}**...")

    headers = {
        "X-Authorization": os.getenv("OPENXBL_KEY", "").strip(),
        "Accept": "application/json"
    }
    
    try:
        # Step 1: Query Search Endpoint using OpenXBL's official path format
        encoded_gt = urllib.parse.quote(cleaned_gt)
        profile_url = f"https://api.xbl.io/v2/search/{encoded_gt}"
        
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code == 401:
            await ctx.send("❌ OpenXBL API Key is unauthorized. Check your Railway configuration variables.")
            return
            
        data = response.json()
        
        # Pull profileUsers out of the root content block
        content_block = data.get("content", data)
        profile_users = content_block.get("profileUsers", [])
        
        if not profile_users or len(profile_users) == 0:
            await ctx.send("❌ Gamertag not found. Double-check the spelling and try again.")
            return
            
        # Target index 0 explicitly to unpack the user profile block
        user_data = profile_users[0]
        xuid = user_data.get("id")
        
        # Step 2: Query Title History explicitly adding the correct structural slashes
        title_url = f"https://xbl.io{xuid}"
        
        title_res = requests.get(title_url, headers=headers).json()
        title_content = title_res.get("content", title_res)
        
        titles = title_content.get("titles", [])
        mcc_data = next((t for t in titles if str(t.get("titleId")) == "1144039928"), None)

        if not mcc_data:
            await ctx.send("❌ This player hasn't played Halo: MCC on this Xbox account.")
            return

        # Step 3: Extract visual profile elements out of the nested settings array
        settings = user_data.get("settings", [])
        avatar_url = next((s.get("value") for s in settings if s.get("id") == "AppDisplayPicRaw"), None)

        achieve_info = mcc_data.get("achievement", {})
        gamerscore = achieve_info.get("currentGamerscore", 0)
        progress = achieve_info.get("progressPercentage", 0)

        # Step 4: Output the complete Spartan Profile card
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
        print(f"Error occurred during API execution: {e}")
        await ctx.send("❌ Failed to process statistic query. Please check server logs.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
