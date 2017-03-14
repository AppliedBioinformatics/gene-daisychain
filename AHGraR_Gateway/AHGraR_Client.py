import asyncio
import websockets
import configparser
import socket

class AHGraRClient():

    def __init__(self, ahgrar_server_ip, ahgrar_server_query_port):
        self.ahgrar_server_ip = ahgrar_server_ip
        self.ahgrar_server_query_port = ahgrar_server_query_port

    async def handle(self, websocket, path):
        web_request = await websocket.recv()
        print(web_request)
        connection = socket.create_connection((self.ahgrar_server_ip, self.ahgrar_server_query_port))
        message = str(len(web_request)) + "|" + web_request
        connection.sendall(message.encode())
        server_reply = self.receive_data(connection)
        print(server_reply)
        connection.close()
        await websocket.send(server_reply)


    # Receive data coming in from server
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
            # Subtract the actual length of the received message from the overall message length
            msg_length -= len(msg_chunk)
            msg += msg_chunk
        return(msg)

if __name__ == '__main__':
    ahgrar_config = configparser.ConfigParser()
    try:
        ahgrar_config.read('AHGraR_config.txt')
    except OSError:
        print("Config file not found. Exiting.")
        exit(3)
    ahgrar_client = AHGraRClient(ahgrar_config['AHGraR_Server']['server_ip'],
                                 ahgrar_config['AHGraR_Server']['server_query_port'])
    start_server = websockets.serve(ahgrar_client.handle, ahgrar_config['AHGraR_Client']['client_ip'],
                                    ahgrar_config['AHGraR_Client']['client_query_port'])
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
