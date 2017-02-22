# Websocket to facilitate communication between AHGraR-web and AHGraR-server
import asyncio
import websockets
import configparser
import socket

async def handle(websocket, path):
    # Receive request from web application
    web_request = await websocket.recv()
    # Forward request to AHGraR gateway
    connection = socket.create_connection(('localhost', gateway_port))
    send_data(connection, web_request)
    gateway_reply = receive_data(connection)
    websocket.send(gateway_reply)



def send_data(connection, reply):
    # Add length of message to header
    message = str(len(reply)) + "|" + reply
    connection.sendall(message.encode())

    # Receive data coming in from server or user


def receive_data(self, connection):
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
        msg += msg_chunk
        # Subtract the actual length of the received message from the overall message length
        msg_length -= len(msg_chunk)
    return (msg)
# Read AHGraR config file
ahgrar_config = configparser.ConfigParser()
try:
    ahgrar_config.read('AHGraR_config.txt')
except OSError:
    print("Config file not found. Exiting.")
    exit(3)
# Connect to gateway, running on the same server (i.e. localhost)
gateway_port = int(ahgrar_config['AHGraR_Server']['port'])
start_server = websockets.serve(handle, 'localhost', 6000)
class_var = "ABC"
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()