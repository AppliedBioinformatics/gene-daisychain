import asyncio
import websockets
import configparser
import socket

async def handle(websocket, path):
    web_request = await websocket.recv()
    connection = socket.create_connection(
        (ahgrar_config['AHGraR_Gateway']['ip'], ahgrar_config['AHGraR_Gateway']['port']))
    if web_request == "Project_List":
        reply = "PMINFO"
        # Web request for species list: "SL_projID"
    elif web_request.startswith("SL"):
        proj_id = web_request.split("_")[1]
        reply = "PAQURY_LIST_"+proj_id+"_SPECIES"
    else:
        reply = ""
    message = str(len(reply)) + "|" + reply
    connection.sendall(message.encode())
    gw_reply = receive_data(connection)
    print(gw_reply)
    connection.close()
    await websocket.send(gw_reply)


# Receive data coming in from gateway
def receive_data(connection):
    # First, determine the length of the message
    # The message has a header containing the length
    # of the actual message:
    # e.g. 123|Data bla bla
    # First, receive data bytewise until the "|" is detected
    msg_header = ""
    while True:
        incoming_data = connection.recv(1).decode()
        if incoming_data == "|":
            break
        else:
            msg_header += incoming_data
    # Store length of the actual message
    msg_length = int(msg_header)
    # Start to build up the actual message
    msg = ""
    # Receive chunks of data until the length of the received message equals the expected length
    while msg_length > 0:
        # Receive a max. of 1024 bytes
        rcv_length = 1024 if msg_length >= 1024 else msg_length
        msg_chunk = connection.recv(rcv_length).decode()
        # Subtract the actual length of the received message from the overall message length
        msg_length -= len(msg_chunk)
        msg += msg_chunk
    return(msg)

ahgrar_config = configparser.ConfigParser()
try:
    ahgrar_config.read('AHGraR_config.txt')
except OSError:
    print("Config file not found. Exiting.")
    exit(3)
start_server = websockets.serve(handle, '0.0.0.0', 7687)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()