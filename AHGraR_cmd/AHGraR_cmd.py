#AHGraRcmd
import socket,os
import sqlite3
import configparser
import shlex


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


def send_data(connection, reply):
    # Add length of message to header
    message = str(len(reply)) + "|" + reply
    connection.sendall(message.encode())


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Manage projects, i.e. create, delete or list projects
def project_management(connection, user_input):
    # Check if cmd is two or three words long
    if not 2 <= len(user_input) <= 3: print("Invalid command")
    # project list
    # Print a list of all existing projects
    # No job-id assigned, project list is directly returned from server
    if user_input[1] == "list":
        send_data(connection, "PMINFO")
        list = receive_data(connection)
        print(list)
    # project status project_ID
    if user_input[1] == "status":
        send_data(connection, "PMINFO_"+user_input[2])
        project_status = receive_data(connection)
        print(project_status)
    # Create a new project
    # cmd is PROJECT CREATE "PROJECT_NAME"
    # Query returns a job-id
    # Result of job-id is project id or FAILURE
    if user_input[1] == "create" and len(user_input) == 3:
        send_data(connection, "PMCREA_"+user_input[2])
        job_id = receive_data(connection)
        print("New project id : " + str(job_id))
    elif user_input[1] == "delete" and len(user_input) == 3:
        send_data(connection, "PMDELE_"+user_input[2])
        job_id = receive_data(connection)
        print("Deleted project id : "+str(job_id))
    else:
        return "Unknown command"


def job_management(proj_id, connection, user_input):
    if user_input[1] == "list":
        print_joblist(proj_id, connection)
    if user_input[1] == "result" and len(user_input)==3:
        fetch_result(connection, proj_id, user_input[2])
    if user_input[1] == "status" and len(user_input)==3:
        job_status(proj_id, user_input[2],connection)
    if user_input[1] == "clear" and len(user_input)==3:
        delete_job(proj_id, user_input[2], True, connection)
    else:
        connection.close()




# Add job-ID to internal SQLlite-DB and print ID to cmdline
def add_jobid(job_id, proj_id, job_description):
    print("job ID: " + job_id)
    job_db = sqlite3.connect("jobs.db")
    job_db_cursor = job_db.cursor()
    job_db_cursor.execute('INSERT INTO JOBS VALUES (?,?,?,?)', (int(job_id), int(proj_id), job_description, "started"))
    job_db.commit()
    job_db.close()


def update_jobstatus(proj_id, job_id, new_job_status):
    job_db = sqlite3.connect("jobs.db")
    job_db_cursor = job_db.cursor()
    job_db_cursor.execute('UPDATE JOBS SET STATUS=? WHERE ID=? AND PROID=?', (new_job_status, int(job_id), int(proj_id)))
    job_db.commit()
    job_db.close()

def delete_job(proj_id, job_id, delete_from_server, connection=None):
    # Optionally delete job from AHGraR-server
    # This does not need to be done when results are fetched
    # as this triggers automatic deletion of the task node
    if delete_from_server:
        send_data(connection, "PATASK_DELE_"+str(proj_id)+"_"+str(job_id))
        if not receive_data(connection)=="Deleted":
            connection.close()
            return
        else:
            connection.close()
    job_db = sqlite3.connect("jobs.db")
    job_db_cursor = job_db.cursor()
    job_db_cursor.execute('DELETE FROM JOBS WHERE ID=? AND PROID=?',
                          (int(job_id), int(proj_id)))
    job_db.commit()
    job_db.close()

# Retrieve the status of a single job
def job_status(proj_id, jobid, connection):
    # First, update the job
    send_data(connection, "PATASK_STAT_" + str(proj_id) + "_" + str(jobid))
    updated_job_status = receive_data(connection).split("\t")
    update_jobstatus(proj_id, jobid, updated_job_status[0])
    print(updated_job_status)
    connection.close()


def print_joblist(proj_id, connection):
    # First, before showing the job-list, update each job status
    # For this, we first retrieve a list of all job-IDs
    job_db = sqlite3.connect("jobs.db")
    job_db_cursor = job_db.cursor()
    job_db_cursor.execute('SELECT ID FROM JOBS WHERE PROID=?', (int(proj_id),))
    jobid_list = [str(job_id[0]) for job_id in job_db_cursor.fetchall()]
    send_data(connection, "PATASK_STAT_"+str(proj_id)+"_"+"_".join(jobid_list))
    updated_job_stats = receive_data(connection).split("\t")
    # Update internal database
    id_stat_map = list(zip(jobid_list, updated_job_stats))
    for id_stat in id_stat_map:
        update_jobstatus(proj_id, id_stat[0],id_stat[1])
    job_db_cursor.execute('SELECT * FROM JOBS WHERE PROID=?', (int(proj_id),))
    job_list = job_db_cursor.fetchall()
    job_list = "\n".join(["\t".join([str(item[0]), item[2],item[3]]) for item in job_list])
    print(job_list)
    job_db.close()

# Fetch results from AHGraR-server
# Task is deleted afterwards from AHGraR-server and from the internal DB
def fetch_result(connection, proj_id, job_id):
    send_data(connection, "PATASK_RESU_" + str(proj_id) + "_" + str(job_id))
    task_results = receive_data(connection)
    connection.close()
    delete_job(proj_id, job_id, False)
    print(task_results)


def project_access(connection, user_input):
    # Check user_input: expected format is:
    # access project 123
    if user_input[1] != "project" or len(user_input)!=3 or not user_input[2].isdigit(): return
    else:
        # Remember project nr.
        accessed_project = user_input[2]
        # Open "UI" for project access
        while True:
            user_input = input("["+accessed_project+"]>: ").strip().split(" ")
            if user_input[0] == "exit": break
            if user_input[0] == "job" and len(user_input) > 1:
                job_management(accessed_project, connection, user_input)
            if user_input[0] == "status":
                send_data(connection,"PMINFO_"+accessed_project)
                project_status = receive_data(connection)
                print(project_status)
            if user_input[0] == "file":
                file_management(connection, accessed_project, user_input[1:])
            if user_input[0] == "build":
                build_management(connection, accessed_project, user_input[1:])
            if user_input[0] == "database":
                db_runner(connection, accessed_project, user_input[1:])
            if user_input[0] == "query":
                query_management(connection, accessed_project, user_input[1:])
            connection.close()
            # Connection is closed after evey send/received interval
            # Open a new connection to continue project access
            # If project access is exited in the next cycle, the main loop closes the connection
            connection = socket.create_connection(
                (ahgrar_config['AHGraR_Gateway']['ip'], ahgrar_config['AHGraR_Gateway']['port']))
    return

# Functions involving files
# Add files to project, hide/unhide or remove them
def file_management(connection, accessed_project, user_input):
    if user_input[0] == "sleep":
        send_data(connection, "PAFILE_SLEE_" + accessed_project)
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "File sleep")
    if user_input[0] == "download" and len(user_input) == 5:
        # download species variant filetype url
        # convert any "_" in url to "\t"
        user_input[4] = user_input[4].replace("_", "\t")
        send_data(connection, "PAFILE_DWNF_"+str(accessed_project)+"_" + "_".join(user_input[1:]))
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "File download "+user_input[4].replace("\t","_")[:10])
    if user_input[0] == "list":
        send_data(connection, "PAFILE_LIST_" + str(accessed_project))
        file_list = receive_data(connection)
        print(file_list)
    # Hide a file so that it is not used in building the database
    if user_input[0] == "hide" and len(user_input) == 2:
        # convert any "_" in file_name to "\t"
        user_input[1] = user_input[1].replace("_", "\t")
        send_data(connection, "PAFILE_HIDF_" + str(accessed_project)+"_"+user_input[1])
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Hide file "+user_input[1])
    # Unhide a file so that it is used in building the database
    if user_input[0] == "unhide" and len(user_input) == 2:
        # convert any "_" in file_name to "\t"
        user_input[1] = user_input[1].replace("_", "\t")
        send_data(connection, "PAFILE_UHIF_" + str(accessed_project) + "_" + user_input[1])
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Unhide file " + user_input[1])
        # Unhide a file so that it is used in building the database
    if user_input[0] == "remove" and len(user_input) == 2:
        # convert any "_" in file_name to "\t"
        user_input[1] = user_input[1].replace("_", "\t")
        send_data(connection, "PAFILE_DELF_" + str(accessed_project) + "_" + user_input[1])
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Remove file " + user_input[1])
    # Batch import of files to project
    if user_input[0] == "import" and len(user_input)==2:
        # convert any "_" in file_name to "\t"
        user_input[1] = user_input[1].replace("_", "\t")
        send_data(connection, "PAFILE_IMPO_" + str(accessed_project) + "_" + user_input[1])
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Importing files from " + user_input[1])


def build_management(connection, accessed_project, user_input):
    if user_input[0] == "set" and user_input[1] == "GFF3" and len(user_input) >=4:
        # Convert any "_" in annotation mapping, feature hierarchy or file names to "\t"
        user_input = [command.replace("_","\t") for command in user_input]
        send_data(connection, "PABULD_GFF3_" + str(accessed_project) + "_" + "_".join(user_input[2:]))
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Testing GFF3 parsing")
    if user_input[0] == "db" and len(user_input)==1:
        # Build project-db. No further input parameters are required as
        # files, parser etc. have to be configured before calling "build db"
        # Appropriate error messages will be returned if project was not
        # configured for db-building
        send_data(connection, "PABULD_DB_" + str(accessed_project))
        task_id = receive_data(connection)
        add_jobid(task_id, accessed_project, "Building project DB")


def db_runner(connection, accessed_project, user_input):
    # Check user command for correct syntax
    if len(user_input) == 1:
        if user_input[0] == "start":
            send_data(connection, "PADABA_" + str(accessed_project)+"_START")
        elif user_input[0] == "stop":
            send_data(connection, "PADABA_" + str(accessed_project)+"_STOP")
        elif user_input[0] == "status":
            send_data(connection, "PADABA_" + str(accessed_project)+"_STATUS")
        else:
            return
        print(receive_data(connection))


def query_management(connection, accessed_project, user_input):
    # Check user command for correct syntax
    if 2 <= len(user_input) <=5:
        if user_input[0] == "search" and len(user_input) == 5:
            # Convert user-input into search term:
            # Input: e.g. E.coli, "Plasmid A1", Keyword, Gene/Protein/Both
            # PAQURY_SEAR_123_CMD_E.coli_Plasmid A1_Keyword_Both
            # Search is case-insensitive, last term defines if searching for only gene or protein,
            # if empty: search for both
            # Replace underscores in query terms with "\t"
            user_input = [item.strip().replace("_","\t") for item in user_input[1:]]
            send_data(connection, "_".join(["PAQURY", "SEAR", str(accessed_project), "CMD"]+user_input))
            recv = receive_data(connection)
            print(recv)
        if user_input[0] == "related" and len(user_input) == 4:
            send_data(connection, "PAQURY_RELA_"+ str(accessed_project)+"_CMD_"+"_".join(user_input[1:]))
            recv = receive_data(connection)
            print(recv)
        if user_input[0] == "list" and user_input[1] == "species":
            send_data(connection, "PAQURY_LIST_"+str(accessed_project)+"_SPECIES")
            recv = receive_data(connection)
            print(recv)
        if user_input[0] == "list" and user_input[1] == "chromosomes":
            # If no species name was defined, search for chromosome names in all species:
            if len(user_input)==2:
                send_data(connection, "PAQURY_LIST_"+str(accessed_project)+"_CHROMOSOME")
                recv = receive_data(connection)
                print(recv)
            # Else search only for chromosome names belonging to one species
            if len(user_input) == 3:
                send_data(connection, "PAQURY_LIST_" + str(accessed_project) + "_CHROMOSOME"+user_input[2])
                recv = receive_data(connection)
                print(recv)




if __name__ == '__main__':
    print("Welcome to AHGraR")
    # AHGraRcmd keeps track of all active jobs in a sqlite3 database
    # Database assigns task description to an unique id
    # Create database if not yet existing
    if not os.path.isfile("jobs.db"):
        conn = sqlite3.connect('jobs.db')
        conn.execute('''CREATE TABLE JOBS
                   (ID INT PRIMARY KEY NOT NULL,
                   PROID INT NOT NULL,
                   NAME           TEXT    NOT NULL,
                   STATUS TEXT NOT NULL);''')
        conn.close()
    # Open config file
    ahgrar_config = configparser.ConfigParser()
    try:
        ahgrar_config.read('AHGraR_config.txt')
    except OSError:
        print("Config file not found. Exiting.")
        exit(3)
    while True:
        user_input = input(">: ").strip()
        if user_input == "exit": break
        connection = socket.create_connection(
            (ahgrar_config['AHGraR_Gateway']['ip'], ahgrar_config['AHGraR_Gateway']['port']))
        user_input = shlex.split(user_input)
        if user_input[0] == "project": project_management(connection, user_input)
        elif user_input[0] == "access": project_access(connection, user_input)
        connection.close()
