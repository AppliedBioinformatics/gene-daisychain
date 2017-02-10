# AHGraR Server module
# Performs computational tasks
# Only connected to AHGraR gateway module, not directly to user app
# Can handle multiple requests in parallel (not sequential)
import configparser
import socketserver
import subprocess
import threading
from neo4j.v1 import GraphDatabase, basic_auth
from Server.Project_management.Project_Delete import DeleteProject
from Server.Project_management.Project_Create import CreateProject
from Server.Project_management.Project_Info import ProjectInfo
from Server.Project_access.Task_Management import TaskManagement
from Server.Project_access.File_Management import FileManagement
from Server.Project_access.DB_Builder import DBBuilder
from Server.Project_access.DB_Runner import DBRunner

# Define server functionality
class AHGraRServer(socketserver.BaseRequestHandler):

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
        # Handle request: Either project management (PM) or project access (PA)
        if request[:2] == "PM":
            self.project_management(request[2:])
        elif request[:2] == "PA":
            self.project_access(request[2:])
        else:
            self.send_data("-1")
        return

    # Project management: Create or delete project, return status or list all projects
    def project_management(self, request):
        # Split up user request
        # Some commands may contain additional "_", e.g. in file names.
        # These are exchanged to "\t" before being send via the socket connection
        # Here, these tabs are exchanged back to underscores
        user_request = [item.replace("\t", "_") for item in request.split("_")]
        # Create a new project?
        if user_request[0] == "CREA" and len(user_request)==2:
            create_project = CreateProject(user_request[1], self.ahgrar_config["AHGraR_Server"]["neo4j_path"], self.get_db_conn(), self.send_data)
            create_project.run()
        # Delete a project?
        if user_request[0] == "DELE" and len(user_request) == 2 and user_request[1].isdigit():
            delete_project = DeleteProject(user_request[1], self.get_db_conn(), self.send_data)
            delete_project.run()
        # Retrieve name, id and status of one or all projects
        # ProjectInfo returns info about all or one projects, depending on if a specific project_id was transmitted
        if user_request[0] == "INFO":
            project_info = ProjectInfo(user_request[1] if len(user_request) == 2 else None, self.get_db_conn(), self.send_data)
            project_info.run()
        # Else Return "-1" to indicate invalid syntax
        else:
            self.send_data("-1")

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
        if user_request[0] == "TASK" and len(user_request) >= 4:
            task_manager.evaluate_user_request(user_request[1:])
        if user_request[0] == "FILE" and 3 <= len(user_request) <= 7:
            # Initialize file manager
            file_manager = FileManagement(self.get_db_conn(), task_manager, self.send_data)
            # Evaluate user request
            file_manager.evaluate_user_request(user_request[1:])
            # Close file manager connection to main-db
            file_manager.close_connection()
        if user_request[0] == "BULD":
            # Initialize build manager
            build_manager = DBBuilder(self.get_db_conn(), task_manager, self.send_data)
            # Evaluate user request
            build_manager.evaluate_user_request(user_request[1:])
            # Close file manager connection to main-db
            build_manager.close_connection()
        if user_request[0] == "DABA":
            # Initialize Database runner, providing start/stop/restart/status functionality
            db_runner = DBRunner(self.get_db_conn(), self.send_data)
            # Evaluate user request
            db_runner.evaluate_user_request(user_request[1:])
        else:
            self.send_data("-2")
        # Close task manager connection to main-db
        task_manager.close_connection()

    def get_db_conn(self):
        driver = GraphDatabase.driver("bolt://localhost:"+self.ahgrar_config["AHGraR_Server"]["proj_db_port"],
                                      auth=basic_auth(self.ahgrar_config["AHGraR_Server"]["proj_db_login"], self.ahgrar_config["AHGraR_Server"]["proj_db_pw"]))
        return(driver.session())

    # Send data to gateway
    def send_data(self, reply):
        # Ensure reply is in string format
        reply = str(reply)
        # Add length of message to header
        message = str(len(reply)) + "|" + reply
        self.request.sendall(message.encode())

    # Receive data from gateway
    def receive_data(self, connection):
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


# Create a new thread for every new connection
class AHGraRServerThread(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    # This server hosts the Neo4j databases and
    # performs all computations
    # A main Neo4j DB contains information about the projects
    # AHGraR_Gateway is the only computer making a direct connection to AHGraR_Server
    # Load config file
    ahgrar_config = configparser.ConfigParser()
    try:
        ahgrar_config.read('AHGraR_config.txt')
    except OSError:
        print("Config file not found. Exiting.")
        exit(3)
    # TODO Check if main database is running
    #subprocess.run(["./AHGraR_main_db/bin/neo4j", "start"])
    # Update ports usable for project graph dbs
    # Retrieve ports from config file
    port_list = ahgrar_config['AHGraR_Server']['proj_graph_db_ports']
    ports = port_list.split(",")
    port_numbers = []
    for port in ports:
        if "-" in port:
            port = port.split("-")
            port_numbers.extend(list(range(int(port[0]), int(port[1]) + 1)))
        else:
            port_numbers.append(int(port))
    # Open connection to AHGraR-DB
    main_db_conn = GraphDatabase.driver("bolt://localhost:"+ahgrar_config["AHGraR_Server"]["proj_db_port"],
                                      auth=basic_auth(ahgrar_config["AHGraR_Server"]["proj_db_login"], ahgrar_config["AHGraR_Server"]["proj_db_pw"])).session()
    # All ports are child nodes of Port_Manager-node
    main_db_conn.run("MERGE (:Port_Manager)")
    # Add ports to database, set status of newly added ports to "inactive"
    # Status of ports already in database remains unchanged
    main_db_conn.run("UNWIND $ports as port MATCH (portMngr:Port_Manager) "
                "MERGE (portMngr)-[:has_port]->(p:Port{nr:port}) "
                "ON CREATE SET p.status = 'inactive' "
                , {"ports": port_numbers, "inactive": "inactive"})
    # Remove ports from database that are not in config file
    # except those that are listed as active
    main_db_conn.run("MATCH (p:Port) WHERE NOT (p.nr IN ($ports)) AND NOT (p.status = 'active') DETACH DELETE (p)  ",
                {"ports": port_numbers})
    main_db_conn.close()
    server_address = ahgrar_config['AHGraR_Server']['ip']
    server_port = int(ahgrar_config['AHGraR_Server']['port'])
    server = AHGraRServerThread((server_address,server_port), AHGraRServer)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    # Keep server running
    # TODO: Add routine to allow proper server start and shutdown
    while True:
        user_input = input(">: ").strip()
        if user_input == "exit": break
    server.socket.close()
    exit(0)