from TikTokApi import TikTokApi
from telethon import TelegramClient, events
import requests
import os
import asyncio
from instaloader import Instaloader, Post
from pytube import YouTube
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

# Your API ID and Hash from Telegram
api_id = '29999447'
api_hash = '97b3a3f3e7655acfa3806f17d19f7f52'

# Persistent session name
session_name = 'bot_session'

# Create the client
client = TelegramClient(session_name, api_id, api_hash)

# Menu content
menu = """
**Bot Menu:**
1. **Spam Stickers:**
   - Command: `/spam <target_username_or_group>`
   - Description: Send spam stickers to the specified user or group.

2. **Download TikTok Video:**
   - Command: `/tiktok <url>`
   - Description: Download a TikTok video using the provided URL.

3. **Download Instagram Video:**
   - Command: `/instagram <url>`
   - Description: Download an Instagram video using the provided URL.

4. **Convert Photo to URL:**
   - Command: `/photourl`
   - Description: Upload a photo and get a URL link.

5. **Download YouTube Video or Audio:**
   - Command: `/youtube <url> <video/audio>`
   - Description: Download a YouTube video or audio using the provided URL.

6. **Show Sticker IDs:**
   - Command: `/showstickers <sticker_set_short_name>`
   - Description: Display all sticker IDs in the specified sticker set.

7. **Menu:**
   - Command: `/menu`
   - Description: Display the bot's feature menu.
"""

async def resolve_target(target):
    try:
        entity = await client.get_entity(target)
        return entity
    except Exception as e:
        print(f"Error resolving target '{target}': {e}")
        return None

async def send_stickers(target, count=1000000):
    sticker_ids = [
        'AAMCBQADFQABZ0hXganlnHsGtdfaiPCnbnzWV70AAtASAAJ_XxhW6X9mnLoRRS8BAAdtAAM2BA',
        'AAMCBQADFQABZ0hXganlnHsGtdfaiPCnbnzWV70AAtASAAJ_XxhW6X9mnLoRRS8BAAdtAAM2BA',
        'AAMCBQADFQABZ0hXganlnHsGtdfaiPCnbnzWV70AAtASAAJ_XxhW6X9mnLoRRS8BAAdtAAM2BA'
    ]
    try:
        peer = await resolve_target(target)
        if not peer:
            return "Invalid target."

        for i in range(count):
            for sticker_id in sticker_ids:
                await client.send_file(peer, sticker_id)
            await asyncio.sleep(2)
        return "Spam sent successfully."
    except Exception as e:
        return f"Error while sending stickers: {e}"

async def download_tiktok_video(url):
    api_endpoint = "https://www.tikwm.com/api/"
    params = {
        "url": url,
        "hd": 1
    }
    try:
        response = requests.get(api_endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "play" in data["data"]:
                return data["data"]["play"]
            else:
                return "Error: Unexpected API response structure."
        else:
            return f"Error: API returned status code {response.status_code}."
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to connect to the API ({e})."

async def download_instagram_content(url):
    try:
        loader = Instaloader()
        shortcode = url.split("/")[-2]
        post = Post.from_shortcode(loader.context, shortcode)

        if post.is_video:
            return post.video_url
        else:
            return post.url
    except Exception as e:
        return f"Error: Failed to download content ({e})."

async def upload_photo(file_path):
    upload_endpoint = "https://api.imgbb.com/1/upload"
    api_key = "c0d32c0ff47fd859e8f40aeee89d0572"
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(upload_endpoint, data={'key': api_key}, files={'image': file})
            if response.status_code == 200:
                return response.json()['data']['url']
            else:
                return None
    except Exception as e:
        print(f"Error uploading photo: {e}")
        return None

async def download_youtube_video(url, format='video'):
    try:
        yt = YouTube(url)
        if format == 'video':
            stream = yt.streams.get_highest_resolution()
        elif format == 'audio':
            stream = yt.streams.filter(only_audio=True).first()
        else:
            return "Invalid format specified."

        output_path = stream.download()
        return output_path
    except Exception as e:
        return f"Error downloading YouTube content: {e}"

@client.on(events.NewMessage(pattern='/spam'))
async def spam_handler(event):
    parts = event.message.text.split(' ')
    if len(parts) < 2:
        await event.reply("Usage: /spam <target_username_or_group>")
        return
    target = parts[1]
    result = await send_stickers(target)
    await event.reply(result)

@client.on(events.NewMessage(pattern='/tiktok'))
async def tiktok_handler(event):
    parts = event.message.text.split(' ')
    if len(parts) < 2:
        await event.reply("Usage: /tiktok <url>")
        return
    url = parts[1]
    video_url = await download_tiktok_video(url)
    if video_url and video_url.startswith("http"):
        await client.send_file(event.chat_id, video_url, caption="Here is your TikTok video!")
    else:
        await event.reply(f"Failed to download TikTok video: {video_url}")

@client.on(events.NewMessage(pattern='/instagram'))
async def instagram_handler(event):
    parts = event.message.text.split(' ')
    if len(parts) < 2:
        await event.reply("Usage: /instagram <url>")
        return
    url = parts[1]
    content_url = await download_instagram_content(url)
    if content_url and content_url.startswith("http"):
        await client.send_file(event.chat_id, content_url, caption="Here is your Instagram content!")
    else:
        await event.reply(f"Failed to download Instagram content: {content_url}")

@client.on(events.NewMessage(pattern='/photourl'))
async def photourl_handler(event):
    if not event.message.file:
        await event.reply("Please send a photo with this command.")
        return
    file_path = await event.message.download_media()
    url = await upload_photo(file_path)
    if url:
        await event.reply(f"Here is your photo URL: {url}")
    else:
        await event.reply("Failed to upload the photo. Please try again.")

@client.on(events.NewMessage(pattern='/youtube'))
async def youtube_handler(event):
    parts = event.message.text.split(' ')
    if len(parts) < 2:
        await event.reply("Usage: /youtube <url> <video/audio>")
        return
    url = parts[1]
    format = 'video' if len(parts) < 3 else parts[2]
    file_path = await download_youtube_video(url, format)
    if file_path and os.path.exists(file_path):
        await client.send_file(event.chat_id, file_path, caption=f"Here is your YouTube {format}!")
        os.remove(file_path)
    else:
        await event.reply(f"Failed to download YouTube content: {file_path}")

@client.on(events.NewMessage(pattern='/showstickers'))
async def show_stickers_handler(event):
    parts = event.message.text.split(' ')
    if len(parts) < 2:
        await event.reply("Usage: /showstickers <sticker_set_short_name>")
        return
    sticker_set_name = parts[1]
    try:
        sticker_set = await client(GetStickerSetRequest(
            stickerset=InputStickerSetShortName(sticker_set_name)
        ))
        stickers = sticker_set.documents
        message = "**Sticker IDs:**\n"
        for sticker in stickers:
            message += f"{sticker.id}\n"
        await event.reply(message)
    except Exception as e:
        await event.reply(f"Error fetching stickers: {e}")

@client.on(events.NewMessage(pattern='/menu'))
async def menu_handler(event):
    await event.reply(menu)

with client:
    client.start()
    print("Bot is running...")
    client.run_until_disconnected()
