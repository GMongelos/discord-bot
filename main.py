import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio

from dotenv import load_dotenv
from constants import VOICE_DISCONNECT_CHOICES
from random import choice


# Load environment variables
load_dotenv()
ffmpeg_exec = os.getenv('FFMPEG_PATH')
discord_token = os.getenv('DISCORD_TOKEN')

# Validate environment variables
if not ffmpeg_exec or not discord_token:
    raise ValueError("FFMPEG_PATH or DISCORD_TOKEN not set! Check your .env file.")

# Create an instance of the bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Global queue and state variables
queue = asyncio.Queue()
current_voice_client = None
is_playing = False


async def play_next(interaction):
    global is_playing, current_voice_client

    while not queue.empty():
        is_playing = True

        # Get the next song from the queue
        url = await queue.get()

        if not interaction.user.voice:
            await interaction.followup.send("You need to join a voice channel first!")
            continue

        channel = interaction.user.voice.channel

        # Connect if not already connected
        if not current_voice_client or not current_voice_client.is_connected():
            current_voice_client = await channel.connect()

        # Extract audio with yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info['title']

        # Play audio using FFmpeg
        current_voice_client.play(
            discord.FFmpegPCMAudio(
                audio_url,
                executable=ffmpeg_exec,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            ),
            after=lambda e: print('Playback done:', e)
        )

        await interaction.followup.send(f"🎵 R E P R O D U C I E N D O: {title}")

        # Wait until audio finishes
        while current_voice_client.is_playing():
            await asyncio.sleep(1)

        queue.task_done()

    # Disconnect after playing
    await current_voice_client.disconnect()
    current_voice_client = None
    is_playing = False
    await interaction.followup.send(choice(VOICE_DISCONNECT_CHOICES))


@bot.tree.command(name="play", description="Reproducime ésta")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()

    # Add the song to the queue
    await queue.put(url)
    await interaction.followup.send("Agregado a la lista")

    # Start playback if not already playing
    if not is_playing:
        await play_next(interaction)


@bot.tree.command(name="skip", description="Salteame ésta")
async def skip(interaction: discord.Interaction):
    global current_voice_client
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await interaction.response.send_message("Salteando")


@bot.tree.command(name="queue", description="Observame ésta")
async def view_queue(interaction: discord.Interaction):
    if queue.empty():
        await interaction.response.send_message("La cola está vacía")
    else:
        songs = list(queue._queue)
        queue_list = "\n".join(f"{i+1}. {url}" for i, url in enumerate(songs))
        await interaction.response.send_message(f"Información sobre la C O L A:\n{queue_list}")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    print("Commands synced")


if __name__ == '__main__':
    bot.run(discord_token)
