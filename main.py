import asyncio
import json
import os
import time

import requests
import websockets

TOKEN = os.getenv("TOKEN")
STATUS = "online"  # online / dnd / idle
CUSTOM_STATUS = ""  # Để trống nếu không muốn custom status
USE_EMOJI = 

if not TOKEN:
    print("Chưa có biến môi trường TOKEN!")
    exit()

headers = {"Authorization": TOKEN}

r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=15)
if r.status_code != 200:
    print("Invalid token!")
    exit()

print("Đăng nhập thành công!")

activity = {
    "name": "Custom Status",
    "type": 4,
    "state": CUSTOM_STATUS,
    "id": "custom"
}

if USE_EMOJI:
    activity["emoji"] = {
        "name": "",
        "id": "1520485215645073680",
        "animated": True
    }

async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                await ws.send(json.dumps({"op": 1, "d": None}))

        hb_task = asyncio.create_task(heartbeat())

        identify = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": STATUS,
                    "afk": False,
                    "activities": [activity] if (CUSTOM_STATUS or USE_EMOJI) else []
                }
            }
        }
        await ws.send(json.dumps(identify))

        try:
            while True:
                msg = await ws.recv()
                json.loads(msg)
        except Exception as e:
            print("Connection lost, reconnecting...", e)
        finally:
            hb_task.cancel()

while True:
    try:
        asyncio.run(discord_gateway())
    except Exception as e:
        print("Error:", e)
    time.sleep(5)
