import asyncio
import websockets
import json

userID = "computer"

async def connectToSocket(uri):
    async with websockets.connect(uri) as websocket:
        i = 0
        while i < 8:
            score = int(input("please input score: "))
            payload = json.dumps({
                'type': 'answer',
                'userID': userID,
                'score': score,
                'optionIndex': 1,
            })

            await websocket.send(payload)
            i += 1
        # res = await websocket.read_message()
        # print(f"get response {res}")

# challenge = input("please input challenge: ")
challenge = "nursing"
asyncio.get_event_loop().run_until_complete(
    # connectToSocket(f'wss://miutech.cloud:8991/ws/battle?user={userID}&challenge={challenge}')
    connectToSocket(f'ws://localhost:8000/ws/battle?user={userID}&challenge={challenge}')
)
