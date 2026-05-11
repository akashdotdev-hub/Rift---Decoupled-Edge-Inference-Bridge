import discord
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# 1. Replace with your Discord Token from the Developer Portal
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# 2. Replace with your latest Cloudflare Tunnel URL (End with /api/generate)
OLLAMA_URL = 'https://repair-python.trycloudflare.com/api/generate'

# 3. We are using phi3 because it fits perfectly in the RTX 3050 VRAM
MODEL_NAME = 'phi3'

# Set up Discord permissions
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'--- Gateway Online ---')
    print(f'Logged in as: {client.user}')
    print(f'Targeting Model: {MODEL_NAME}')
    print(f'Tunnel Route: {OLLAMA_URL}')
    print(f'-----------------------')

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Listen for the trigger command
    if message.content.startswith('!radiant'):
        user_prompt = message.content.replace('!radiant', '').strip()
        
        if not user_prompt:
            await message.channel.send("Type a prompt! Example: `!radiant What is the best Omen smoke for Ascent A?`")
            return

        # Start the typing indicator so you know the cloud-to-home link is active
        async with message.channel.typing():
            try:
                payload = {
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "stream": False
                }
                
                # Asynchronous request to your home GPU via Cloudflare
                async with aiohttp.ClientSession() as session:
                    async with session.post(OLLAMA_URL, json=payload, timeout=60) as response:
                        if response.status == 200:
                            data = await response.json()
                            ai_reply = data.get('response', 'Empty response from AI.')
                            
                            # FIX: Discord Limit Protection (Max 2000 chars)
                            # This prevents the "400 Bad Request" if the AI is too talkative
                            if len(ai_reply) > 1900:
                                safe_reply = ai_reply[:1900] + "\n\n*(Message truncated due to Discord length limits)*"
                            else:
                                safe_reply = ai_reply
                                
                            await message.channel.send(f" **Radiant-AI:**\n{safe_reply}")
                        
                        elif response.status == 500:
                            await message.channel.send(" **GPU Deadlock (500):** Your RTX 3050 rejected the request. Try restarting Ollama on Windows.")
                        else:
                            await message.channel.send(f" **Tunnel Error ({response.status}):** Check your Cloudflare URL.")
                            
            except Exception as e:
                await message.channel.send(f" **Connection Failed:** AWS could not reach your home network. Error: {str(e)}")

client.run(DISCORD_TOKEN)
