import asyncio
import websockets

async def hello():
    async with websockets.connect('ws://localhost:6000') as websocket:
        cmd = input("Command?")
        await websocket.send(cmd)
        reply = await websocket.recv()
        print("< {}".format(reply))

asyncio.get_event_loop().run_until_complete(hello())

