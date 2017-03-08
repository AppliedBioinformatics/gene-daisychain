# AHGraR Server module
# Performs computational tasks
# Only connected to AHGraR gateway module, not directly to user app
# Can handle multiple requests in parallel (not sequential)
import configparser
import socketserver
import threading
import shutil
import os
import subprocess
import time
from random import choice
from neo4j.v1 import GraphDatabase, basic_auth
from Server.Project_management.Project_Delete import DeleteProject
from Server.Project_management.Project_Create import CreateProject
from Server.Project_management.Project_Info import ProjectInfo
from Server.Project_access.Task_Management import TaskManagement
from Server.Project_access.File_Management import FileManagement
from Server.Project_access.DB_Builder import DBBuilder
from Server.Project_access.DB_Runner import DBRunner
from Server.Project_access.Query_Management import QueryManagement

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
        if user_request[0] == "QURY":
            # Initialize query manager
            query_manager = QueryManagement(self.get_db_conn(), self.send_data)
            # Evaluate user request
            query_manager.evaluate_user_request(user_request[1:])
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
        self.request.sendall(message.encode())
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
class AHGraRServerThread(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    # Main function to start up the Server-side of AHGraR
    # One Neo4j instance is used as internal database to manage individual projects ("main db")
    # Each project has an independent Neo4j instance to host project data
    # The main db can only be access from localhost
    # Load config file
    ahgrar_config = configparser.ConfigParser()
    ahgrar_config.read('AHGraR_config.txt')
    # Check paths
    try:
        # Check path to MCL
        if not os.path.isfile(ahgrar_config['AHGraR_Server']['mcl_path']):
            print("Invalid MCL path")
            exit(3)
        # Check path to Neo4j
        # Look for Neo4j binary to ensure that neo4j_path is pointing to the uppermost directory
        if not os.path.isfile(os.path.join(ahgrar_config['AHGraR_Server']['neo4j_path'], "bin", "neo4j")):
            print("Invalid Neo4j path")
            exit(3)
        # Check path to blast+
        # Look for blastn binary and makeblastdb
        if not os.path.isfile(os.path.join(ahgrar_config['AHGraR_Server']['blast+_path'], "blastn")):
            print("Invalid blast+ path - can't find blastn")
            exit(3)
        if not os.path.isfile(os.path.join(ahgrar_config['AHGraR_Server']['blast+_path'], "makeblastdb")):
            print("Invalid blast+ path - can't find makeblastdb")
            exit(3)
    except KeyError:
        print("Config file error: Can not retrieve path names")
        exit(3)
    # Check if main db is set up
    if not os.path.exists("main_db"):
        # If not, initiate a new Neo4j instance as main db
        print("Main DB does not exist\nCreating a new main DB instance")
        # Create a new Neo4j copy
        try:
            shutil.copytree(ahgrar_config['AHGraR_Server']['neo4j_path'], "main_db")
        except (KeyError, OSError):
            print("Error while initializing main db")
            print("Could not create database copy")
            exit(3)
        # Edit Neo4j config
        # Change some lines in config file, collect all lines, changed and unchanged in a list
        neo4j_conf_content = []
        try:
            with open(os.path.join("main_db", "conf", "neo4j.conf"), "r") as conf_file:
                for line in conf_file:
                    if line == "#dbms.connector.bolt.listen_address=:7687\n":
                        neo4j_conf_content.append("dbms.connector.bolt.listen_address=:" + ahgrar_config['AHGraR_Server']['main_db_bolt_port'] + "\n")
                    elif line == "#dbms.connector.http.listen_address=:7474\n":
                        neo4j_conf_content.append("dbms.connector.http.listen_address=:" + ahgrar_config['AHGraR_Server']['main_db_http_port'] + "\n")
                    elif line == "dbms.connector.https.enabled=true\n":
                        neo4j_conf_content.append("dbms.connector.https.enabled=false\n")
                    else:
                        neo4j_conf_content.append(line)
        except (KeyError, OSError):
            print("Error while initializing main db")
            print("Could not create database copy")
            exit(3)
        # Write lines to a new file to replace the original config file
        with open(os.path.join("main_db", "conf", "neo4j.conf"), "w") as conf_file:
            for line in neo4j_conf_content:
                conf_file.write(line)
        # Generate a random password for main db access
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        neo4j_pw = ''.join(choice(chars) for _ in range(50))
        # Write password to file
        with open("main_db_access", "w") as file:
            file.write(neo4j_pw)
        try:
            subprocess.run([os.path.join("main_db", "bin", "neo4j-admin"),
                    "set-initial-password", neo4j_pw], check=True, stdout=subprocess.PIPE, stderr =subprocess.PIPE)
        except subprocess.CalledProcessError as err:
            print("Error while initializing main db")
            print(err.stdout)
            print(err.stderr)
            exit(3)
    # Check status of main db
    status = subprocess.run([os.path.join("main_db", "bin", "neo4j"), "status"], stdout=subprocess.PIPE)
    if status.returncode != 0:
        main_db_start_code = subprocess.run([os.path.join("main_db", "bin", "neo4j"), "start"], stdout=subprocess.PIPE)
        if main_db_start_code.returncode != 0:
            print("Error while starting up main db")
            exit(3)
        # Wait 60 seconds for database to load
        print("Waiting for main db to start")
        time.sleep(60)
        # Check status again
        status = subprocess.run([os.path.join("main_db", "bin", "neo4j"), "status"], stdout=subprocess.PIPE)
        if status.returncode != 0:
            print("Error while starting up main db")
            exit(3)
    print("Main DB is running")

    # Update ports usable for project graph dbs
    # Retrieve ports from config file
    try:
        port_list = ahgrar_config['AHGraR_Server']['project_ports']
    except KeyError:
        print("Config file error: Can not retrieve list of ports for projects")
        exit(3)
    ports = [item.strip() for item in port_list.split(",")]
    port_numbers = []
    for port in ports:
        if "-" in port:
            port = [item.strip() for item in port.split("-")]
            if not port[0].isdigit() or not port[1].isdigit():
                continue
            port_numbers.extend(list(range(int(port[0]), int(port[1]) + 1)))
        else:
            if not port.isdigit():
                continue
            port_numbers.append(int(port))
    # Open connection to AHGraR-DB
    print("Importing available project ports")
    with open("main_db_access", "r") as pw_file:
        main_db_conn = GraphDatabase.driver("bolt://localhost:"+ahgrar_config["AHGraR_Server"]["main_db_bolt_port"],
                                          auth=basic_auth("neo4j", pw_file.read()), encrypted=False).session()
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
    # Start to listen for connections
    try:
        server_address = ahgrar_config['AHGraR_Server']['server_app_ip']
        server_address = "0.0.0.0"
        server_port = int(ahgrar_config['AHGraR_Server']['server_app_port'])
    except KeyError:
        print("Config file error: Can not retrieve server listening address and/or port")
        exit(3)
    server = AHGraRServerThread((server_address,server_port), AHGraRServer)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Listening for incomming connections at "+server_address+":"+str(server_port))
    print("Type 'exit' to shutdown server")
    # Keep server running
    while True:
        user_input = input(">: ").strip()
        if user_input == "exit": break
    server.socket.shutdown(0)
    server.socket.close()
    exit(0)