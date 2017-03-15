import asyncio
import websockets

async def hello():
    async with websockets.connect('ws://146.118.99.190:7687') as websocket:

        name = input("Query:   ")
        await websocket.send(name)
        print("> {}".format(name))

        greeting = await websocket.recv()
        print("< {}".format(greeting))

asyncio.get_event_loop().run_until_complete(hello())