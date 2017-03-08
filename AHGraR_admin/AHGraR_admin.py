# Local admin access to AHGraR server
# Must be run on the same host than AHGraR Server
# Provides functionality to create and delete projects
# Add files to a project and build a projects graph database
# from these files.
import configparser
import os
import socket

def print_options():
    print("(1) to list available projects")
    print("(2) to create a new project")
    print("(3) to add/remove data from a project")
    print("(4) to build a projects database")
    print("(5) to delete a project")
    print("(0) to exit")


def send_data(connection, reply):
    # Add length of message to header
    message = str(len(reply)) + "|" + reply
    connection.sendall(message.encode())

# Receive data coming in from server
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


def list_projects(maindb_conn):
    send_data(maindb_conn, "PMINFO")
    proj_list = receive_data(maindb_conn)
    print(20*"#")
    print("Available projects: ")
    print(20 * "#")
    print("\t".join(["Name", "ID", "Status"]))
    print(20 * "-")
    print(proj_list)


def create_project(maindb_conn):
    print("Enter name for new project")
    print("Enter '0' to cancel")
    proj_name = input("[Create]>: ").strip()
    if proj_name == "0":
        return
    # Remove any special characters from future project name
    proj_name = "".join(char for char in proj_name if char.isalnum())
    if proj_name:
        send_data(maindb_conn, "PMCREA_"+proj_name)
        new_proj_id = receive_data(maindb_conn)
        print("Created new project "+proj_name+ " with ID "+new_proj_id)
    else:
        maindb_conn.close()
        print("Invalid project name")


def change_project_files(maindb_conn):
    print("Change files")


def build_project_db(maindb_conn):
    print("Build")




def delete_project(maindb_conn):
    clear_console()
    list_projects(maindb_conn)
    print("Enter ID of project to delete it")
    print("Enter '0' to cancel")
    proj_id = input("[Delete]>: ").strip()
    if proj_id == "0" or not proj_id.isdigit():
        return
    print("Deleting project with ID "+proj_id)
    print("To continue, enter 'delete'")
    user_input = input("[Delete]>: ").strip()
    if user_input != "delete":
        return
    clear_console()
    print("Deleting project now")
    # Open a new connection to main-db
    maindb_conn = socket.create_connection(
        ("localhost", ahgrar_config['AHGraR_Server']['server_app_port']))
    send_data(maindb_conn, "PMDELE_" + proj_id)
    status = receive_data(maindb_conn)
    if status == proj_id:
        print("Deleted project ID "+proj_id)
    else:
        print("Deletion of project ID " + proj_id + " failed")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    print("Welcome to AHGraR")
    # Load config file
    ahgrar_config = configparser.ConfigParser()
    ahgrar_config.read('AHGraR_config_new.txt')
    # Print options
    print_options()
    while True:
        # Wait for cmdline input
        user_input = input(">: ").strip()
        # Check if a number between 0-5 was entered
        # If so, perform an action
        # If not, show options again
        if not user_input.isdigit() or int(user_input) not in range(0,6):
            clear_console()
            print_options()
            continue
        # Open up a connection to AHGraR-server running on localhost
        maindb_conn = socket.create_connection(
            ("localhost", ahgrar_config['AHGraR_Server']['server_app_port']))
        # Perform an action
        if user_input == "0":
            exit(0)
        actions = {"1": list_projects,
                   "2": create_project,
                   "3": change_project_files,
                   "4": build_project_db,
                   "5": delete_project}
        clear_console()
        actions[user_input](maindb_conn)





