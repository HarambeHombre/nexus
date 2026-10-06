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
    print(f"✅ Bot successfully online! Logged in as: {bot.user.name}")

@bot.command(name="halostats")
async def get_stats(ctx, *, gamertag: str):
    cleaned_gt = gamertag.strip()
    print(f"\n--- 📥 NEW COMMAND RECEIVED ---")
    print(f"Target Gamertag: '{cleaned_gt}'")
    
    await ctx.send(f"🛰️ Connecting to Xbox Live for **{cleaned_gt}**...")

    openxbl_key = os.getenv("OPENXBL_KEY", "").strip()

    headers = {
        "X-Authorization": openxbl_key,
        "Accept": "application/json"
    }
    
    try:
        domain_part = "api" + "." + "xbl" + "." + "io"
        encoded_gt = urllib.parse.quote(cleaned_gt)
        profile_url = f"https://{domain_part}/v2/friends/search/{encoded_gt}"
        
        print(f"🚀 STEP 1: Hitting profile search endpoint...")
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code == 401:
            await ctx.send("❌ OpenXBL API Key is unauthorized. Check your Railway configuration variables.")
            return
            
        data = response.json()
        
        # Navigate content tree structural layer safely
        content_block = data.get("content", data)
        profile_users = content_block.get("profileUsers", [])
        
        if not profile_users or len(profile_users) == 0:
            await ctx.send("❌ Gamertag not found. Double-check the spelling and try again.")
            return
            
        # FIX: Target index 0 directly to unpack the user account block from the list!
        user_data = profile_users[0]
        xuid = user_data.get("id")
        print(f"🎯 Found target XUID: {xuid}")
        
        # Query Title History
        title_url = f"https://{domain_part}/v2/player/titlehistory/{xuid}"
        print(f"🚀 STEP 2: Querying Title History...")
        
        title_res = requests.get(title_url, headers=headers).json()
        
        title_content = title_res.get("content", title_res)
        titles = title_content.get("titles", [])
        
        # Filter explicitly for Halo MCC title sequence numbers
        mcc_data = next((t for t in titles if str(t.get("titleId")) == "1144039928"), None)

        if not mcc_data:
            await ctx.send("❌ This player hasn't played Halo: MCC on this Xbox account.")
            return

        # Step 3: Extract visual profile layout items
        settings = user_data.get("settings", [])
        avatar_url = next((s.get("value") for s in settings if s.get("id") == "AppDisplayPicRaw"), None)

        achieve_info = mcc_data.get("achievement", {})
        gamerscore = achieve_info.get("currentGamerscore", 0)
        progress = achieve_info.get("progressPercentage", 0)
        print(f"Stats Parsed -> GamerScore: {gamerscore} | Total Progress: {progress}%")

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
        print(f"✅ Success: Card layout delivered safely to server.")

    except Exception as e:
        print(f"🚨 CRITICAL SYSTEM FAILURE: {e}")
        await ctx.send("❌ Failed to process statistic query. Please check server logs.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
