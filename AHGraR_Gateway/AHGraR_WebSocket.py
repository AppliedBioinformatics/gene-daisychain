import asyncio
import websockets
import configparser
import socket

async def handle(websocket, path):
    web_request = await websocket.recv()
    connection = socket.create_connection(
        (ahgrar_config['AHGraR_Gateway']['ip'], ahgrar_config['AHGraR_Gateway']['port']))
    reply = "PMINFO"
    message = str(len(reply)) + "|" + reply
    connection.sendall(message.encode())
    reply = connection.recv(1024).decode()
    connection.close()
    greeting = "Hello {}!".format(reply)
    await websocket.send(greeting)
    print("> {}".format(greeting))

ahgrar_config = configparser.ConfigParser()
try:
    ahgrar_config.read('AHGraR_config.txt')
except OSError:
    print("Config file not found. Exiting.")
    exit(3)
start_server = websockets.serve(handle, '0.0.0.0', 7687)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()