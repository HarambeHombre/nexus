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
    print(f"✅ Bot successfully online! Logged in as: {bot.user.name} (ID: {bot.user.id})")

@bot.command(name="halostats")
async def get_stats(ctx, *, gamertag: str):
    cleaned_gt = gamertag.strip()
    print(f"\n--- 📥 NEW COMMAND RECEIVED ---")
    print(f"User: {ctx.author} (ID: {ctx.author.id})")
    print(f"Target Gamertag: '{cleaned_gt}'")
    
    await ctx.send(f"🛰️ Connecting to Xbox Live for **{cleaned_gt}**...")

    # Fetching keys safely
    bot_token_exists = "Yes" if os.getenv("DISCORD_BOT_TOKEN") else "No"
    openxbl_key = os.getenv("OPENXBL_KEY", "").strip()
    openxbl_key_exists = "Yes" if openxbl_key else "No"
    
    print(f"Environment Verification -> DISCORD_BOT_TOKEN loaded: {bot_token_exists} | OPENXBL_KEY loaded: {openxbl_key_exists}")

    headers = {
        "X-Authorization": openxbl_key,
        "Accept": "application/json"
    }
    
    try:
        # Step 1: URL Encode the gamertag and build search path
        encoded_gt = urllib.parse.quote(cleaned_gt)
        profile_url = f"https://xbl.io{encoded_gt}"
        
        print(f"🚀 STEP 1: Hitting profile search endpoint...")
        print(f"Target URL: {profile_url}")
        
        response = requests.get(profile_url, headers=headers)
        print(f"HTTP Response Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ Error: OpenXBL API key returned 401 Unauthorized.")
            await ctx.send("❌ OpenXBL API Key is unauthorized. Check your Railway configuration variables.")
            return
            
        data = response.json()
        print(f"Raw Search JSON Payload Received: {data}")
        
        # Navigate content tree structural layer
        content_block = data.get("content", data)
        profile_users = content_block.get("profileUsers", [])
        print(f"Extracted 'profileUsers' element array: {profile_users}")
        
        if not profile_users or len(profile_users) == 0:
            print(f"⚠️ Search warning: No user objects populated for target string.")
            await ctx.send("❌ Gamertag not found. Double-check the spelling and try again.")
            return
            
        # Unpacking targeted block array index 0
        user_data = profile_users[0]
        xuid = user_data.get("id")
        print(f"🎯 Found target XUID: {xuid}")
        
        # Step 2: Build target history URL path string
        title_url = f"https://xbl.io{xuid}"
        print(f"🚀 STEP 2: Querying Title History...")
        print(f"Target URL: {title_url}")
        
        title_res = requests.get(title_url, headers=headers).json()
        print(f"Raw Title JSON Payload Received: {title_res}")
        
        title_content = title_res.get("content", title_res)
        titles = title_content.get("titles", [])
        
        # Filter explicitly for Halo MCC title sequence numbers
        mcc_data = next((t for t in titles if str(t.get("titleId")) == "1144039928"), None)
        print(f"Extracted Halo MCC Title Block: {mcc_data}")

        if not mcc_data:
            print(f"⚠️ Search warning: Player found, but account has never run Halo MCC retail build.")
            await ctx.send("❌ This player hasn't played Halo: MCC on this Xbox account.")
            return

        # Step 3: Extract visual profile layout items
        settings = user_data.get("settings", [])
        avatar_url = next((s.get("value") for s in settings if s.get("id") == "AppDisplayPicRaw"), None)
        print(f"Extracted Avatar URL target: {avatar_url}")

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
        import traceback
        print(traceback.format_exc())
        await ctx.send("❌ Failed to process statistic query. Please check server logs.")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
