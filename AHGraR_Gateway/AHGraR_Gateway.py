# AHGraR Gateway module
# Connects AHGraRWeb or AHGraRCmd to Server_old module
# Can handle multiple requests in parallel (not sequential)
import socketserver
import threading
import configparser
import socket

# Define server functionality
class GatewayServer(socketserver.BaseRequestHandler):
    def setup(self):
        self.ahgrar_config = configparser.ConfigParser()
        try:
            self.ahgrar_config.read('AHGraR_config_new.txt')
        except OSError:
            exit(3)
    # Handling user requests
    # Two categories:
    # (1.) Project management (list, create, delete projects)
    # (2.) Project access (query, add data....)
    # Requests for (1.) start with PM
    # Requests for (2.) start with PA
    def handle(self):
        # Receive command from user app
        user_request = self.receive_data(self.request)
        # Connect to AHGraR-Server_old
        server_connection = socket.create_connection(
            (self.ahgrar_config['AHGraR_Server']['ip'], self.ahgrar_config['AHGraR_Server']['port']))
        # And forward user_request
        self.send_data_server(server_connection, user_request)
        # Receive server reply
        server_reply = self.receive_data(server_connection)
        # And send server reply back to user app
        self.send_data_user(server_reply)


    # Send data to user client
    def send_data_user(self, reply):
        # Ensure reply is in string format
        reply = str(reply)
        # Add length of message to header
        message = str(len(reply))+"|"+reply
        self.request.sendall(message.encode())
        #self.request.sendall((str(len(reply)) + "|").encode())
        # Split reply into chunks of length 512
        #reply_chunks = [reply[i:i + 512] for i in range(0, len(reply), 512)]
        #for reply_chunk in reply_chunks:
        #    self.request.sendall(reply_chunk.encode())




    #
    # # Receive data from user client
    # def receive_data_user(self, connection):
    #     msg_length = ""
    #     while True:
    #         incoming_data = connection.recv(1).decode()
    #         if incoming_data == "|":
    #             break
    #         else:
    #             msg_length += incoming_data
    #     msg_length = int(msg_length)
    #     msg = ""
    #     while msg_length > 0:
    #         rcv_length = 1024 if msg_length >= 1024 else msg_length
    #         msg_length -= rcv_length
    #         msg += connection.recv(rcv_length).decode()
    #         print(msg_length)
    #     return (msg)


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

    def send_data_server(self, connection, reply):
        # Ensure reply is in string format
        reply = str(reply)
        # Add length of message to header
        message = str(len(reply)) + "|" + reply
        connection.sendall(message.encode())


# Create a new thread for every new connection
class GatewayServerThread(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    # Open config file
    ahgrar_config = configparser.ConfigParser()
    try:
        ahgrar_config.read('AHGraR_config_new.txt')
    except OSError:
        print("Config file not found. Exiting.")
        exit(3)
    server_address = ahgrar_config['AHGraR_Server']['ip']
    server_port = int(ahgrar_config['AHGraR_Server']['port'])
    # Set up Gateway server
    gateway_address = ahgrar_config['AHGraR_Gateway']['ip']
    gateway_port = int(ahgrar_config['AHGraR_Gateway']['port'])
    gateway_server = GatewayServerThread((gateway_address,gateway_port), GatewayServer)
    gw_server_thread = threading.Thread(target=gateway_server.serve_forever)
    gw_server_thread.daemon = True
    gw_server_thread.start()
    # Keep server running
    # TODO: Add routine to allow proper server start and shutdown
    while True:
        user_input = input(">: ").strip()
        if user_input == "exit": break
    gateway_server.socket.close()
    exit(0)
