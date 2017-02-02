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
            self.ahgrar_config.read('AHGraR_config.txt')
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
        user_request = self.receive_data_user(self.request)
        # Connect to AHGraR-Server_old
        server_connection = socket.create_connection(
            (self.ahgrar_config['AHGraR_Server']['ip'], self.ahgrar_config['AHGraR_Server']['port']))
        # And forward user_request
        self.send_data_server(server_connection, user_request)
        # Receive server reply
        server_reply = self.receive_data_server(server_connection)
        # And send server reply back to user app
        self.send_data_user(server_reply)



    # Send data to user client
    def send_data_user(self, reply):
        # Add length of message to header
        message = str(len(reply))+"|"+reply
        self.request.sendall(message.encode())

    # Receive data from user client
    def receive_data_user(self, connection):
        # First decode the length of the message
        msg_length = ""
        while True:
            incoming_data = connection.recv(1).decode()
            if incoming_data == "|":
                break
            else:
                msg_length += incoming_data
        msg_length = int(msg_length)
        # Then receive the actual message
        msg = connection.recv(msg_length).decode()
        return (msg)

    def receive_data_server(self, connection):
        msg_length = ""
        while True:
            incoming_data = connection.recv(1).decode()
            if incoming_data == "|":
                break
            else:
                msg_length += incoming_data
        msg_length = int(msg_length)
        msg = connection.recv(msg_length).decode()
        return (msg)

    def send_data_server(self, connection, reply):
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
        ahgrar_config.read('AHGraR_config.txt')
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
