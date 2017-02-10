# This class provides functionality to start, stop, status a project-specific neo4j graph database instance
import os
import subprocess


class DBRunner:

    def __init__(self, main_db_connection, send_data):
        self.main_db_conn = main_db_connection
        self.send_data = send_data

    # Reply to request send from a user app
    # User_request is a list produced by the "_" split command
    # e.g. [ProjectID, START]
    def evaluate_user_request(self, user_request):
        # Check for correct syntax: Proj_ID + command
        if len(user_request) != 2 or not user_request[0].isdigit():
            self.send_data("-5")
        proj_id = user_request[0]
        # Define path to neo4j binary
        neo4j_binary = os.path.join("Projects", str(user_request[0]), "proj_graph_db", "bin", "neo4j")
        # Start db?
        if user_request[1] == "START":
            self.start(neo4j_binary, proj_id)
        elif user_request[1] == "STOP":
            self.stop(neo4j_binary, proj_id)
        elif user_request[1] == "STATUS":
            self.get_status(neo4j_binary)
        else:
            self.send_data("-5")

    def get_status(self,neo4j_binary):
        # Retrieve status (running/not running) from neo4j instance
        # returncode 0: DB is running
        # returncode 3: DB not running
        try:
            status = subprocess.run([neo4j_binary, "status"], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            self.send_data("Unknown")
            return
        if status.returncode == 0:
            self.send_data("Running")
        elif status.returncode == 3:
            self.send_data("Not running")
        else:
            self.send_data("Unknown")

    def start(self,neo4j_binary, proj_id):
        # Start up the project neo4j database
        self.send_data("Starting Project DB")
        try:
            stdout = subprocess.run([neo4j_binary, "start"], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return
        # Only change project status if previous subprocess was successfull
        if stdout.returncode == 0:
            self.set_project_status(proj_id, "DB_RUNNING")


    def stop(self,neo4j_binary, proj_id):
        # Start up the project neo4j database
        self.send_data("Stopping Project DB")
        try:
            stdout = subprocess.run([neo4j_binary, "stop"])
        except subprocess.CalledProcessError:
            return
        # Only change project status if previous subprocess was successfull
        if stdout.returncode == 0:
            self.set_project_status(proj_id, "DB_STOPPED")


    # Change project status
    def set_project_status(self, proj_id, new_status):
        self.main_db_conn.run(
            "MATCH (proj:Project) WHERE ID(proj) = {proj_id} SET proj.status = {new_status}"
            , {"proj_id": int(proj_id), "new_status": str(new_status)})