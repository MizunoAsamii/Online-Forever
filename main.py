import asyncio
import json
import os
import time

import requests
import websockets

TOKEN = os.getenv("TOKEN")
STATUS = "online"  # online / dnd / idle

# Trạng thái tùy chỉnh
STATUS_TEXT = "."
EMOJI_NAME = "MahiruDumA"
EMOJI_ID = "1520485215645073680"
EMOJI_ANIMATED = True

REFRESH_SECONDS = 1800  # đặt lại trạng thái mỗi 30 phút

if not TOKEN:
    print("Chưa có biến môi trường TOKEN!", flush=True)
    exit()

headers = {"Authorization": TOKEN}

r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=15)
if r.status_code != 200:
    print("Invalid token!", flush=True)
