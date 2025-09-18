'''
MCLabs Wiki GPT - Discord Bot

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

import os
import requests
import discord
from discord import app_commands
from discord.ext import commands

'''
ENVIRONMENTAL VARIABLES
'''

# Configure Discord intents
intents = discord.Intents.default()
intents.messages = True

# Initialize bot
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Discord bot is ready!")
    await bot.tree.sync()

@bot.tree.command(name="ask", description="Ask WikiGPT!")
async def ask(interaction: discord.Interaction, question: str):
	try:
		# Make API request to the API endpoint and get response
		payload = {"api_token": os.getenv("API_TOKEN"), "question": question, "include_context": "False"}
		response = requests.post(f"https://{os.getenv('RAILWAY_API_DOMAIN')}/query", json=payload)
		data = response.json()
		
		# Respond in Discord
		if response.status_code == 200:
			answer = data.get("answer", "No answer returned.")
			await interaction.response.send_message(content=answer, ephemeral=True)
		else:
			await interaction.response.send_message(content=f"An error has occured while processing your request. Please contact a developer for further assistance!", ephemeral=True)
			print(f"Error {response.status_code}: {data.get('error', 'Unknown error')}")

	except Exception as e:
		await interaction.response.send_message(content=f"An error has occured while processing your request. Please contact a developer for further assistance!", ephemeral=True)
		print(f"Exception: {e}")

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))