import asyncio
import websockets
import json

userID = "computer"

async def connectToSocket(uri):
    async with websockets.connect(uri) as websocket:
        i = 0
        while i < 5:
            score = int(input("please input score: "))
            payload = json.dumps({
                'type': 'answer',
                'userID': userID,
                'score': score,
                'option_index': None,
            })

            await websocket.send(payload)
            i += 1
        # res = await websocket.read_message()
        # print(f"get response {res}")

challenge = input("please input challenge: ")
asyncio.get_event_loop().run_until_complete(
    connectToSocket(f'ws://localhost:8000/api/battle?user={userID}&challenge={challenge}')
)