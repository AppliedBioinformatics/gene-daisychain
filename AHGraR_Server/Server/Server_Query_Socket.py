# Define server functionality
from Server.Project_access.Task_Management import TaskManagement
from Server.Project_access.Query_Management import QueryManagement
import configparser
import socketserver
from neo4j.v1 import GraphDatabase, basic_auth

class AHGraRQueryServer(socketserver.BaseRequestHandler):

    def setup(self):
        # Load AHGraR config file
        self.ahgrar_config = configparser.ConfigParser()
        try:
            self.ahgrar_config.read('AHGraR_config.txt')
        except OSError:
            print("Config file not found. Exiting.")
            exit(3)

    # Handling user requests
    def handle(self):
        # Receive command from gateway
        request = self.receive_data(self.request)
        if request[:2] == "PA":
            self.project_access(request[2:])
        else:
            self.send_data("Invalid Request")
        return


    def project_access(self, request):
        # Split up user request
        # Some commands may contain additional "_", e.g. in file names.
        # These are exchanged to "\t" before being send via the socket connection
        # Here, these tabs are exchanged back to underscores
        user_request = [item.replace("\t", "_") for item in request.split("_")]
        # Initialize task manager
        task_manager = TaskManagement(self.get_db_conn(), self.send_data)
        print(user_request)
        # Some queries/user requests are handled by the task_manager.
        # These are: Job status and job deletion queries and retrieval of results
        if user_request[0] == "QURY":
            # Initialize query manager
            query_manager = QueryManagement(self.get_db_conn(), self.send_data)
            # Evaluate user request, query manager returns data, doesn't send data anywhere
            self.send_data(query_manager.evaluate_user_request(user_request[1:]))
        else:
            self.send_data("-2")
        # Close task manager connection to main-db
        task_manager.close_connection()

    def get_db_conn(self):
        with open("main_db_access", "r") as pw_file:
            driver = GraphDatabase.driver("bolt://localhost:"+self.ahgrar_config["AHGraR_Server"]["main_db_bolt_port"],
                                          auth=basic_auth("neo4j",pw_file.read()),encrypted=False)
        return(driver.session())

    # Send data to gateway
    def send_data(self, reply):
        # Ensure reply is in string format
        reply = str(reply)
        # Add length of message to header
        message = str(len(reply)) + "|" + reply
        self.request.sendall(message.encode("utf-8", errors="ignore"))
        # Split reply into chunks of length 512
        #reply_chunks = [reply[i:i+512] for i in range(0, len(reply), 512)]
        #for reply_chunk in reply_chunks:
         #   self.request.sendall(reply_chunk.encode())



    # Receive data from gateway
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


# Create a new thread for every new connection
class AHGraRQueryServerThread(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
