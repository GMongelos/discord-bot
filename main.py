import os

import discord
from discord.ext import commands
import yt_dlp
import asyncio

from dotenv import load_dotenv
from constants import VOICE_DISCONNECT_CHOICES
from random import choice


load_dotenv()

# Create an instance of the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def play_audio(interaction: discord.Interaction, url: str):

    if not interaction.user.voice:
        await interaction.followup.send("You need to join a voice channel first!")
        return

    channel = interaction.user.voice.channel
    voice_client = await channel.connect()

    # Set up yt-dlp options to extract audio
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']

    # Stream the audio using the voice client
    voice_client.play(
        discord.FFmpegPCMAudio(
            url2,
            executable=os.getenv('FFMPEG_PATH'),
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        ),
        after=lambda e: print('done', e)
    )

    await interaction.followup.send(f"R E P R O D U C I E N D O: {info['title']}")

    # Wait until the audio finishes playing
    while voice_client.is_playing():
        await asyncio.sleep(1)

    # Disconnect after playback
    await voice_client.disconnect()
    await interaction.followup.send(choice(VOICE_DISCONNECT_CHOICES))


# Define the slash command to play audio from a YouTube link
@bot.tree.command(name="play", description="Reproducime ésta")
async def play(interaction: discord.Interaction, url: str):

    await interaction.response.defer()  # Acknowledge the command
    await play_audio(interaction, url)


# Event to sync commands when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()


if __name__ == '__main__':
    bot.run(token=os.getenv("DISCORD_TOKEN"))
