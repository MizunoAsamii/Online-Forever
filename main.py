import asyncio
import json
import os
import time

import requests
import websockets

TOKEN = os.getenv("TOKEN")

# Các thông số này được truyền từ workflow
STATUS = os.getenv("STATUS", "online")  # online / idle / dnd
STATUS_TEXT = os.getenv("STATUS_TEXT", "")
EMOJI_NAME = os.getenv("EMOJI_NAME", "")
EMOJI_ID = os.getenv("EMOJI_ID", "")
EMOJI_ANIMATED = os.getenv("EMOJI_ANIMATED", "false").lower() == "true"

REFRESH_SECONDS = 1800  # đặt lại trạng thái mỗi 30 phút

if not TOKEN:
    print("Chưa có biến môi trường TOKEN!", flush=True)
    exit()

headers = {"Authorization": TOKEN}

r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=15)
if r.status_code != 200:
    print("Lỗi kiểm tra token. Mã:", r.status_code, flush=True)
    exit()

print("Đăng nhập thành công!", flush=True)

HAS_STATUS = bool(STATUS_TEXT or EMOJI_NAME)

activity = {
    "name": "Custom Status",
    "type": 4,
    "id": "custom",
}
if STATUS_TEXT:
    activity["state"] = STATUS_TEXT
if EMOJI_NAME:
    activity["emoji"] = {
        "name": EMOJI_NAME,
        "id": EMOJI_ID or None,
        "animated": EMOJI_ANIMATED if EMOJI_ID else False,
    }


def set_custom_status():
    if not HAS_STATUS:
        return
    payload = {
        "custom_status": {
            "text": STATUS_TEXT or None,
            "emoji_id": EMOJI_ID or None,
            "emoji_name": EMOJI_NAME or None,
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
                    "activities": [activity] if HAS_STATUS else [],
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
