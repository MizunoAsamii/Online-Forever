import asyncio
import json
import os
import time

import requests
import websockets

TOKEN = os.getenv("TOKEN")
STATUS = "online"  # online / dnd / idle

# Trạng thái tùy chỉnh
STATUS_TEXT = "\u200b"
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
    exit()

print("Đăng nhập thành công!", flush=True)

activity = {
    "name": "Custom Status",
    "type": 4,
    "state": STATUS_TEXT,
    "id": "custom",
    "emoji": {
        "name": EMOJI_NAME,
        "id": EMOJI_ID,
        "animated": EMOJI_ANIMATED,
    },
}


def set_custom_status():
    payload = {
        "custom_status": {
            "text": STATUS_TEXT,
            "emoji_id": EMOJI_ID,
            "emoji_name": EMOJI_NAME,
        }
    }
    try:
        rs = requests.patch(
            "https://discord.com/api/v9/users/@me/settings",
            headers=headers,
            json=payload,
            timeout=15,
        )
        print("Đặt trạng thái:", rs.status_code, flush=True)
    except Exception as e:
        print("Lỗi đặt trạng thái:", e, flush=True)


async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri, max_size=None) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                await ws.send(json.dumps({"op": 1, "d": None}))

        async def refresh():
            while True:
                await asyncio.sleep(REFRESH_SECONDS)
                await asyncio.get_running_loop().run_in_executor(
                    None, set_custom_status
                )

        hb_task = asyncio.create_task(heartbeat())
        refresh_task = None

        identify = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc",
                },
                "presence": {
                    "status": STATUS,
                    "afk": False,
                    "activities": [activity],
                },
            },
        }
        await ws.send(json.dumps(identify))

        await asyncio.sleep(3)
        await asyncio.get_running_loop().run_in_executor(None, set_custom_status)
        refresh_task = asyncio.create_task(refresh())

        try:
            while True:
                msg = await ws.recv()
                json.loads(msg)
        except Exception as e:
            print("Connection lost, reconnecting...", e, flush=True)
        finally:
            hb_task.cancel()
            if refresh_task:
                refresh_task.cancel()


while True:
    try:
        asyncio.run(discord_gateway())
    except Exception as e:
        print("Error:", e, flush=True)
    time.sleep(30)
