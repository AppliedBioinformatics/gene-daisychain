# AHGraR Server module
# Performs computational tasks
# Only connected to AHGraR gateway module, not directly to user app
# Can handle multiple requests in parallel (not sequential)
import configparser
from Server.Server_Admin_Socket import AHGraRAdminServer,AHGraRAdminServerThread
from Server.Server_Query_Socket import AHGraRQueryServerThread,AHGraRQueryServer
import threading
import shutil
import os
import subprocess
import time
from random import choice
from neo4j.v1 import GraphDatabase, basic_auth




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
    except KeyError as e:
        print(e)
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
    # Start to listen for connections for socket connnections
    try:
        server_admin_listen = 'localhost' if ahgrar_config['AHGraR_Server']['only_local_admin'] == "True" else '0.0.0.0'
        server_query_listen = 'localhost' if ahgrar_config['AHGraR_Server']['only_local_query'] == "True" else '0.0.0.0'
        server_admin_port = int(ahgrar_config['AHGraR_Server']['server_admin_port'])
        server_query_port = int(ahgrar_config['AHGraR_Server']['server_query_port'])
    except KeyError:
        print("Config file error: Can not retrieve server listening address and/or port")
        exit(3)
    # Fire up socket for admin connections
    admin_socket = AHGraRAdminServerThread((server_admin_listen,server_admin_port), AHGraRAdminServer)
    admin_socket_thread = threading.Thread(target=admin_socket.serve_forever, daemon=True)
    admin_socket_thread.start()
    # Fire up socket for query connections
    query_socket = AHGraRQueryServerThread((server_query_listen, server_query_port), AHGraRQueryServer)
    query_socket_thread= threading.Thread(target=query_socket.serve_forever, daemon=True)
    query_socket_thread.start()
    print("Listening for admin connections at "+server_admin_listen+":"+str(server_admin_port))
    print("Listening for query connections at " + server_query_listen + ":" + str(server_query_port))
    print("Type 'exit' to shutdown server")
    # Keep server running
    while True:
        user_input = input(">: ").strip()
        if user_input == "exit": break
    print("Please wait for server shutdown")
    admin_socket.socket.shutdown(0)
    admin_socket.socket.close()
    admin_socket_thread.join(2)
    query_socket.socket.shutdown(0)
    query_socket.socket.close()
    query_socket_thread.join(2)
    exit(0)